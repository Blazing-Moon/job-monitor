"""Main entry: run all scrapers, merge into state, render the page."""
from __future__ import annotations

import logging
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from render import write_page
from scrapers import ALL_SCRAPERS
from state import load_state, merge, save_state, utcnow

DEBUG_DIR = Path("debug/snapshots")

# If every source already has data more recent than this window in state,
# don't scrape again — the primary run today already succeeded and the
# safety-net run has nothing to do. Sized to cover the ~4-hour primary→
# safety-net gap plus GitHub cron slip (up to ~60 min).
FRESHNESS_HOURS = 6


def _latest_last_seen(state: dict, source: str) -> datetime | None:
    """Most recent last_seen across state's listings for `source`, or None."""
    return max(
        (datetime.fromisoformat(L["last_seen"])
         for L in state.get("listings", [])
         if L["source"] == source),
        default=None,
    )


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    now = utcnow()
    state = load_state()

    # If every source has recent-enough data, exit without touching
    # anything. No scrape, no state churn, no commit, no email.
    freshness_cutoff = now - timedelta(hours=FRESHNESS_HOURS)
    all_fresh = all(
        (last := _latest_last_seen(state, s.name)) is not None
        and last >= freshness_cutoff
        for s in ALL_SCRAPERS
    )
    if all_fresh:
        print(
            f"All {len(ALL_SCRAPERS)} sources have data < {FRESHNESS_HOURS}h old; "
            f"exiting without scraping."
        )
        return 0

    # Pre-scrape counts so we can detect a source that silently went to 0.
    prior_counts: Counter[str] = Counter()
    for L in state.get("listings", []):
        prior_counts[L["source"]] += 1

    all_listings = []
    scrape_errors: dict[str, str] = {}
    sources_ok: set[str] = set()
    per_source_count: Counter[str] = Counter()

    for scraper in ALL_SCRAPERS:
        result = scraper.run(debug_dir=DEBUG_DIR)
        if result.ok:
            all_listings.extend(result.listings)
            sources_ok.add(scraper.name)
            per_source_count[scraper.name] = len(result.listings)
        else:
            scrape_errors[scraper.name] = result.error

    # A successful scrape that returns 0 from a source that previously
    # had listings is more likely a parser regression than the source
    # genuinely emptying overnight. Flag it as a failure.
    for src in list(sources_ok):
        if per_source_count[src] == 0 and prior_counts.get(src, 0) > 0:
            scrape_errors[src] = (
                f"scrape returned 0 listings but state previously held "
                f"{prior_counts[src]} from this source; likely parser broke"
            )

    new_state = merge(state, all_listings, sources_ok, now)
    save_state(new_state)
    write_page(new_state, scrape_errors)

    print(
        f"Scraped {len(all_listings)} listings from "
        f"{len(sources_ok)}/{len(ALL_SCRAPERS)} sources. "
        f"State has {len(new_state['listings'])} listings."
    )
    for src, n in per_source_count.items():
        print(f"  {src}: {n}")
    if scrape_errors:
        print("Errors:")
        for src, err in scrape_errors.items():
            print(f"  {src}: {err}")
        # Surface scrape failures as a workflow failure so GitHub emails the owner.
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
