# FairProfit Desktop Website

Static product website for the FairProfit Desktop Windows app. The site is designed to deploy from the `website/` folder to the public `nikatsam/WINAPP_CraftFairProfit_WEBSITE` GitHub Pages repository.

## Local preview

From this directory, run:

```powershell
python -m http.server 8000
```

Open `http://localhost:8000/`. The calculator runs locally in the browser; it does not save or transmit entered values.

## Validate and stage Pages output

```powershell
python scripts/validate_site.py --output _site
node --check script.js
node scripts/test_calculator.js
```

The validator checks HTML metadata, unique canonicals/titles, local links/resources, JSON-LD, sitemap and robots. `_site/` contains only public page assets; research notes and workflow files are not deployed.

## Release notes

- The public publisher name is Nikatsam. `privacy.html` describes the published app and points privacy/data-rights inquiries to the public repository Issues page; users are warned not to post sensitive details.
- Craft Fair Profit is published on Microsoft Store at <https://apps.microsoft.com/detail/9PNZ4GH53SWP> (Store ID `9PNZ4GH53SWP`).
- Public GitHub Issues are available for technical support and privacy/data-rights inquiries; users should not post personal or sensitive information there.
- `SERP_RESEARCH.md` records qualitative query intent and search-access limitations. It contains no fabricated search volume, ranking or traffic claims.
- Webmaster verification and sitemap submission remain owner-deferred. Search engine indexing and rankings cannot be guaranteed.
