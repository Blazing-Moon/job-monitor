from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import Listing, Scraper


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

        for a in soup.find_all("a", href=re.compile(r"/jobs/\d+")):
            href = a.get("href", "")
            m = re.search(r"/jobs/(\d+)", href)
            if not m:
                continue
            source_id = m.group(1)
            if source_id in seen:
                continue
            seen.add(source_id)

            title = a.get_text(" ", strip=True)
            if not title or len(title) < 3:
                continue

            container = a.find_parent(["li", "article", "div", "tr"])
            department, location = "", ""
            if container is not None:
                department = _extract_field(container, ["department", "school", "division", "unit"])
                location = _extract_field(container, ["location", "city", "campus"])

            yield Listing(
                source=self.name,
                source_id=source_id,
                title=title,
                url=urljoin(self.url, href),
                department=department,
                location=location,
            )


def _extract_field(container, keywords: list[str]) -> str:
    """Best-effort: find a sibling element whose class or text hints at the field."""
    for kw in keywords:
        el = container.find(class_=re.compile(kw, re.I))
        if el:
            text = el.get_text(" ", strip=True)
            if text:
                return text
    return ""
