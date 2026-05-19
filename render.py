"""Render the listings page (docs/index.html) from state."""
from __future__ import annotations

import html
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from scrapers import ALL_SCRAPERS

OUTPUT = Path("docs/index.html")
CENTRAL = ZoneInfo("America/Chicago")

SOURCE_LABELS = {s.name: s.label for s in ALL_SCRAPERS}
SOURCE_URLS = {s.name: s.url for s in ALL_SCRAPERS}
SOURCE_ORDER = [s.name for s in ALL_SCRAPERS]


def last_monday_central(now_utc: datetime) -> datetime:
    """Most recent Monday 00:00 in America/Chicago, returned as UTC."""
    now_central = now_utc.astimezone(CENTRAL)
    monday_central = now_central - timedelta(days=now_central.weekday())
    monday_central = monday_central.replace(hour=0, minute=0, second=0, microsecond=0)
    return monday_central.astimezone(timezone.utc)


def render(state: dict, scrape_errors: dict[str, str]) -> str:
    now_utc = datetime.now(timezone.utc)
    last_updated_iso = state.get("last_updated")
    if last_updated_iso:
        last_updated_utc = datetime.fromisoformat(last_updated_iso)
    else:
        last_updated_utc = now_utc

    week_start_utc = last_monday_central(last_updated_utc)
    week_start_central = week_start_utc.astimezone(CENTRAL)

    # Bucket listings.
    new_this_week: dict[str, list[dict]] = {n: [] for n in SOURCE_ORDER}
    still_open: dict[str, list[dict]] = {n: [] for n in SOURCE_ORDER}
    recently_removed: dict[str, list[dict]] = {n: [] for n in SOURCE_ORDER}

    for L in state.get("listings", []):
        src = L["source"]
        if src not in new_this_week:
            continue
        first_seen = datetime.fromisoformat(L["first_seen"])
        last_seen = datetime.fromisoformat(L["last_seen"])
        present_in_last_scrape = (
            last_updated_iso is not None and L["last_seen"] == last_updated_iso
        )
        if not present_in_last_scrape and src not in scrape_errors:
            recently_removed[src].append(L)
        elif first_seen >= week_start_utc:
            new_this_week[src].append(L)
        else:
            still_open[src].append(L)

    total_new = sum(len(v) for v in new_this_week.values())
    total_open = sum(len(v) for v in still_open.values())
    total_removed = sum(len(v) for v in recently_removed.values())

    last_updated_central = last_updated_utc.astimezone(CENTRAL)
    parts: list[str] = []
    parts.append(_HEAD)
    parts.append("<body>")
    parts.append('<main class="container">')
    parts.append(f"<h1>Madison-area Job Monitor</h1>")
    parts.append(
        f'<p class="meta">Last updated '
        f'<time datetime="{html.escape(last_updated_utc.isoformat())}">'
        f"{last_updated_central:%A, %b %-d, %Y at %-I:%M %p %Z}</time>. "
        f'Week begins <time datetime="{html.escape(week_start_utc.isoformat())}">'
        f"{week_start_central:%a, %b %-d}</time>.</p>"
    )

    if scrape_errors:
        parts.append('<div class="errors"><strong>Scrape errors this run:</strong><ul>')
        for src, err in scrape_errors.items():
            label = SOURCE_LABELS.get(src, src)
            parts.append(f"<li>{html.escape(label)}: {html.escape(err)}</li>")
        parts.append("</ul></div>")

    parts.append(_section("New this week", new_this_week, total_new, empty="No new listings yet this week."))
    parts.append(_section("Still open from prior weeks", still_open, total_open, empty="Nothing currently open from earlier weeks."))
    parts.append(_section("Recently removed", recently_removed, total_removed, empty="No listings have disappeared recently.", show_dates="removed"))

    parts.append("<footer><p>Data scraped daily at 00:00 US Central. ")
    parts.append('Source: <a href="https://github.com/blazing-moon/job-monitor">github.com/blazing-moon/job-monitor</a>.</p></footer>')
    parts.append("</main></body></html>")
    return "\n".join(parts)


def _section(title: str, buckets: dict[str, list[dict]], total: int, empty: str, show_dates: str = "first_seen") -> str:
    out = [f'<section><h2>{html.escape(title)} <span class="count">({total})</span></h2>']
    if total == 0:
        out.append(f'<p class="empty">{html.escape(empty)}</p>')
        out.append("</section>")
        return "\n".join(out)

    for src in SOURCE_ORDER:
        rows = buckets.get(src, [])
        if not rows:
            continue
        rows.sort(key=lambda L: L.get("first_seen", ""), reverse=True)
        label = SOURCE_LABELS[src]
        src_url = SOURCE_URLS[src]
        out.append(
            f'<h3><a class="srclink" href="{html.escape(src_url)}">{html.escape(label)}</a>'
            f' <span class="count">({len(rows)})</span></h3>'
        )
        out.append('<table class="listings"><tbody>')
        for L in rows:
            title_link = (
                f'<a href="{html.escape(L["url"])}">{html.escape(L["title"])}</a>'
            )
            meta_bits = []
            if L.get("department"):
                meta_bits.append(html.escape(L["department"]))
            if L.get("location"):
                meta_bits.append(html.escape(L["location"]))
            meta = " &middot; ".join(meta_bits)

            if show_dates == "removed":
                last_seen = datetime.fromisoformat(L["last_seen"]).astimezone(CENTRAL)
                date_str = f"last seen {last_seen:%b %-d}"
            else:
                first_seen = datetime.fromisoformat(L["first_seen"]).astimezone(CENTRAL)
                date_str = f"first seen {first_seen:%b %-d}"

            out.append("<tr>")
            out.append(f'<td class="title">{title_link}'
                       + (f'<div class="sub">{meta}</div>' if meta else "")
                       + "</td>")
            out.append(f'<td class="date">{html.escape(date_str)}</td>')
            out.append("</tr>")
        out.append("</tbody></table>")
    out.append("</section>")
    return "\n".join(out)


_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>Madison-area Job Monitor</title>
<link rel="stylesheet" href="style.css">
</head>"""


def write_page(state: dict, scrape_errors: dict[str, str], path: Path = OUTPUT) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(state, scrape_errors), encoding="utf-8")
