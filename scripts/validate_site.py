from __future__ import annotations

import argparse
import json
import shutil
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


SITE_ROOT = Path(__file__).resolve().parents[1]
SITE_BASE = "https://nikatsam.github.io/WINAPP_CraftFairProfit_WEBSITE/"
STATIC_FILES = (
    "index.html",
    "privacy.html",
    "404.html",
    "styles.css",
    "script.js",
    "favicon.svg",
    "robots.txt",
    "sitemap.xml",
    "guides/index.html",
    "guides/craft-fair-profit.html",
    "guides/craft-fair-inventory-checklist.html",
    "guides/craft-fair-costs.html",
    "guides/is-a-craft-fair-worth-it.html",
    "guides/craft-fair-pricing.html",
    "assets/fairprofit-overview.png",
    "assets/01-overview.png",
    "assets/02-products.png",
    "assets/03-events.png",
    "assets/04-event-comparison.png",
)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang = ""
        self.title = ""
        self.in_title = False
        self.h1_count = 0
        self.ids: set[str] = set()
        self.meta: dict[tuple[str, str], str] = {}
        self.canonical: list[str] = []
        self.links: list[str] = []
        self.resources: list[str] = []
        self.jsonld: list[str] = []
        self.script_buffer: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "html":
            self.lang = values.get("lang", "")
        if "id" in values:
            self.ids.add(values["id"])
        if tag == "h1":
            self.h1_count += 1
        if tag == "title":
            self.in_title = True
        if tag == "meta":
            key = values.get("name") or values.get("property")
            if key:
                self.meta[("meta", key.lower())] = values.get("content", "")
        if tag == "link":
            if values.get("rel", "").lower() == "canonical":
                self.canonical.append(values.get("href", ""))
            elif values.get("href"):
                self.resources.append(values["href"])
        elif tag == "a" and values.get("href"):
            self.links.append(values["href"])
        elif tag in {"img", "script"}:
            source = values.get("src")
            if source:
                self.resources.append(source)
        if tag == "script" and values.get("type") == "application/ld+json":
            self.script_buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        if tag == "script" and self.script_buffer is not None:
            self.jsonld.append("".join(self.script_buffer))
            self.script_buffer = None

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data
        if self.script_buffer is not None:
            self.script_buffer.append(data)


def page_url(path: Path) -> str:
    relative = path.relative_to(SITE_ROOT).as_posix()
    if relative == "index.html":
        return SITE_BASE
    if relative == "guides/index.html":
        return f"{SITE_BASE}guides/"
    return f"{SITE_BASE}{relative}"


def local_target(source: Path, target: str) -> Path | None:
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or target.startswith("mailto:") or target.startswith("tel:"):
        return None
    path_text = parsed.path
    if not path_text:
        return source
    if path_text.startswith("/"):
        return SITE_ROOT / path_text.lstrip("/")
    path = source.parent / path_text
    if path_text.endswith("/"):
        return path / "index.html"
    return path


def validate_site() -> list[str]:
    failures: list[str] = []
    html_files = sorted(path for path in SITE_ROOT.rglob("*.html") if "_site" not in path.parts)
    canonical_urls: set[str] = set()
    titles: set[str] = set()
    published_html = [path for path in html_files if path.name != "404.html"]

    for page in html_files:
        parser = PageParser()
        parser.feed(page.read_text(encoding="utf-8"))
        rel = page.relative_to(SITE_ROOT).as_posix()
        prefix = f"{rel}: "
        description = parser.meta.get(("meta", "description"), "")
        robots = parser.meta.get(("meta", "robots"), "")
        expected_canonical = page_url(page)

        if not parser.lang:
            failures.append(prefix + "missing html lang")
        if not parser.title.strip():
            failures.append(prefix + "missing title")
        elif page.name != "404.html" and parser.title in titles:
            failures.append(prefix + "duplicate title")
        titles.add(parser.title)
        if not (70 <= len(description) <= 190):
            failures.append(prefix + f"meta description length {len(description)} is outside 70-190")
        if parser.h1_count != 1:
            failures.append(prefix + f"expected exactly one H1, found {parser.h1_count}")
        if page.name != "404.html" and parser.canonical != [expected_canonical]:
            failures.append(prefix + f"expected one canonical URL: {expected_canonical}")
        if page.name != "404.html" and "noindex" in robots.lower():
            failures.append(prefix + "published page is marked noindex")
        if page.name != "404.html":
            if expected_canonical in canonical_urls:
                failures.append(prefix + "duplicate canonical URL")
            canonical_urls.add(expected_canonical)

        for source in parser.resources + parser.links:
            target = local_target(page, source)
            if target is None:
                continue
            if not target.exists():
                failures.append(prefix + f"broken local link/resource: {source}")
            elif urlsplit(source).fragment and target.suffix == ".html":
                destination = PageParser()
                destination.feed(target.read_text(encoding="utf-8"))
                if urlsplit(source).fragment not in destination.ids:
                    failures.append(prefix + f"missing target anchor: {source}")

        for block in parser.jsonld:
            try:
                json.loads(block)
            except json.JSONDecodeError as error:
                failures.append(prefix + f"invalid JSON-LD: {error}")

        image = parser.meta.get(("meta", "og:image"))
        if image:
            parsed_image = urlsplit(image)
            image_path = parsed_image.path.removeprefix(urlsplit(SITE_BASE).path).lstrip("/")
            target = SITE_ROOT / image_path if parsed_image.netloc == urlsplit(SITE_BASE).netloc else None
            if target is None or not target.is_file():
                failures.append(prefix + "Open Graph image must resolve to a local image")

    sitemap = SITE_ROOT / "sitemap.xml"
    try:
        sitemap_root = ET.parse(sitemap).getroot()
        sitemap_urls = {
            element.text.strip()
            for element in sitemap_root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
            if element.text
        }
        expected_urls = {page_url(page) for page in published_html}
        if sitemap_urls != expected_urls:
            failures.append("sitemap URLs do not exactly match published HTML pages")
    except (OSError, ET.ParseError) as error:
        failures.append(f"sitemap.xml is invalid: {error}")

    robots_file = SITE_ROOT / "robots.txt"
    if not robots_file.exists() or f"Sitemap: {SITE_BASE}sitemap.xml" not in robots_file.read_text(encoding="utf-8"):
        failures.append("robots.txt must reference the canonical sitemap URL")

    faq_page = SITE_ROOT / "index.html"
    if faq_page.exists():
        text = faq_page.read_text(encoding="utf-8")
        if "FAQPage" not in text or "<details>" not in text:
            failures.append("home page FAQ content/schema is missing")

    if "index.html" not in {path.relative_to(SITE_ROOT).as_posix() for path in html_files}:
        failures.append("root index.html is missing")

    return failures


def build_output(output: Path) -> None:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for relative in STATIC_FILES:
        source = SITE_ROOT / relative
        if not source.is_file():
            raise FileNotFoundError(f"Required website file is missing: {relative}")
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    nojekyll = SITE_ROOT / ".nojekyll"
    if nojekyll.exists():
        shutil.copy2(nojekyll, output / ".nojekyll")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check website SEO, links, structured data and deployment files.")
    parser.add_argument("--output", type=Path, help="Copy the validated static site to this deployment folder.")
    args = parser.parse_args()

    failures = validate_site()
    if failures:
        print("SITE VALIDATION FAILED:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    if args.output:
        output = args.output.resolve()
        if output != (SITE_ROOT / "_site").resolve():
            print("Deployment output must be the generated _site directory.", file=sys.stderr)
            return 2
        build_output(output)

    page_count = sum(1 for path in SITE_ROOT.rglob("*.html") if "_site" not in path.parts)
    print(f"SITE VALIDATED: {page_count} source HTML pages, local links/resources, canonicals, sitemap, robots and JSON-LD valid.")
    if args.output:
        print(f"DEPLOYMENT FILES WRITTEN: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
