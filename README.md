# job-monitor

A weekly rundown of new Madison-area job listings from three sources,
published as a small static site:
**<https://blazing-moon.github.io/job-monitor/>**

## What the site shows

The page has three sections:

- **New this week** — listings that first showed up on the source site
  on or after the most recent Monday (US Central time).
- **Still open from prior weeks** — listings that are still posted but
  were first seen before this Monday.
- **Recently removed** — listings that were here last time but have
  since disappeared from the source. Kept around for 14 days so you
  can tell what just came down.

Each Monday at 00:00 US Central the "new this week" bucket resets:
everything that was in it rolls into "still open from prior weeks."

## How fresh is it

The scraper runs once a day, around 00:00 US Central (give or take an
hour — GitHub's scheduled runs aren't precise). The "Last updated"
timestamp at the top of the page tells you exactly when the most recent
scrape finished.

## Sources

- **UW–Madison Jobs** — filtered to Madison, in the categories
  Administration, Arts, Comms/Marketing, IT, Other, Public Broadcasting,
  and Teaching & Learning.
- **Wisconsin State Jobs** — within 25 mi of zip 53703 (Madison +
  statewide postings).
- **City of Madison Careers** (governmentjobs.com).

---

## For developers

### How it works

1. `.github/workflows/scrape.yml` runs at 06:00 UTC daily (00:00 CST /
   01:00 CDT) and on manual dispatch.
2. `update.py` fetches each source, parses listings, and merges them
   into `data/listings.json`. Each listing has `first_seen` and
   `last_seen` UTC timestamps.
3. `render.py` writes `docs/index.html` from that state.
4. The workflow commits any changes back to the repo. GitHub Pages
   serves `/docs/` as the published site.

### Layout

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

### Local run

```
pip install -r requirements.txt
python update.py
```

Writes `data/listings.json`, `docs/index.html`, and per-source raw HTML
to `debug/snapshots/`.

### Failures

If a scraper raises, or returns zero listings from a source that
previously had some, the workflow exits non-zero so GitHub emails the
repo owner about the failed run. The page still renders, with an
"errors this run" banner at the top.
