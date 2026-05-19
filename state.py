"""State management for listings.json.

The state file holds one entry per listing we've ever seen, with:
  - first_seen: ISO timestamp (UTC) of the first scrape that saw it
  - last_seen:  ISO timestamp (UTC) of the most recent scrape that saw it

Listings whose last_seen is older than RETENTION_DAYS are dropped.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scrapers.base import Listing

RETENTION_DAYS = 14
STATE_PATH = Path("data/listings.json")


@dataclass
class StoredListing:
    id: str
    source: str
    source_id: str
    title: str
    url: str
    department: str
    location: str
    first_seen: str  # ISO 8601 UTC
    last_seen: str   # ISO 8601 UTC

    @classmethod
    def from_dict(cls, d: dict) -> "StoredListing":
        return cls(
            id=d["id"],
            source=d["source"],
            source_id=d["source_id"],
            title=d["title"],
            url=d["url"],
            department=d.get("department", ""),
            location=d.get("location", ""),
            first_seen=d["first_seen"],
            last_seen=d["last_seen"],
        )

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def load_state(path: Path = STATE_PATH) -> dict:
    if not path.exists():
        return {
            "schema_version": 1,
            "last_updated": None,
            "first_run_completed": False,
            "listings": [],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(state: dict, path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def merge(
    state: dict,
    scraped: list[Listing],
    sources_scraped_ok: set[str],
    now: datetime,
) -> dict:
    """Merge a fresh scrape into state.

    `sources_scraped_ok` is the set of source names whose scrape succeeded;
    listings from a failed source are not aged out (we don't know if they
    were really removed or if the scraper just broke).
    """
    now_iso = now.isoformat()
    first_run = not state.get("first_run_completed", False)

    # On the first run, seed first_seen to one week ago so the inaugural
    # crop doesn't all show up as "new this week".
    seed_first_seen = (now - timedelta(days=8)).isoformat() if first_run else now_iso

    by_id: dict[str, StoredListing] = {}
    for d in state.get("listings", []):
        sl = StoredListing.from_dict(d)
        by_id[sl.id] = sl

    scraped_ids: set[str] = set()
    for L in scraped:
        scraped_ids.add(L.id)
        if L.id in by_id:
            existing = by_id[L.id]
            existing.last_seen = now_iso
            # Refresh fields that may have been updated upstream
            existing.title = L.title
            existing.url = L.url
            if L.department:
                existing.department = L.department
            if L.location:
                existing.location = L.location
        else:
            by_id[L.id] = StoredListing(
                id=L.id,
                source=L.source,
                source_id=L.source_id,
                title=L.title,
                url=L.url,
                department=L.department,
                location=L.location,
                first_seen=seed_first_seen,
                last_seen=now_iso,
            )

    # Retention: drop anything from a successfully-scraped source whose
    # last_seen is older than RETENTION_DAYS.
    cutoff = now - timedelta(days=RETENTION_DAYS)
    kept: list[StoredListing] = []
    for sl in by_id.values():
        if sl.source not in sources_scraped_ok:
            kept.append(sl)
            continue
        last_seen_dt = datetime.fromisoformat(sl.last_seen)
        if last_seen_dt >= cutoff:
            kept.append(sl)
        # else: drop

    kept.sort(key=lambda s: (s.source, s.title.lower()))

    return {
        "schema_version": 1,
        "last_updated": now_iso,
        "first_run_completed": True,
        "listings": [sl.to_dict() for sl in kept],
    }


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
