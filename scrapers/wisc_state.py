"""Wisconsin state jobs (wisc.jobs).

The search results page renders job rows into a Kendo grid; the source
data is embedded as a JSON array inside an inline <script> that calls
$('#grid').kendoGrid({ dataSource: { data: [ ... ] } }). The static HTML
has no per-listing anchors, so we extract the array from the script.
"""
from __future__ import annotations

import json
import re
from typing import Iterable

from .base import Listing, Scraper

# The grid's column template builds detail URLs as:
#   https://wj.wi.gov/psc/wisjobs/CAREERS/HRMS/c/HRS_HRAM_FL.HRS_CG_SEARCH_FL.GBL
#     ?Page=HRS_APP_JBPST_FL&Action=U&FOCUS=Applicant
#     &SiteId=1&PostingSeq=1&JobOpeningId=<JobId>
DETAIL_URL_TEMPLATE = (
    "https://wj.wi.gov/psc/wisjobs/CAREERS/HRMS/c/"
    "HRS_HRAM_FL.HRS_CG_SEARCH_FL.GBL"
    "?Page=HRS_APP_JBPST_FL&Action=U&FOCUS=Applicant"
    "&SiteId=1&PostingSeq=1&JobOpeningId={job_id}"
)

# Matches the `data: [ ... ]` array passed to the Kendo grid's dataSource.
_DATA_ARRAY_RE = re.compile(
    r"dataSource\s*:\s*\{\s*data\s*:\s*(\[.*?\])\s*,",
    re.DOTALL,
)


class WiscStateScraper(Scraper):
    name = "wisc_state"
    label = "Wisconsin State Jobs (25 mi of 53703)"
    url = "https://wisc.jobs/Pages/SearchResults.aspx?keywords=&city=&zip=53703&distance=25"

    def parse(self, html: str) -> Iterable[Listing]:
        m = _DATA_ARRAY_RE.search(html)
        if not m:
            return
        try:
            rows = json.loads(m.group(1))
        except json.JSONDecodeError:
            return

        seen: set[str] = set()
        for row in rows:
            job_id = str(row.get("JobId") or "").strip()
            if not job_id or job_id in seen:
                continue
            seen.add(job_id)

            title = (row.get("PostingTitle") or "").strip()
            if not title:
                continue

            # The page's "zip=53703 distance=25" filter is applied
            # client-side; the JSON we extract contains every active
            # posting statewide. Keep only Madison-area postings (plus
            # statewide ones, which would apply here too).
            location = (row.get("Location") or "").strip()
            loc_lower = location.lower()
            if "madison" not in loc_lower and "statewide" not in loc_lower:
                continue

            yield Listing(
                source=self.name,
                source_id=job_id,
                title=title,
                url=DETAIL_URL_TEMPLATE.format(job_id=job_id),
                department=(row.get("AgencyName") or "").strip(),
                location=location,
            )
