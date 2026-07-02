"""City of Madison (NEOGOV / governmentjobs.com).

The public agency page renders its listings client-side via Knockout, so
the visible HTML at /careers/MadisonWi contains the template shell but no
job rows. The listings are pulled from a separate XHR endpoint that
returns a ready-to-insert HTML fragment.
"""
from __future__ import annotations

from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import BROWSER_UA, Listing, Scraper

LISTINGS_URL = (
    "https://www.governmentjobs.com/careers/home/index"
    "?agency=madisonwi&sort=PositionTitle&isDescendingSort=false"
)
PUBLIC_URL = "https://www.governmentjobs.com/careers/MadisonWi"
BASE = "https://www.governmentjobs.com"


class MadisonCityScraper(Scraper):
    name = "madison_city"
    label = "City of Madison Careers"
    url = PUBLIC_URL

    def fetch(self) -> str:
        # The endpoint requires the XHR header; without it the server
        # responds with the SPA shell instead of the listings fragment.
        headers = {
            "User-Agent": BROWSER_UA,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": PUBLIC_URL,
        }
        return self._get(LISTINGS_URL, headers=headers).text

    def parse(self, html: str) -> Iterable[Listing]:
        soup = BeautifulSoup(html, "lxml")

        for li in soup.select("li.list-item[data-job-id]"):
            source_id = (li.get("data-job-id") or "").strip()
            if not source_id:
                continue

            a = (li.select_one("h3.job-item-link-container a.item-details-link")
                 or li.select_one("a.item-details-link"))
            if a is None:
                continue

            title = a.get_text(" ", strip=True)
            if not title:
                continue

            href = a.get("href", "")
            url = urljoin(BASE, href) if href else PUBLIC_URL

            department = (a.get("data-department-name") or "").strip()

            location = ""
            meta_li = li.select_one("ul.list-meta li")
            if meta_li is not None:
                location = meta_li.get_text(" ", strip=True)

            yield Listing(
                source=self.name,
                source_id=source_id,
                title=title,
                url=url,
                department=department,
                location=location,
            )
