"""GET /programme/marigaon — Reality Pass R3 (docs/REAL_DATA_PLAN.md §5, §8's
R3 row).

Not in PRD.md's original §9 API table (that table predates the Reality
Pass) — added per REAL_DATA_PLAN.md's own explicit instruction to build
this endpoint. Mirrors scripts/fetch_gt2.py's `build_programme_summary()`
output field-for-field; this schema is the typed contract between that
offline script's JSON and the live API's response, same "always
Pydantic-typed at the I/O boundary" convention CLAUDE.md requires
everywhere else.

Serves PS 26015 expected-solution points: (a) a standardized programme-level
view of work-code status/geotagging coverage, and (g) decision support for
the human moderation queue — `moderation_backlog` is literally "what to
moderate first," computed exactly (not estimated) from the real GT2 report.
"""

from __future__ import annotations

from pydantic import BaseModel


class ProgrammeProject(BaseModel):
    project_id: int
    project_name: str
    nrm_total: int
    epa_total: int
    livelihood_total: int
    production_total: int
    total_work_codes: int
    geotagged_work_codes: int
    non_geotagged_work_codes: int


class ProgrammeFocusProject(ProgrammeProject):
    note: str


class ProgrammeCategoryBreakdown(BaseModel):
    category: str  # one of PRD §15.1's fixed 9 codes
    work_code_count: int
    share_pct_of_geotagged: float


class ProgrammeModerationStage(BaseModel):
    accepted: int
    yet_to_moderate: int
    rejected: int
    not_submitted: int
    mixed: int
    other: int
    yet_to_moderate_pct_of_geotagged: float


class ProgrammeMarigaonOut(BaseModel):
    district: str  # standard spelling ("Morigaon"), matches GET /districts/geotag-coverage
    district_source_spelling: str  # the GT2 portal's own spelling ("MARIGAON")
    state: str
    district_total_projects: int
    district_total_work_codes: int
    district_geotagged_work_codes: int
    district_non_geotagged_work_codes: int
    projects: list[ProgrammeProject]
    focus_project: ProgrammeFocusProject
    category_breakdown: list[ProgrammeCategoryBreakdown]
    unmapped_activities: list[str]
    moderation_backlog: dict[str, ProgrammeModerationStage]  # keys: "pre" | "mid" | "post"
    moderation_backlog_denominator: int
    moderation_backlog_note: str
    activity_category_mapping_source: str
    source_report: str
    source_urls: dict[str, str]
    retrieved_at: dict[str, str]
    is_synthetic: bool = False
