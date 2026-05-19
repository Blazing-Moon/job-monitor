from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import Listing, Scraper


class MadisonCityScraper(Scraper):
    name = "madison_city"
    label = "City of Madison Careers"
    url = "https://www.governmentjobs.com/careers/MadisonWi"

    def parse(self, html: str) -> Iterable[Listing]:
        soup = BeautifulSoup(html, "lxml")
        seen: set[str] = set()

        # NEOGOV / governmentjobs.com job links look like:
        #   /careers/madisonwi/jobs/4567890/job-title
        link_pattern = re.compile(r"/careers/[^/]+/jobs/(\d+)", re.I)

        for a in soup.find_all("a", href=True):
            href = a["href"]
            m = link_pattern.search(href)
            if not m:
                continue
            source_id = m.group(1)
            if source_id in seen:
                continue
            seen.add(source_id)

            title = a.get_text(" ", strip=True)
            if not title or len(title) < 3:
                continue

            container = a.find_parent(["tr", "li", "article", "div"])
            department, location = "", ""
            if container is not None:
                department = _extract_field(container, ["department", "agency"])
                location = _extract_field(container, ["location", "city"])

            yield Listing(
                source=self.name,
                source_id=source_id,
                title=title,
                url=urljoin(self.url, href),
                department=department,
                location=location,
            )


def _extract_field(container, keywords: list[str]) -> str:
    for kw in keywords:
        el = container.find(class_=re.compile(kw, re.I))
        if el:
            text = el.get_text(" ", strip=True)
            if text:
                return text
    return ""
