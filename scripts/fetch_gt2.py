"""scripts/fetch_gt2.py

R3 (docs/REAL_DATA_PLAN.md §1, §5, §8's R3 row) — fetches the WDC-PMKSY 2.0
MIS "GT2 — Work Code Status with Geotagging Details" report's drill-down for
Marigaon district, Assam, and writes the real work-code registry + programme
aggregates the API serves.

Drill-down (REAL_DATA_PLAN.md §1): state -> district -> project -> work-code
detail, via
    https://wdcpmksy.dolr.gov.in/getAllAssetGeoData
    -> getDistWiseAssetGeoData?stcode=<n>&stname=<STATE>
    -> getProjWiseAssetGeoData?dcode=<n>&stname=<STATE>&distname=<DISTRICT>
    -> getProjDtlAssetGeoData?projid=<n>&stname=..&distname=..&projname=..

This script bootstraps a session (one GET to `/`) before the drill-down
calls: these are JSP-backed endpoints that conventionally expect a
JSESSIONID, and a stray unauthenticated path on this host (tried during
reconnaissance, e.g. `/robots.txt`) does return the site's own
error404.jsp page. The report endpoints themselves answered correctly even
without a prior session in ad hoc testing, but bootstrapping first is one
extra harmless GET and matches how a real browser would hit them — kept
for robustness. Handled by `_GovSession` below.

Run ONCE, offline — like scripts/precompute_gee.py. Never imported by the
live API (CLAUDE.md precompute-first non-negotiable: `GET /programme/marigaon`
reads this script's JSON output from disk, it never re-fetches or re-parses
HTML on a request). Fetches politely (rate-limited well under the plan's
"<=1 req/sec" ceiling, identified User-Agent) and caches every raw HTML
response to scripts/cache/gt2/ — re-running this script during development
reads from that cache and makes zero new HTTP requests. Delete
scripts/cache/gt2/ to force a fresh pull (e.g. to re-verify before a demo).

No photo/image data is fetched or requested anywhere in this script — GT2's
work-code table links out to Bhuvan photo pages (`bhuvan-app1.nrsc.gov.in/
wdc2.0/?collection_sno=...`) but this script never follows those links. R3 is
text/numeric registry data only, per the human's explicit instruction.

Writes:
  scripts/output/registry/workcodes_marigaon_wdc1.csv
    work_code, head, activity, drishti_category, pre_status, mid_status,
    post_status, source_url, retrieved_at
  scripts/output/registry/programme_marigaon.json
    registry aggregates + the exact (computed, not estimated) moderation
    backlog — read by api/app/routers/programme.py.

Usage: `python scripts/fetch_gt2.py` (run from anywhere; paths below are
resolved relative to this file, not the cwd).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote_plus

import requests

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

BASE_URL = "https://wdcpmksy.dolr.gov.in"
SCRIPTS_DIR = Path(__file__).resolve().parent
CACHE_DIR = SCRIPTS_DIR / "cache" / "gt2"
OUTPUT_DIR = SCRIPTS_DIR / "output" / "registry"

# Identifies this script per REAL_DATA_PLAN.md's "identify yourself in the
# User-Agent" rule — a government sysadmin looking at access logs should be
# able to tell what this traffic is and who to contact about it.
USER_AGENT = (
    "SAKSHYA-SIH26015-ResearchBot/1.0 "
    "(SIH 2026 hackathon project PS 26015, non-commercial research use; "
    "contact: abhijeetrou123@gmail.com)"
)
RATE_LIMIT_SECONDS = 1.2  # stricter than REAL_DATA_PLAN.md's "<=1 req/sec"

# Drill-down target: Marigaon district, Assam (REAL_DATA_PLAN.md §0, §1).
STATE_CODE = 18
STATE_NAME = "ASSAM"
DIST_NAME = "MARIGAON"  # source portal's spelling; this project's own data
# (scripts/config/watershed.yaml, api/app/services/district_coverage.py)
# uses the standard spelling "Morigaon" downstream of this script.
FOCUS_PROJECT_NAME_HINT = "WDC - 1"  # distinguishes WDC-1 from WDC-2 by name

# REAL_DATA_PLAN.md §5's proposed activity -> PRD §15.1 category mapping.
# Order matters: first matching keyword wins. Anything matching nothing
# falls through to OM ("Others") — PRD §15.1's own catch-all — and is
# recorded in `unmapped_activities` in the output JSON for human review,
# rather than silently invented as something more specific than it is.
_CATEGORY_KEYWORDS: list[tuple[str, str]] = [
    ("farm pond", "PT"),
    ("amrit sarovar", "PT"),
    ("check dam", "SM"),
    ("bunding", "BN"),  # covers "Contour Bunding" and "Graded Bunding"
    ("bund", "BN"),
    ("irrigation", "NC"),
    ("drainage channel", "NC"),
    ("channel", "NC"),
    ("goatery", "LS"),
    ("piggery", "LS"),
    ("dairy", "LS"),
    ("duckery", "LS"),
    ("bee keeping", "LH"),
    ("weaving", "LH"),
    ("handloom", "LH"),
    ("hand craft", "LH"),
    ("handicraft", "LH"),
    ("horticulture", "LH"),
    ("fisheries", "LH"),
]
_DEFAULT_CATEGORY = "OM"
_VALID_CATEGORIES = {"AM", "VM", "SM", "PT", "NC", "BN", "LS", "LH", "OM"}


def map_activity_to_category(activity: str) -> str:
    """REAL_DATA_PLAN.md §5's mapping, by keyword. Never returns anything
    outside PRD §15.1's fixed 9 codes (CLAUDE.md: "Don't invent new
    categories.")."""
    lowered = activity.lower()
    for keyword, category in _CATEGORY_KEYWORDS:
        if keyword in lowered:
            assert category in _VALID_CATEGORIES
            return category
    return _DEFAULT_CATEGORY


# --------------------------------------------------------------------------
# Polite, cache-first fetching
# --------------------------------------------------------------------------


class _GovSession:
    """Cache-first GET against wdcpmksy.dolr.gov.in, with a one-time
    session bootstrap (see module docstring).

    Every successful live fetch is written to CACHE_DIR before anything
    else happens to it, so a crash mid-parse never costs a re-fetch.
    """

    def __init__(self, *, force: bool = False) -> None:
        self._session: requests.Session | None = None
        self._bootstrapped = False
        self._force = force

    def _ensure_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
        return self._session

    def get(self, cache_key: str, path: str, params: dict, referer: str | None) -> str:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        html_path = CACHE_DIR / f"{cache_key}.html"
        meta_path = CACHE_DIR / f"{cache_key}.meta.json"
        if not self._force and html_path.exists() and meta_path.exists():
            print(f"[cache hit] {cache_key}", file=sys.stderr)
            return html_path.read_text(encoding="utf-8")

        session = self._ensure_session()
        if not self._bootstrapped:
            print("[fetch] bootstrap session: GET /", file=sys.stderr)
            session.get(f"{BASE_URL}/", timeout=30)
            self._bootstrapped = True
            time.sleep(RATE_LIMIT_SECONDS)

        url = f"{BASE_URL}/{path}"
        print(f"[fetch] {url} params={params}", file=sys.stderr)
        headers = {"X-Requested-With": "XMLHttpRequest"}
        if referer:
            headers["Referer"] = referer
        resp = session.get(url, params=params, headers=headers, timeout=60)
        resp.raise_for_status()
        text = resp.text
        if "pagenotfound.jsp" in text or "error404" in text:
            raise RuntimeError(
                f"{cache_key}: server returned its 404/error page for {resp.url} "
                "(session bootstrap likely failed, or params are wrong)"
            )
        html_path.write_text(text, encoding="utf-8")
        meta_path.write_text(
            json.dumps(
                {
                    "url": resp.url,
                    "status": resp.status_code,
                    "content_type": resp.headers.get("content-type", ""),
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        time.sleep(RATE_LIMIT_SECONDS)
        return text

    def retrieved_at(self, cache_key: str) -> str:
        meta_path = CACHE_DIR / f"{cache_key}.meta.json"
        if meta_path.exists():
            return json.loads(meta_path.read_text(encoding="utf-8"))["retrieved_at"]
        return datetime.now(timezone.utc).isoformat()

    def source_url(self, cache_key: str) -> str:
        meta_path = CACHE_DIR / f"{cache_key}.meta.json"
        if meta_path.exists():
            return json.loads(meta_path.read_text(encoding="utf-8"))["url"]
        return BASE_URL


# --------------------------------------------------------------------------
# HTML table parsing — BY COLUMN INDEX, not text order (REAL_DATA_PLAN.md §5
# explicitly warns raw-text parsing loses column alignment on these
# rowspan/colspan-heavy government report tables).
# --------------------------------------------------------------------------


@dataclass
class _Cell:
    text: str
    href: str | None = None


@dataclass
class _Row:
    group: str | None  # section header in effect for this row (NRM/EPA/...), or None
    cells: list[_Cell] = field(default_factory=list)


class _TableRowParser(HTMLParser):
    """Walks a GT2 report page's `<table id="dtBasicExample"><tbody>` and
    emits one `_Row` per data row, indexed by column position.

    A "group header" row (this report's convention for grouping work codes
    under NRM / EPA / Livelihood / Production) is a `<tr>` containing a
    single `<td colspan="...">` — recognised structurally (single cell +
    colspan present), not by sniffing for particular header text, so it
    doesn't silently misparse if the government changes group names.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[_Row] = []
        self._in_tbody = False
        self._in_tr = False
        self._cells: list[_Cell] | None = None
        self._in_td = False
        self._td_text_parts: list[str] = []
        self._td_href: str | None = None
        self._row_has_colspan = False
        self._current_group: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        if tag == "tbody":
            self._in_tbody = True
        elif tag == "tr" and self._in_tbody:
            self._in_tr = True
            self._cells = []
            self._row_has_colspan = False
        elif tag == "td" and self._in_tr:
            self._in_td = True
            self._td_text_parts = []
            self._td_href = None
            if attr_map.get("colspan"):
                self._row_has_colspan = True
        elif tag == "a" and self._in_td:
            href = attr_map.get("href")
            if href:
                self._td_href = href

    def handle_endtag(self, tag: str) -> None:
        if tag == "tbody":
            self._in_tbody = False
        elif tag == "tr" and self._in_tr:
            self._in_tr = False
            cells = self._cells or []
            if len(cells) == 1 and self._row_has_colspan:
                text = cells[0].text.strip()
                if text:
                    self._current_group = text
            elif cells:
                # Skip the numbered `<th>` header-index row (1,2,3,...) —
                # it lives inside <tbody> in this markup but has no <td>s,
                # so `cells` (built from <td> only) is already empty for it
                # and this branch is never reached for that row.
                self.rows.append(_Row(group=self._current_group, cells=cells))
            self._cells = None
        elif tag == "td" and self._in_td:
            self._in_td = False
            text = " ".join("".join(self._td_text_parts).split())  # collapse whitespace
            assert self._cells is not None
            self._cells.append(_Cell(text=text, href=self._td_href))

    def handle_data(self, data: str) -> None:
        if self._in_td:
            self._td_text_parts.append(data)


def _parse_rows(html: str) -> list[_Row]:
    parser = _TableRowParser()
    parser.feed(html)
    return parser.rows


def _href_query(href: str) -> dict[str, str]:
    """`getProjWiseAssetGeoData?dcode=296&stname=ASSAM&distname=MARIGAON`
    -> {'dcode': '296', 'stname': 'ASSAM', 'distname': 'MARIGAON'}."""
    if "?" not in href:
        return {}
    query = href.split("?", 1)[1]
    out: dict[str, str] = {}
    for part in query.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            # unquote_plus (not unquote): standard query-string decoding
            # where literal "+" means space. In practice this site's own
            # href markup carries values like "MARIGAON-WDC - 1 /2021-22"
            # completely unencoded (no % or + at all), so this is a no-op
            # against the live pages — kept correct anyway for hrefs that
            # do arrive percent/plus-encoded.
            out[k] = unquote_plus(v)
    return out


def _int(text: str) -> int:
    return int(text.strip().replace(",", ""))


# --------------------------------------------------------------------------
# Level-specific extraction
# --------------------------------------------------------------------------


def find_district_row(rows: list[_Row], district_name: str) -> dict:
    """District-level table columns (by index, confirmed against the live
    header row 2026-09-28): 0 S.No, 1 District Name (link -> dcode), 2 Total
    Projects, 3-6 NRM(total/not_started/ongoing/completed), 7-10 EPA(...),
    11-14 Livelihood(...), 15-18 Production(...), 19 Total Work Code, 20
    Total Geotag, 21 Total Non-Geotag."""
    for row in rows:
        if len(row.cells) < 22:
            continue  # not a full district data row (e.g. a merged-cell Grand Total row)
        if row.cells[1].text.strip().upper() == district_name.upper():
            href = row.cells[1].href or ""
            params = _href_query(href)
            c = row.cells
            return {
                "district": c[1].text.strip(),
                "dcode": int(params["dcode"]),
                "total_projects": _int(c[2].text),
                "nrm_total": _int(c[3].text),
                "epa_total": _int(c[7].text),
                "livelihood_total": _int(c[11].text),
                "production_total": _int(c[15].text),
                "total_work_codes": _int(c[19].text),
                "geotagged_work_codes": _int(c[20].text),
                "non_geotagged_work_codes": _int(c[21].text),
            }
    raise ValueError(f"district {district_name!r} not found in district-level table")


def parse_project_rows(rows: list[_Row]) -> list[dict]:
    """Project-level table columns (by index): 0 S.No, 1 Project Name (link
    -> projid/stname/distname/projname), 2-5 NRM(...), 6-9 EPA(...), 10-13
    Livelihood(...), 14-17 Production(...), 18 Total Work Code, 19 Total
    Geotag, 20 Total Non-Geotag."""
    out = []
    for row in rows:
        c = row.cells
        if len(c) < 21:
            continue  # not a full project data row (e.g. a merged-cell Grand Total row)
        href = c[1].href or ""
        params = _href_query(href)
        if "projid" not in params:
            continue
        out.append(
            {
                "project_id": int(params["projid"]),
                "project_name": params.get("projname", c[1].text.strip()),
                "nrm_total": _int(c[2].text),
                "epa_total": _int(c[6].text),
                "livelihood_total": _int(c[10].text),
                "production_total": _int(c[14].text),
                "total_work_codes": _int(c[18].text),
                "geotagged_work_codes": _int(c[19].text),
                "non_geotagged_work_codes": _int(c[20].text),
            }
        )
    return out


_STATUS_MAP = {
    "": "not_submitted",  # no status text at all -> nothing submitted for this stage yet
    "accepted": "accepted",
    "rejected": "rejected",
    "yet to moderate": "yet_to_moderate",
}
_KNOWN_STATUS_WORDS = ("accepted", "rejected", "yet to moderate")


def _normalize_status(raw: str) -> tuple[str, str]:
    """Returns (display_value, status_slug).

    Blank cell -> ("Not Submitted", "not_submitted") — a real 4th state
    found in the data, distinct from "Yet to Moderate" (submitted,
    awaiting review): REAL_DATA_PLAN.md §1 only names Accepted/Yet to
    Moderate/Rejected, this script's own finding is that a 4th, unlabelled
    blank state also occurs (no photo submitted at that stage yet).

    A cell can ALSO carry more than one status word (found empirically:
    work code P18296000090-3753272's Pre-Implementation cell literally
    reads "Accepted Rejected" — two separate photo submissions at the same
    stage with different moderation outcomes). Slug "mixed" in that case,
    kept as its own bucket rather than force-fit into one status or
    silently dropped from the denominator."""
    cleaned = raw.strip()
    if not cleaned:
        return "Not Submitted", "not_submitted"
    lowered = cleaned.lower()
    if lowered in _STATUS_MAP:
        return cleaned, _STATUS_MAP[lowered]
    matched = [w for w in _KNOWN_STATUS_WORDS if w in lowered]
    if len(matched) > 1:
        return cleaned, "mixed"
    if len(matched) == 1:
        return cleaned, _STATUS_MAP[matched[0]]
    return cleaned, "other"


@dataclass
class WorkCodeRow:
    work_code: str
    head: str
    activity: str
    drishti_category: str
    pre_status: str
    mid_status: str
    post_status: str
    pre_slug: str
    mid_slug: str
    post_slug: str


def parse_workcode_rows(rows: list[_Row]) -> list[WorkCodeRow]:
    """Work-code detail table columns (by index): 0 S.No, 1 Work Code, 2
    Head Name, 3 Activity Name, 4 Pre Implementation, 5 Mid Implementation,
    6 Post Implementation. `group` (NRM/EPA/Livelihood/Production) comes
    from the preceding section-header row, not used in the category
    mapping itself (mapping is by activity-name keyword per
    REAL_DATA_PLAN.md §5), only carried for provenance/debugging."""
    out = []
    for row in rows:
        c = row.cells
        if len(c) < 7:
            continue  # defensive: skip anything that isn't a 7-column data row
        work_code = c[1].text.strip()
        if not work_code:
            continue
        activity = c[3].text.strip()
        pre_display, pre_slug = _normalize_status(c[4].text)
        mid_display, mid_slug = _normalize_status(c[5].text)
        post_display, post_slug = _normalize_status(c[6].text)
        out.append(
            WorkCodeRow(
                work_code=work_code,
                head=c[2].text.strip(),
                activity=activity,
                drishti_category=map_activity_to_category(activity),
                pre_status=pre_display,
                mid_status=mid_display,
                post_status=post_display,
                pre_slug=pre_slug,
                mid_slug=mid_slug,
                post_slug=post_slug,
            )
        )
    return out


# --------------------------------------------------------------------------
# Output writers
# --------------------------------------------------------------------------


def write_csv(path: Path, rows: list[WorkCodeRow], source_url: str, retrieved_at: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "work_code",
                "head",
                "activity",
                "drishti_category",
                "pre_status",
                "mid_status",
                "post_status",
                "source_url",
                "retrieved_at",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    r.work_code,
                    r.head,
                    r.activity,
                    r.drishti_category,
                    r.pre_status,
                    r.mid_status,
                    r.post_status,
                    source_url,
                    retrieved_at,
                ]
            )


def _stage_backlog(rows: list[WorkCodeRow], slug_attr: str) -> dict:
    counts = Counter(getattr(r, slug_attr) for r in rows)
    total = len(rows)
    result = {
        "accepted": counts.get("accepted", 0),
        "yet_to_moderate": counts.get("yet_to_moderate", 0),
        "rejected": counts.get("rejected", 0),
        "not_submitted": counts.get("not_submitted", 0),
        "mixed": counts.get("mixed", 0),  # e.g. "Accepted Rejected" — two submissions, different outcomes
        "other": counts.get("other", 0),  # unrecognised status text, if any — should be 0 in practice
        "yet_to_moderate_pct_of_geotagged": (
            round(counts.get("yet_to_moderate", 0) / total * 100, 1) if total else 0.0
        ),
    }
    assert (
        sum(result[k] for k in ("accepted", "yet_to_moderate", "rejected", "not_submitted", "mixed", "other"))
        == total
    ), f"status bucket counts don't sum to total rows ({total}) for {slug_attr} — a status value slipped through unclassified"
    return result


def build_programme_summary(
    *,
    district: dict,
    projects: list[dict],
    focus_project: dict,
    workcode_rows: list[WorkCodeRow],
    source_urls: dict[str, str],
    retrieved_ats: dict[str, str],
) -> dict:
    total_registry = focus_project["total_work_codes"]  # 263 for WDC-1: includes non-geotagged
    geotagged_in_table = len(workcode_rows)  # 240: this table only lists geotagged work codes

    category_counts = Counter(r.drishti_category for r in workcode_rows)
    category_breakdown = [
        {
            "category": cat,
            "work_code_count": category_counts.get(cat, 0),
            "share_pct_of_geotagged": (
                round(category_counts.get(cat, 0) / geotagged_in_table * 100, 1)
                if geotagged_in_table
                else 0.0
            ),
        }
        for cat in sorted(_VALID_CATEGORIES)
        if category_counts.get(cat, 0) > 0
    ]

    unmapped_activities = sorted(
        {r.activity for r in workcode_rows if r.drishti_category == _DEFAULT_CATEGORY}
    )

    moderation_backlog = {
        stage: _stage_backlog(workcode_rows, f"{stage}_slug") for stage in ("pre", "mid", "post")
    }

    return {
        "district": "Morigaon",  # this project's standard spelling; see DIST_NAME note above
        "district_source_spelling": district["district"],
        "state": STATE_NAME.title(),
        "district_total_projects": district["total_projects"],
        "district_total_work_codes": district["total_work_codes"],
        "district_geotagged_work_codes": district["geotagged_work_codes"],
        "district_non_geotagged_work_codes": district["non_geotagged_work_codes"],
        "projects": projects,
        "focus_project": {
            **focus_project,
            "note": (
                "The work-code detail drill-down (this script's main target) lists "
                f"only the {geotagged_in_table} GEOTAGGED work codes out of this "
                f"project's {total_registry} total — the {total_registry - geotagged_in_table} "
                "non-geotagged ones have no photo submitted at any stage, so they "
                "carry no Pre/Mid/Post status and are outside this table."
            ),
        },
        "category_breakdown": category_breakdown,
        "unmapped_activities": unmapped_activities,
        "moderation_backlog": moderation_backlog,
        "moderation_backlog_denominator": geotagged_in_table,
        "moderation_backlog_note": (
            "Percentages are of the "
            f"{geotagged_in_table} geotagged work codes in the focus project "
            f"({focus_project['project_name']}) that actually have a Pre/Mid/Post "
            "submission to moderate — not of the district's full registry. "
            "'not_submitted' means no photo was uploaded for that stage yet "
            "(e.g. mid/post-implementation photos for a still-early work), which "
            "is a distinct state from 'yet_to_moderate' (a photo was submitted and "
            "is awaiting a moderator's Accept/Reject decision) found empirically "
            "in this data, not documented anywhere in REAL_DATA_PLAN.md. A 'mixed' "
            "bucket also exists for the rare work code with two submissions at the "
            "same stage and different outcomes (e.g. one Accepted, one Rejected) — "
            "also found empirically, not force-fit into a single status."
        ),
        "activity_category_mapping_source": "docs/REAL_DATA_PLAN.md §5",
        "source_report": "WDC-PMKSY 2.0 MIS, Report GT2 (Work Code Status with Geotagging Details)",
        "source_urls": source_urls,
        "retrieved_at": retrieved_ats,
        "is_synthetic": False,
    }


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force", action="store_true", help="bypass the on-disk HTML cache and re-fetch everything"
    )
    args = parser.parse_args()

    gov = _GovSession(force=args.force)
    source_urls: dict[str, str] = {}
    retrieved_ats: dict[str, str] = {}

    # 1. State level — establishes the drill-down starts here, per plan §1.
    state_html = gov.get("state_all", "getAllAssetGeoData", {}, referer=None)
    source_urls["state"] = gov.source_url("state_all")
    retrieved_ats["state"] = gov.retrieved_at("state_all")
    state_rows = _parse_rows(state_html)
    # State-level table has the same column layout as district-level (S.No,
    # Name(+link), Total Projects, NRM/EPA/Livelihood/Production blocks,
    # Total/Geotag/NonGeotag) — confirmed against the live header row.
    assam_link = next(
        (
            row.cells[1].href
            for row in state_rows
            if len(row.cells) > 1 and row.cells[1].text.strip().upper() == STATE_NAME
        ),
        None,
    )
    if assam_link is None:
        raise RuntimeError(f"could not find {STATE_NAME!r} row in the state-level GT2 table")
    assam_params = _href_query(assam_link)
    stcode = int(assam_params["stcode"])
    assert stcode == STATE_CODE, f"discovered stcode {stcode} != expected {STATE_CODE}"

    # 2. District level for Assam — cross-check point for GET /districts/geotag-coverage.
    district_html = gov.get(
        f"district_{STATE_NAME}",
        "getDistWiseAssetGeoData",
        {"stcode": stcode, "stname": STATE_NAME},
        referer=f"{BASE_URL}/getAllAssetGeoData",
    )
    source_urls["district"] = gov.source_url(f"district_{STATE_NAME}")
    retrieved_ats["district"] = gov.retrieved_at(f"district_{STATE_NAME}")
    district_rows = _parse_rows(district_html)
    district = find_district_row(district_rows, DIST_NAME)

    # 3. Project level for Marigaon.
    project_html = gov.get(
        f"project_{DIST_NAME}",
        "getProjWiseAssetGeoData",
        {"dcode": district["dcode"], "stname": STATE_NAME, "distname": DIST_NAME},
        referer=f"{BASE_URL}/getDistWiseAssetGeoData?stcode={stcode}&stname={STATE_NAME}",
    )
    source_urls["project"] = gov.source_url(f"project_{DIST_NAME}")
    retrieved_ats["project"] = gov.retrieved_at(f"project_{DIST_NAME}")
    project_rows_raw = _parse_rows(project_html)
    projects = parse_project_rows(project_rows_raw)
    if not projects:
        raise RuntimeError("no projects parsed from the project-level GT2 table for Marigaon")
    focus_project = next((p for p in projects if FOCUS_PROJECT_NAME_HINT in p["project_name"]), None)
    if focus_project is None:
        raise RuntimeError(f"no project matching {FOCUS_PROJECT_NAME_HINT!r} found for Marigaon")

    # 4. Work-code detail for the focus project (WDC-1).
    projdtl_key = f"projectdetail_{focus_project['project_id']}"
    projdtl_html = gov.get(
        projdtl_key,
        "getProjDtlAssetGeoData",
        {
            "projid": focus_project["project_id"],
            "stname": STATE_NAME,
            "distname": DIST_NAME,
            "projname": focus_project["project_name"],
        },
        referer=(
            f"{BASE_URL}/getProjWiseAssetGeoData?dcode={district['dcode']}"
            f"&stname={STATE_NAME}&distname={DIST_NAME}"
        ),
    )
    source_urls["work_code_detail"] = gov.source_url(projdtl_key)
    retrieved_ats["work_code_detail"] = gov.retrieved_at(projdtl_key)
    projdtl_rows_raw = _parse_rows(projdtl_html)
    workcode_rows = parse_workcode_rows(projdtl_rows_raw)
    if not workcode_rows:
        raise RuntimeError("no work codes parsed from the work-code detail table — check the cache/parser")

    print(
        f"Parsed {len(workcode_rows)} geotagged work codes for "
        f"{focus_project['project_name']} (registry total {focus_project['total_work_codes']})",
        file=sys.stderr,
    )

    csv_path = OUTPUT_DIR / "workcodes_marigaon_wdc1.csv"
    write_csv(csv_path, workcode_rows, source_urls["work_code_detail"], retrieved_ats["work_code_detail"])
    print(f"Wrote {csv_path}", file=sys.stderr)

    summary = build_programme_summary(
        district=district,
        projects=projects,
        focus_project=focus_project,
        workcode_rows=workcode_rows,
        source_urls=source_urls,
        retrieved_ats=retrieved_ats,
    )
    json_path = OUTPUT_DIR / "programme_marigaon.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote {json_path}", file=sys.stderr)

    # Human-readable summary on stdout.
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
