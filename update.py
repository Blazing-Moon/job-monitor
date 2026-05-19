"""Main entry: run all scrapers, merge into state, render the page."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from render import write_page
from scrapers import ALL_SCRAPERS
from state import load_state, merge, save_state, utcnow

DEBUG_DIR = Path("debug/snapshots")


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    now = utcnow()
    state = load_state()

    all_listings = []
    scrape_errors: dict[str, str] = {}
    sources_ok: set[str] = set()

    for scraper in ALL_SCRAPERS:
        result = scraper.run(debug_dir=DEBUG_DIR)
        if result.ok:
            all_listings.extend(result.listings)
            sources_ok.add(scraper.name)
        else:
            scrape_errors[scraper.name] = result.error

    new_state = merge(state, all_listings, sources_ok, now)
    save_state(new_state)
    write_page(new_state, scrape_errors)

    print(
        f"Scraped {len(all_listings)} listings from "
        f"{len(sources_ok)}/{len(ALL_SCRAPERS)} sources. "
        f"State has {len(new_state['listings'])} listings."
    )
    if scrape_errors:
        print("Errors:")
        for src, err in scrape_errors.items():
            print(f"  {src}: {err}")
        # Surface scrape failures as a workflow failure so GitHub emails the owner.
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
