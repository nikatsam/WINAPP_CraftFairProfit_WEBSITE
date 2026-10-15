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

- The public publisher name is Nikatsam. `privacy.html` remains a draft until the publisher verifies its Partner Center identity, supplies a private privacy/data-rights contact and reviews the policy against the release build.
- The app has not been published or certified. The Microsoft Store link is a FairProfit search, not a live listing.
- Public GitHub Issues are available for technical product support only; users should not post personal or sensitive information there.
- `SERP_RESEARCH.md` records qualitative query intent and search-access limitations. It contains no fabricated search volume, ranking or traffic claims.
- Add the verified site to Google Search Console, Bing Webmaster Tools and Yandex Webmaster and submit `sitemap.xml` after Pages is live. Search engine indexing and rankings cannot be guaranteed.
