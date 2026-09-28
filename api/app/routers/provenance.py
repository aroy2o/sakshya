"""GET /provenance — Reality Pass R4 (docs/REAL_DATA_PLAN.md §3 rule 2, §8's
R4 row).

Every dataset the project uses, real or synthetic, with its source, licence,
retrieved_at and is_synthetic flag — so every number in the UI traces back
to something concrete. Pure in-process list, no file/DB read, no network
call: the entries themselves are the precomputed artifact (same
precompute-first spirit as GET /programme/marigaon and
GET /mws/{id}/thematic/{layer}, just literal Python instead of a JSON file
since there's no offline "fetch" step that produces this particular list).
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.provenance import ProvenanceEntry
from app.services.provenance_sources import ALL_ENTRIES

router = APIRouter(tags=["provenance"])


@router.get("/provenance", response_model=list[ProvenanceEntry])
def get_provenance() -> list[ProvenanceEntry]:
    return ALL_ENTRIES
