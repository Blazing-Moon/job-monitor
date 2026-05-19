from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import Listing, Scraper


class WiscStateScraper(Scraper):
    name = "wisc_state"
    label = "Wisconsin State Jobs (25 mi of 53703)"
    url = "https://wisc.jobs/Pages/SearchResults.aspx?keywords=&city=&zip=53703&distance=25"

    def parse(self, html: str) -> Iterable[Listing]:
        soup = BeautifulSoup(html, "lxml")
        seen: set[str] = set()

        # State system listings typically link to a job detail page.
        # Try a few link patterns observed across NEOGOV / state systems.
        link_patterns = [
            re.compile(r"JobDetails?\.aspx\?.*(jobid|id|recruitmentid)=", re.I),
            re.compile(r"/jobs?/\d+", re.I),
            re.compile(r"/job/(view|detail)/\d+", re.I),
        ]

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not any(p.search(href) for p in link_patterns):
                continue

            source_id = _extract_id(href)
            if not source_id or source_id in seen:
                continue
            seen.add(source_id)

            title = a.get_text(" ", strip=True)
            if not title or len(title) < 3:
                continue

            container = a.find_parent(["tr", "li", "article", "div"])
            department, location = "", ""
            if container is not None:
                department = _extract_field(container, ["agency", "department", "employer"])
                location = _extract_field(container, ["location", "city", "county"])

            yield Listing(
                source=self.name,
                source_id=source_id,
                title=title,
                url=urljoin(self.url, href),
                department=department,
                location=location,
            )


def _extract_id(href: str) -> str:
    m = re.search(r"[?&](?:jobid|id|recruitmentid)=([^&#]+)", href, re.I)
    if m:
        return m.group(1)
    m = re.search(r"/(\d+)(?:/|$|\?)", href)
    if m:
        return m.group(1)
    return ""


def _extract_field(container, keywords: list[str]) -> str:
    for kw in keywords:
        el = container.find(class_=re.compile(kw, re.I))
        if el:
            text = el.get_text(" ", strip=True)
            if text:
                return text
    return ""
