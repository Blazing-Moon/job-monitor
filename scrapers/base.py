from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import requests

log = logging.getLogger(__name__)

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


@dataclass
class Listing:
    """A single job listing, normalized across sources."""

    source: str
    source_id: str
    title: str
    url: str
    department: str = ""
    location: str = ""

    @property
    def id(self) -> str:
        return f"{self.source}:{self.source_id}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "source_id": self.source_id,
            "title": self.title,
            "url": self.url,
            "department": self.department,
            "location": self.location,
        }


@dataclass
class ScrapeResult:
    listings: list[Listing] = field(default_factory=list)
    raw_html: str = ""
    error: str = ""

    @property
    def ok(self) -> bool:
        return not self.error


class Scraper:
    """Base class. Subclasses set name/label/url and implement parse()."""

    name: str = ""
    label: str = ""
    url: str = ""

    def fetch(self) -> str:
        headers = {
            "User-Agent": BROWSER_UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        resp = requests.get(self.url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.text

    def parse(self, html: str) -> Iterable[Listing]:
        raise NotImplementedError

    def run(self, debug_dir: Path | None = None) -> ScrapeResult:
        result = ScrapeResult()
        try:
            html = self.fetch()
            result.raw_html = html
            result.listings = list(self.parse(html))
            log.info("%s: %d listings", self.name, len(result.listings))
        except Exception as e:
            result.error = f"{type(e).__name__}: {e}"
            log.exception("%s: scrape failed", self.name)
        if debug_dir is not None:
            debug_dir.mkdir(parents=True, exist_ok=True)
            (debug_dir / f"{self.name}.html").write_text(
                result.raw_html or result.error, encoding="utf-8"
            )
        return result
