#!/usr/bin/env python3
"""
FR2.0 — Photo sourcing for SAKSHYA's AI Image Interpreter (PRD Phase 2).

Generates synthetic photos of watershed structures via Pollinations.ai
(https://image.pollinations.ai/prompt/<description>, no API key needed — PRD §14's
default) and writes a manifest describing each image, for downstream use by:
  - this repo's own batch_classify.py (FR2.4), to test the vision classifier
  - backend-engineer's seed script (PRD FR1.5 / Phase 1), once the local-storage
    path below is confirmed with them at Sync Point 1

Every image is downloaded and persisted LOCALLY at generation time — the
manifest's `pollinations_url` field is kept only as generation provenance, never
as a live reference. CLAUDE.md's precompute-first non-negotiable means the demo
dashboard must not depend on a live third-party call just to render a photo pin.

is_synthetic=True and photo_source='ai_generated' are set on every single record
produced here, unconditionally (CLAUDE.md's is_synthetic/photo_source
non-negotiable — no exceptions, no untagged photos).

Two sets are generated:
  1. The "good" set — one declared activity per prompt, image content matches the
     declared activity. Exercises matches_declared == 'yes' in the classifier.
  2. The "mismatch" set — declared as one activity, but the image is generated for
     a visibly different one. Exists specifically to exercise matches_declared ==
     'no'/'uncertain', and to feed PRD §6's "planted bad records" success metric
     (mirrors PLAYBOOK §10's "check dam photo AI reads as plantation" example).

Usage:
    python3 scripts/generate_synthetic_photos.py --sanity-only   # ~9 images, QA first
    python3 scripts/generate_synthetic_photos.py                 # full good + mismatch sets
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

# PRD §15.1 fixed activity categories — do not invent new ones. Two representative
# activities per category is enough to exercise the classifier across the whole
# fixed vocabulary without over-spending the free Pollinations endpoint's goodwill.
#
# Wording note (found during this script's own sanity-check pass, per the FR2.0
# instruction to say so rather than ship unusable test data): short generic
# descriptions like "Contour bunding on farmland" reliably rendered as plain
# scenic aerial/drone-style landscape shots with no visible engineered structure
# at all -- useless as classifier test material, since even a correct classifier
# can't confirm a structure that isn't in the frame. Descriptions below were
# rewritten to name the concrete material/construction vocabulary of each
# structure and bias toward a close/medium shot instead of a wide scenic one.
#
# AM/BN specifically needed a second round: negating with "not an aerial view" /
# "not from above" did NOT work (the model still defaulted to aerial crop-pattern
# shots regardless, and once even drifted off-subject entirely) -- negation
# phrasing is unreliable here. What did work: putting a person in the frame
# actively standing at / inspecting the structure, which reliably forces
# ground-level framing. Re-verified by inspecting output before the full batch ran.
# Each entry is (short_label, prompt_description). short_label is what actually
# belongs in a DRISHTI-schema field_record.activity (PRD §8) -- a short human
# label like "Check Dam", matching the style of the MISMATCH_SET's declared
# activities below -- not the long descriptive sentence used to drive image
# generation. Keeping these separate avoids a verbose paragraph ending up as an
# "activity" value in the seeded data.
CATEGORY_ACTIVITIES: dict[str, list[tuple[str, str]]] = {
    "AM": [
        (
            "Contour Bund",
            "a farmer standing beside a small earthen contour bund ridge in a green field, inspecting "
            "the grass-covered ridge which reaches his knee, ground-level documentary photo, person "
            "clearly visible in frame",
        ),
        (
            "Bench Terracing",
            "a farmer standing on one of several stepped bench terraces cut into a hillside farm, "
            "looking along the earthen risers, ground-level documentary photo, person clearly visible in frame",
        ),
    ],
    "VM": [
        (
            "Block Plantation",
            "rows of newly planted young sapling trees with bamboo tree guards in a cleared plantation "
            "block, close-medium shot",
        ),
        (
            "Grass Turfing",
            "strips of grass turf laid on a bare eroded slope for soil stabilization, close view of the turf patches",
        ),
    ],
    "SM": [
        (
            "Check Dam",
            "a small concrete check dam wall with a spillway crossing a narrow stream, water pooling "
            "behind it, close-medium shot of the dam wall",
        ),
        (
            "Boulder Check Structure",
            "a boulder check structure made of stacked stones blocking a small gully, close view of the rock structure",
        ),
    ],
    "PT": [
        ("Farm Pond", "a farm pond lined with a plastic sheet, close-medium shot of the pond edge and lining"),
        (
            "Percolation Tank",
            "a percolation tank, a small excavated water body with an earthen embankment wall, medium shot",
        ),
    ],
    "NC": [
        (
            "Nala Deepening",
            "a freshly excavated and widened nala stream channel with cut earthen banks and visible "
            "excavator marks, close-medium shot",
        ),
        (
            "Diversion Channel",
            "a stone-lined diversion channel with stone pitching visible on the channel walls, close view",
        ),
    ],
    "BN": [
        (
            "Earthen Bund",
            "a farmer standing beside a low earthen bund wall about waist-high along a field edge, "
            "inspecting the packed-soil wall, ground-level documentary photo, person clearly visible in frame",
        ),
        (
            "Boulder Bund",
            "a farmer standing beside a boulder bund, a low wall of stacked stones along a farm boundary, "
            "ground-level documentary photo, person clearly visible in frame",
        ),
    ],
    "LS": [
        ("Cattle Shelter", "a cattle shelter shed on a rural farm"),
        ("Livestock Health Camp", "a livestock health camp under a tent with cattle nearby"),
    ],
    "LH": [
        ("Horticulture Orchard", "a horticulture orchard with rows of young fruit saplings"),
        ("Fisheries Pond", "a small fish pond dug for a fisheries livelihood scheme, medium shot"),
    ],
    "OM": [
        (
            "Jungle Clearance",
            "a worker clearing jungle undergrowth with a machete, cut branches and felled small trees "
            "scattered on the ground, freshly cleared patch with visible tree stumps, ground-level "
            "documentary photo, person clearly visible in frame",
        ),
        ("Agro Service Centre", "an agro service centre building in a rural village"),
    ],
}

# Declared as one activity, generated as a visibly different one — deliberately
# planted classifier mismatches (distinct from backend-engineer's FR1.5 geo-
# integrity bad rows, which test EXIF/boundary/duplicate logic, not visual match).
MISMATCH_SET: list[dict[str, str]] = [
    {
        "declared_category": "SM",
        "declared_activity": "Check Dam",
        "actual_prompt_activity": "rows of newly planted young sapling trees with bamboo tree guards in a cleared plantation block, close-medium shot",
        "ground_truth_category": "VM",
    },
    {
        "declared_category": "PT",
        "declared_activity": "Farm Pond",
        "actual_prompt_activity": "a farmer standing beside a low earthen bund wall about waist-high along a field edge, inspecting the packed-soil wall, ground-level documentary photo, person clearly visible in frame",
        "ground_truth_category": "BN",
    },
    {
        "declared_category": "VM",
        "declared_activity": "Block Plantation",
        "actual_prompt_activity": "a small concrete check dam wall with a spillway crossing a narrow stream, water pooling behind it, close-medium shot of the dam wall",
        "ground_truth_category": "SM",
    },
    {
        "declared_category": "BN",
        "declared_activity": "Contour Bund",
        "actual_prompt_activity": "a cattle shelter shed on a rural farm",
        "ground_truth_category": "LS",
    },
]

PROMPT_SUFFIX = (
    "in rural India, watershed development programme, eye-level ground photograph "
    "(not an aerial or drone view), a person's-eye-height shot standing next to the structure, "
    "realistic daylight photo, documentary style"
)
DEFAULT_WIDTH = 768
DEFAULT_HEIGHT = 512
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"
DOWNLOAD_TIMEOUT_S = 30
DOWNLOAD_RETRIES = 2
POLITE_DELAY_S = 0.5  # between requests to the free endpoint


@dataclass
class PhotoRecord:
    id: str
    declared_category: str
    declared_activity: str
    actual_prompt: str
    ground_truth_category: str  # what the image actually depicts -- mock-provider / eval ground truth
    is_mismatch_test: bool
    local_path: str
    pollinations_seed: int
    pollinations_url: str  # provenance only, never treated as a live source
    width: int
    height: int
    is_synthetic: bool = True
    photo_source: str = "ai_generated"
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def build_url(prompt: str, seed: int, width: int, height: int) -> str:
    encoded = quote(prompt)
    return f"{POLLINATIONS_BASE}/{encoded}?width={width}&height={height}&seed={seed}&nologo=true"


def download_image(url: str, dest: Path, *, timeout: int = DOWNLOAD_TIMEOUT_S, retries: int = DOWNLOAD_RETRIES) -> None:
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            if not content_type.startswith("image/"):
                raise ValueError(f"unexpected content-type: {content_type!r}")
            dest.write_bytes(resp.content)
            return
        except Exception as exc:  # noqa: BLE001 -- deliberately broad; retried, then re-raised below
            last_exc = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"failed to download {url} after {retries + 1} attempt(s): {last_exc}")


def generate_good_set(
    out_dir: Path, *, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT, seed_base: int = 1000
) -> list[PhotoRecord]:
    records: list[PhotoRecord] = []
    seed = seed_base
    for category, activities in CATEGORY_ACTIVITIES.items():
        for i, (label, description) in enumerate(activities):
            prompt = f"{description}, {PROMPT_SUFFIX}"
            rec_id = f"{category.lower()}_{i + 1:02d}"
            local_path = out_dir / f"{rec_id}.jpg"
            url = build_url(prompt, seed, width, height)
            records.append(
                PhotoRecord(
                    id=rec_id,
                    declared_category=category,
                    declared_activity=label,
                    actual_prompt=prompt,
                    ground_truth_category=category,
                    is_mismatch_test=False,
                    local_path=str(local_path),
                    pollinations_seed=seed,
                    pollinations_url=url,
                    width=width,
                    height=height,
                )
            )
            seed += 1
    return records


def generate_mismatch_set(
    out_dir: Path, *, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT, seed_base: int = 2000
) -> list[PhotoRecord]:
    records: list[PhotoRecord] = []
    seed = seed_base
    for i, spec in enumerate(MISMATCH_SET):
        prompt = f"{spec['actual_prompt_activity']}, {PROMPT_SUFFIX}"
        rec_id = f"mismatch_{i + 1:02d}"
        local_path = out_dir / f"{rec_id}.jpg"
        url = build_url(prompt, seed, width, height)
        records.append(
            PhotoRecord(
                id=rec_id,
                declared_category=spec["declared_category"],
                declared_activity=spec["declared_activity"],
                actual_prompt=prompt,
                ground_truth_category=spec["ground_truth_category"],
                is_mismatch_test=True,
                local_path=str(local_path),
                pollinations_seed=seed,
                pollinations_url=url,
                width=width,
                height=height,
            )
        )
        seed += 1
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out-dir", default="scripts/generated_photos")
    parser.add_argument(
        "--sanity-only",
        action="store_true",
        help="generate only one image per category (~9 images) for manual QA before mass-generating",
    )
    parser.add_argument("--skip-mismatch", action="store_true", help="skip the deliberately-mismatched set")
    parser.add_argument("--manifest-name", default="manifest.json")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    good = generate_good_set(out_dir)
    if args.sanity_only:
        good = [r for r in good if r.id.endswith("_01")]  # one per category
    mismatches = [] if (args.skip_mismatch or args.sanity_only) else generate_mismatch_set(out_dir)

    all_records = good + mismatches
    print(f"Generating {len(all_records)} image(s) into {out_dir} ...", file=sys.stderr)
    succeeded: list[PhotoRecord] = []
    failed: list[tuple[PhotoRecord, str]] = []
    for rec in all_records:
        dest = Path(rec.local_path)
        if dest.exists():
            print(f"  [{rec.id}] already downloaded, skipping -> {dest.name}", file=sys.stderr)
            succeeded.append(rec)
            continue
        print(f"  [{rec.id}] {rec.actual_prompt!r} -> {dest.name}", file=sys.stderr)
        try:
            download_image(rec.pollinations_url, dest)
            succeeded.append(rec)
        except Exception as exc:  # noqa: BLE001 -- Pollinations is a free/flaky endpoint;
            # one bad image must not lose an otherwise-successful batch. Failures are
            # reported and excluded from the manifest rather than silently guessed at
            # or left referencing a file that doesn't exist.
            print(f"  [{rec.id}] FAILED: {exc}", file=sys.stderr)
            failed.append((rec, str(exc)))
        time.sleep(POLITE_DELAY_S)

    manifest_path = out_dir / args.manifest_name
    manifest_path.write_text(json.dumps([asdict(r) for r in succeeded], indent=2))
    print(
        f"Wrote manifest: {manifest_path} ({len(succeeded)} record(s); {len(failed)} failed)",
        file=sys.stderr,
    )
    if failed:
        print("Failed records (re-run the script to retry -- already-downloaded images are skipped):", file=sys.stderr)
        for rec, reason in failed:
            print(f"  - {rec.id}: {reason}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
