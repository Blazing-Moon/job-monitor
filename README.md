# job-monitor

Scrapes three Madison-area job sources daily and publishes a weekly digest
page via GitHub Pages.

## Sources

- **UW–Madison Jobs** — Administration, Arts, Comms/Marketing, IT, Other,
  Public Broadcasting, Teaching & Learning, restricted to Madison.
- **Wisconsin State Jobs** — within 25 mi of 53703.
- **City of Madison Careers** (governmentjobs.com).

## How it works

1. `.github/workflows/scrape.yml` runs at 06:00 UTC daily (00:00 US Central /
   01:00 CDT) and on manual dispatch.
2. `update.py` fetches each source, parses listings, and merges them into
   `data/listings.json`. Each listing has a `first_seen` and `last_seen`
   timestamp.
3. `render.py` generates `docs/index.html` with three sections:
   - **New this week** — listings whose `first_seen` is on or after the
     most recent Monday 00:00 US Central.
   - **Still open from prior weeks**.
   - **Recently removed** — listings missing from the latest successful
     scrape, kept on the page for 14 days.
4. The workflow commits any changes back to the repo. GitHub Pages serves
   `/docs/` as the published site.

## Layout

```
.github/workflows/scrape.yml  Scheduled scrape + commit
scrapers/                     One module per source
update.py                     Main entry: scrape → merge → render
state.py                      listings.json read/write/merge
render.py                     HTML page generator
data/listings.json            Persistent state (committed)
docs/                         Published site (GitHub Pages root)
debug/snapshots/              Raw HTML from each scrape, for debugging
```

## Local run

```
pip install -r requirements.txt
python update.py
```

This writes `data/listings.json`, `docs/index.html`, and per-source raw HTML
to `debug/snapshots/`.

## Failures

If a scraper raises or returns nothing, the workflow exits non-zero so
GitHub emails the repo owner about the failed scheduled run. The page
still renders, showing an "errors this run" banner.
