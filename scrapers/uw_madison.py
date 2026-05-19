from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .base import Listing, Scraper

# Real listing URLs look like:
#   https://jobs.wisc.edu/jobs/<slug>
#   https://jobs.wisc.edu/jobs/<slug>-<uuid>
# where <slug> is kebab-case (no slashes) and the optional trailing UUID
# is the stable posting id. We must exclude /jobs/search and similar
# navigational links.
_SLUG_RE = re.compile(r"^/jobs/([a-z0-9][a-z0-9-]+)$", re.I)
_UUID_RE = re.compile(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$", re.I)

# Slugs that aren't listings.
_NON_LISTING_SLUGS = {"search", "saved"}


class UWMadisonScraper(Scraper):
    name = "uw_madison"
    label = "UW–Madison Jobs"
    url = (
        "https://jobs.wisc.edu/jobs/search"
        "?page=1"
        "&category_uids%5B%5D=b8deb656947105bcb05785b127aa27ba"
        "&category_uids%5B%5D=3137579afa35719380e85ab6a3b52ce7"
        "&category_uids%5B%5D=6ebbdab01d8053ced2cb2abd3f5052e9"
        "&category_uids%5B%5D=0cab7fcac6928c822828e53a082c754b"
        "&category_uids%5B%5D=76683a6dee6b5d4ae2a01990f31e9a94"
        "&category_uids%5B%5D=645de1d33d345236341e07c144083b25"
        "&cities%5B%5D=Madison"
        "&query=madison"
    )

    def parse(self, html: str) -> Iterable[Listing]:
        soup = BeautifulSoup(html, "lxml")
        seen: set[str] = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            # Normalize: only the path matters for matching.
            path = urlparse(href).path
            m = _SLUG_RE.match(path)
            if not m:
                continue
            slug = m.group(1)
            if slug in _NON_LISTING_SLUGS:
                continue

            uuid_match = _UUID_RE.search(slug)
            source_id = uuid_match.group(1) if uuid_match else slug
            if source_id in seen:
                continue
            seen.add(source_id)

            title = a.get_text(" ", strip=True)
            if not title or len(title) < 3:
                continue

            yield Listing(
                source=self.name,
                source_id=source_id,
                title=title,
                url=urljoin(self.url, href),
            )
