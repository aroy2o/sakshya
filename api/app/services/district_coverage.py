"""GET /districts/geotag-coverage — PRD §9 / FR5.5.

REAL data, not placeholder. Source: WDC-PMKSY 2.0 MIS, Report GT2 ("Work Code
Status with Geotagging Details") and its per-state district drill-down,
Department of Land Resources, Ministry of Rural Development, Government of
India — https://wdcpmksy.dolr.gov.in/getAllAssetGeoData (state-level) and
https://wdcpmksy.dolr.gov.in/getDistWiseAssetGeoData?stcode=<n>&stname=<STATE>
(district-level; stcode=18 ASSAM, 17 MEGHALAYA, 16 TRIPURA). Live-fetched and
transcribed 2026-09-28 (report timestamp on the page: "Report as on:
28/09/2026 01:09 PM"). PLAYBOOK.md §1.4 independently cites the same GT2
report from a slightly earlier date with matching-within-live-drift totals
(Assam 15,178/13,972 there vs 15,178/13,974 here — the MIS "updates live",
per PLAYBOOK's own caveat) - that agreement is what gives this transcription
confidence, on top of every state's district rows summing exactly to its own
reported grand total (checked by hand for all three states below).

CLAUDE.md non-negotiable: "never fabricate a number... use a clearly-labeled
placeholder... don't silently invent a plausible-looking one." This is the
other side of that rule — real numbers were found, so they're used as-is
(not smoothed, not rounded away from source), with the source cited here
instead of a placeholder flag.

Assam is the priority (our demo watershed's district, PRD §14) - all 31
Assam districts are included, not just Morigaon, since the full state table
was available at no extra cost. Meghalaya and Tripura included too (PRD
§14's backup-watershed states / PLAYBOOK §1.4's own "North-East angle"),
giving the choropleth real multi-state variety rather than a single dot.

District name note: the source portal spells our demo district "MARIGAON"
(an older transliteration still used in some GoI systems); this project's
own data (scripts/config/watershed.yaml's `district` field) uses the current
standard spelling "Morigaon" — used here too, for consistency with the rest
of this API's data, not because the source was wrong.

Data-quality note, not silently smoothed away: four Assam districts report
geotagged_works slightly *exceeding* total_works in the live source
(Dhubri, Golaghat, Kamrup Metro, Karbi Anglong) - a reconciliation quirk in
the government's own live MIS, not a transcription error here (every
district's raw total_works/geotagged_works below is copied verbatim from the
source). geotag_coverage_pct is clamped to 100.0 for these rows only because
PRD §9's response schema (mirrored by frontend's zDistrictCoverage) requires
0-100; the raw counts are left untouched.
"""

from __future__ import annotations

# (district, state, total_works, geotagged_works)
_RAW_DISTRICT_DATA: list[tuple[str, str, int, int]] = [
    # --- Assam (stcode=18) - all 31 districts, source GT2 district drill-down ---
    ("Baksa", "Assam", 599, 596),
    ("Barpeta", "Assam", 681, 662),
    ("Bongaigaon", "Assam", 523, 519),
    ("Cachar", "Assam", 445, 365),
    ("Charaideo", "Assam", 46, 27),
    ("Chirang", "Assam", 609, 604),
    ("Darrang", "Assam", 688, 686),
    ("Dhemaji", "Assam", 469, 462),
    ("Dhubri", "Assam", 628, 633),  # source anomaly: geotagged > total, see module docstring
    ("Dibrugarh", "Assam", 442, 442),
    ("Dima Hasao", "Assam", 468, 391),
    ("Goalpara", "Assam", 541, 495),
    ("Golaghat", "Assam", 592, 595),  # source anomaly: geotagged > total, see module docstring
    ("Hailakandi", "Assam", 552, 431),
    ("Hojai", "Assam", 307, 297),
    ("Jorhat", "Assam", 647, 564),
    ("Kamrup", "Assam", 458, 414),
    ("Kamrup Metro", "Assam", 59, 60),  # source anomaly: geotagged > total, see module docstring
    ("Karbi Anglong", "Assam", 1056, 1111),  # source anomaly: geotagged > total, see module docstring
    ("Kokrajhar", "Assam", 749, 729),
    ("Lakhimpur", "Assam", 622, 546),
    ("Majuli", "Assam", 404, 368),
    ("Morigaon", "Assam", 309, 267),  # our demo watershed's district (PRD §14) - source spells it "Marigaon"
    ("Nagaon", "Assam", 364, 277),
    ("Nalbari", "Assam", 723, 694),
    ("Sivasagar", "Assam", 351, 272),
    ("Sonitpur", "Assam", 234, 189),
    ("Tamulpur", "Assam", 47, 44),
    ("Tinsukia", "Assam", 441, 440),
    ("Udalguri", "Assam", 500, 478),
    ("West Karbi Anglong", "Assam", 624, 316),
    # --- Meghalaya (stcode=17) - all 12 districts ---
    ("Eastern West Khasi Hills", "Meghalaya", 636, 251),
    ("East Garo Hills", "Meghalaya", 573, 191),
    ("East Jaintia Hills", "Meghalaya", 1225, 443),
    ("East Khasi Hills", "Meghalaya", 971, 171),
    ("North Garo Hills", "Meghalaya", 827, 323),
    ("Ri Bhoi", "Meghalaya", 1687, 606),
    ("South Garo Hills", "Meghalaya", 469, 123),
    ("South West Garo Hills", "Meghalaya", 758, 326),
    ("South West Khasi Hills", "Meghalaya", 2201, 1000),
    ("West Garo Hills", "Meghalaya", 792, 212),
    ("West Jaintia Hills", "Meghalaya", 2673, 443),
    ("West Khasi Hills", "Meghalaya", 648, 210),
    # --- Tripura (stcode=16) - all 8 districts ---
    ("Dhalai", "Tripura", 3262, 485),
    ("Gomati", "Tripura", 3011, 509),
    ("Khowai", "Tripura", 2490, 583),
    ("North Tripura", "Tripura", 1053, 81),
    ("Sepahijala", "Tripura", 1409, 421),
    ("South Tripura", "Tripura", 1965, 428),
    ("Unakoti", "Tripura", 756, 90),
    ("West Tripura", "Tripura", 1702, 197),
]

SOURCE_REPORT = "WDC-PMKSY 2.0 MIS, Report GT2 (Work Code Status with Geotagging Details)"
SOURCE_URL = "https://wdcpmksy.dolr.gov.in/getAllAssetGeoData"
AS_OF = "2026-09-28"


def get_district_coverage() -> list[dict]:
    rows = []
    for district, state, total_works, geotagged_works in _RAW_DISTRICT_DATA:
        pct = round(geotagged_works / total_works * 100, 1) if total_works else 0.0
        rows.append(
            {
                "district": district,
                "state": state,
                "total_works": total_works,
                "geotagged_works": geotagged_works,
                "geotag_coverage_pct": min(pct, 100.0),
                # Additive over frontend's current zDistrictCoverage (silently
                # stripped by zod's non-strict .parse() until they opt in) -
                # traceability for CLAUDE.md's "never fabricate a number":
                # every real number here is one click away from its source.
                "source_report": SOURCE_REPORT,
                "as_of": AS_OF,
            }
        )
    return rows
