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

The scraper runs on a two-attempt schedule each day, both in US
Central time:

- **Primary run, ~midnight–1 AM** — the daily refresh.
- **Safety-net run, ~2–3 AM** — only actually scrapes if the primary
  run didn't produce fresh data. If the primary already succeeded,
  the safety-net exits immediately and the page is left alone. This
  catches nights where one of the source sites (usually wisc.jobs)
  was unreachable during the primary window.

Both runs may slip by up to an hour — GitHub's scheduled runs
aren't precise. The "Last updated" timestamp at the top of the page
tells you exactly when the most recent successful scrape finished.

On rare days where a source is unreachable during both windows, the
page still shows the previous day's data for that source, plus an
"errors this run" banner naming what failed.

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

1. `.github/workflows/scrape.yml` runs twice daily and on manual
   dispatch:
   - **Primary** at 06:00 UTC (midnight CST / 01:00 CDT).
   - **Safety-net** at 08:00 UTC (02:00 CST / 03:00 CDT), which
     exits immediately if every source in state has a `last_seen`
     within the last 6 hours — i.e., the primary already succeeded.
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
