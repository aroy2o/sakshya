"""pytest coverage for fetch_gt2.py's HTML table parser and category mapping
(R3, docs/REAL_DATA_PLAN.md §5, §8). No network access — every test feeds
small inline HTML fixtures shaped like the real GT2 report tables (verified
against the live site 2026-09-28, see scripts/cache/gt2/), so this stays
fast and never touches the government server.

Column-index parsing is the thing REAL_DATA_PLAN.md §5 explicitly warns is
easy to get wrong on these rowspan/colspan-heavy tables, so that's the
focus here — not text-order parsing, not "does requests work."
"""

from __future__ import annotations

import pytest

from fetch_gt2 import (
    _normalize_status,
    _parse_rows,
    find_district_row,
    map_activity_to_category,
    parse_project_rows,
    parse_workcode_rows,
)

# --- fixtures shaped like the real report tables (trimmed to what parsing needs) ---

_WORKCODE_TABLE = """
<table id="dtBasicExample" class="table">
<thead><tr><th>S.No.</th><th>Work Code</th><th>Head Name</th><th>Activity Name</th>
<th colspan="3">Stage</th></tr>
<tr><th>Pre</th><th>Mid</th><th>Post</th></tr></thead>
<tbody>
<tr><th>1</th><th>2</th><th>3</th><th>4</th><th>5</th><th>6</th><th>7</th></tr>
<tr style="background-color:grey"><td colspan="8" class="text-center"><b>NRM</b></td></tr>
<tr>
  <td>1</td>
  <td>P18296000090-0001</td>
  <td>Area covered under SMC</td>
  <td>Farm Ponds</td>
  <td style="text-align: center;"><br/><a href="https://bhuvan-app1.nrsc.gov.in/wdc2.0/?collection_sno=1">Accepted </a></td>
  <td style="text-align: center;"></td>
  <td style="text-align: center;"></td>
</tr>
<tr>
  <td>2</td>
  <td>P18296000090-0002</td>
  <td>Area covered under SMC</td>
  <td>Check dams</td>
  <td style="text-align: center;"><br/><a href="#">Yet to Moderate </a></td>
  <td style="text-align: center;"></td>
  <td style="text-align: center;"></td>
</tr>
<tr style="background-color:grey"><td colspan="8" class="text-center"><b>Livelihood</b></td></tr>
<tr>
  <td>3</td>
  <td>P18296000090-0003</td>
  <td>Livelihood Activities</td>
  <td>Goatery</td>
  <td style="text-align: center;"><br/><a href="#">Accepted </a><br/><a href="#">Rejected </a></td>
  <td style="text-align: center;"></td>
  <td style="text-align: center;"></td>
</tr>
</tbody>
</table>
"""

_DISTRICT_TABLE = """
<table id="dtBasicExample" class="table">
<tbody>
<tr><th>1</th></tr>
<tr>
  <td>1</td>
  <td><a href="getProjWiseAssetGeoData?dcode=296&amp;stname=ASSAM&amp;distname=MARIGAON">MARIGAON</a></td>
  <td class="text-right">2</td>
  <td class="text-right">115</td><td class="text-right">12</td><td class="text-right">0</td><td class="text-right">103</td>
  <td class="text-right">15</td><td class="text-right">0</td><td class="text-right">0</td><td class="text-right">15</td>
  <td class="text-right">112</td><td class="text-right">0</td><td class="text-right">0</td><td class="text-right">112</td>
  <td class="text-right">67</td><td class="text-right">0</td><td class="text-right">0</td><td class="text-right">67</td>
  <td class="text-right">309</td><td class="text-right">267</td><td class="text-right">42</td>
</tr>
</tbody>
</table>
"""

_PROJECT_TABLE = """
<table id="dtBasicExample" class="table">
<tbody>
<tr><th>1</th></tr>
<tr>
  <td>1</td>
  <td><a href="getProjDtlAssetGeoData?projid=90&amp;stname=ASSAM&amp;distname=MARIGAON&amp;projname=MARIGAON-WDC+-+1+%2F2021-22">MARIGAON-WDC - 1 /2021-22</a></td>
  <td class="text-right">73</td><td class="text-right">0</td><td class="text-right">0</td><td class="text-right">73</td>
  <td class="text-right">11</td><td class="text-right">0</td><td class="text-right">0</td><td class="text-right">11</td>
  <td class="text-right">112</td><td class="text-right">0</td><td class="text-right">0</td><td class="text-right">112</td>
  <td class="text-right">67</td><td class="text-right">0</td><td class="text-right">0</td><td class="text-right">67</td>
  <td class="text-right">263</td><td class="text-right">240</td><td class="text-right">23</td>
</tr>
</tbody>
</table>
"""


# --- category mapping (REAL_DATA_PLAN.md §5) --------------------------------


@pytest.mark.parametrize(
    "activity,expected",
    [
        ("Farm Ponds", "PT"),
        ("Amrit Sarovar", "PT"),
        ("Check dams", "SM"),
        ("Contour Bunding", "BN"),
        ("Graded Bunding", "BN"),
        ("Irrigation/Drainage Channel", "NC"),
        ("Goatery", "LS"),
        ("Piggery", "LS"),
        ("Dairy", "LS"),
        ("Duckery", "LS"),
        ("Bee Keeping", "LH"),
        ("Weaving", "LH"),
        ("Handloom items", "LH"),
        ("Hand craft production", "LH"),
        ("Horticulture Plantation", "LH"),
        ("Fisheries", "LH"),
    ],
)
def test_map_activity_to_category_matches_plan_table(activity, expected):
    assert map_activity_to_category(activity) == expected


@pytest.mark.parametrize(
    "activity",
    ["Borewell and Hand Pump", "Rural Infrastructure", "Farm implement", "Others", "Something Unheard Of"],
)
def test_map_activity_to_category_defaults_to_OM_never_invents_a_new_code(activity):
    # PRD §15.1's fixed 9 codes only, never a made-up category (CLAUDE.md
    # non-negotiable). Anything not in the plan's explicit table lands on
    # OM ("Others"), not silently guessed as something more specific.
    assert map_activity_to_category(activity) == "OM"


def test_map_activity_to_category_never_returns_outside_the_fixed_9():
    from fetch_gt2 import _VALID_CATEGORIES

    assert _VALID_CATEGORIES == {"AM", "VM", "SM", "PT", "NC", "BN", "LS", "LH", "OM"}


# --- status normalization ----------------------------------------------------


def test_normalize_status_blank_is_not_submitted():
    display, slug = _normalize_status("")
    assert (display, slug) == ("Not Submitted", "not_submitted")


def test_normalize_status_known_values():
    assert _normalize_status("Accepted") == ("Accepted", "accepted")
    assert _normalize_status("Rejected") == ("Rejected", "rejected")
    assert _normalize_status("Yet to Moderate") == ("Yet to Moderate", "yet_to_moderate")


def test_normalize_status_mixed_is_its_own_bucket_not_forced():
    # Real finding in the live data (work code P18296000090-3753272): a
    # cell can carry two statuses. Must not silently collapse to one.
    display, slug = _normalize_status("Accepted Rejected")
    assert slug == "mixed"
    assert "Accepted" in display and "Rejected" in display


# --- table row parsing: column index, not text order -------------------------


def test_workcode_table_parses_by_column_index_and_tracks_group():
    rows = _parse_rows(_WORKCODE_TABLE)
    wc_rows = parse_workcode_rows(rows)
    assert len(wc_rows) == 3

    r0 = wc_rows[0]
    assert r0.work_code == "P18296000090-0001"
    assert r0.head == "Area covered under SMC"
    assert r0.activity == "Farm Ponds"
    assert r0.drishti_category == "PT"
    assert r0.pre_status == "Accepted"
    assert r0.mid_status == "Not Submitted"
    assert r0.post_status == "Not Submitted"

    r1 = wc_rows[1]
    assert r1.activity == "Check dams"
    assert r1.drishti_category == "SM"
    assert r1.pre_slug == "yet_to_moderate"

    # Third row is under the "Livelihood" group header and has a mixed
    # Pre-Implementation status (two <a> tags in one cell).
    r2 = wc_rows[2]
    assert r2.activity == "Goatery"
    assert r2.drishti_category == "LS"
    assert r2.pre_slug == "mixed"


def test_district_row_parsed_by_column_index():
    rows = _parse_rows(_DISTRICT_TABLE)
    district = find_district_row(rows, "MARIGAON")
    assert district["dcode"] == 296
    assert district["total_projects"] == 2
    assert district["total_work_codes"] == 309
    assert district["geotagged_work_codes"] == 267
    assert district["non_geotagged_work_codes"] == 42
    # Column-index sanity: make sure we didn't accidentally read the NRM
    # block's numbers into the district totals or vice versa.
    assert district["nrm_total"] == 115
    assert district["epa_total"] == 15
    assert district["livelihood_total"] == 112
    assert district["production_total"] == 67


def test_district_row_missing_raises_rather_than_returning_wrong_row():
    rows = _parse_rows(_DISTRICT_TABLE)
    with pytest.raises(ValueError):
        find_district_row(rows, "NOT-A-REAL-DISTRICT")


def test_project_rows_parsed_by_column_index():
    rows = _parse_rows(_PROJECT_TABLE)
    projects = parse_project_rows(rows)
    assert len(projects) == 1
    p = projects[0]
    assert p["project_id"] == 90
    assert p["project_name"] == "MARIGAON-WDC - 1 /2021-22"
    assert p["nrm_total"] == 73
    assert p["epa_total"] == 11
    assert p["livelihood_total"] == 112
    assert p["production_total"] == 67
    assert p["total_work_codes"] == 263
    assert p["geotagged_work_codes"] == 240
    assert p["non_geotagged_work_codes"] == 23
