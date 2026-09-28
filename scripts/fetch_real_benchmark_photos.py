#!/usr/bin/env python3
"""
R5 — real-photo classifier benchmark: source + download real, CC-licensed
photos from Wikimedia Commons for PRD §15.1's 9 activity categories, so the
classifier can be scored against ground truth that isn't the AI-generated
synthetic set (see docs/REAL_DATA_PLAN.md §2 item 9, §8 R5 row).

Not a scraper/crawler: CURATED_PHOTOS below is a fixed, hand-reviewed list of
~45 individual files picked by browsing a handful of Commons categories
("Category:Check dams in India", "Category:Ponds in India", "Category:Levees
in India", "Category:Agricultural terraces in Kerala", "Category:Reforestation
in India", "Category:Goats in Assam", "Category:Sericulture in India",
"Category:Fish farming in India", "Category:Irrigation canals in India", plus
three off-topic distractors) — filtered by hand to drop diagrams/illustrations
and files that were miscategorized (a named reservoir dam under "Check dams",
tourism photos under "Levees", etc.). Running this script again re-downloads
the same fixed list; it does not crawl further pages or additional
categories. This satisfies the "no bulk scraping" rule in
docs/REAL_DATA_PLAN.md while still pulling individual files from Commons,
which the plan explicitly allows.

Per-file licence varies on Commons (CC BY 2.0/3.0/4.0, CC BY-SA, CC0, even
Public Domain) — never assumed uniform. This script fetches imageinfo's
extmetadata for every file and records author + exact licence string in
manifest.json; nothing here hardcodes a licence.

Precompute-first (CLAUDE.md non-negotiable): images are downloaded once and
persisted under scripts/real_photos/<CODE>/ — the live API/frontend must
never fetch these from commons.wikimedia.org at request time. Re-run this
script manually to refresh; it's idempotent (skips files already on disk).

Usage: python scripts/fetch_real_benchmark_photos.py
"""
from __future__ import annotations

import json
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import requests

API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = (
    "SakshyaSIH2026ResearchBot/1.0 "
    "(non-commercial SIH-2026 hackathon research project; watershed-photo classifier benchmark)"
)
OUT_DIR = Path(__file__).resolve().parent / "real_photos"
MANIFEST_PATH = OUT_DIR / "manifest.json"
THUMB_WIDTH = 1024  # downsized, not the (often multi-MB) original — this is a benchmark set, not an archive

# (Commons file title incl. "File:" prefix, ground-truth PRD §15.1 category or "NONE")
CURATED_PHOTOS: list[tuple[str, str]] = [
    # --- SM: Structural measures (check dam, boulder structures, CPT) ---
    ("File:Cement check dam at Kokale.jpg", "SM"),
    ("File:Cement dam on kokale odha1.jpg", "SM"),
    ("File:Check dam @ shevaroy foot hills.jpg", "SM"),
    ("File:Check Dam On Ooka Chettu Vaagu at Peddamungalachedu Village.jpg", "SM"),
    ("File:Checkdam across Bharathapuzha.jpg", "SM"),
    ("File:IMG-20180131-WA0004.jpg", "SM"),
    ("File:Kelkuchh.jpg", "SM"),
    ("File:Pond check dam overflow during raining season.jpg", "SM"),
    ("File:Vagamon chek dam.JPG", "SM"),
    ("File:Mungeshpur Drain, Delhi.jpg", "SM"),  # "under construction dam"
    # --- PT: Pond-Tanks (farm pond, percolation tank, recharge pit) ---
    ("File:A pond in a village (India, 2013).jpg", "PT"),
    ("File:Beautiful pond built for Water storage.jpg", "PT"),
    ("File:Bongal Pukhuri.JPG", "PT"),
    ("File:Draught pond.jpg", "PT"),
    ("File:Pond in Udaipur town of Gomati District of Tripura.jpg", "PT"),
    ("File:Senchowa Pukhuri, historical pond near Khowang, Dibrugarh 03.jpg", "PT"),
    # --- BN: Bunds — Baitarani river embankment ("Bandha") restoration series, Odisha ---
    ("File:Baitarani Bandha Restoration work underway - panoramio (1).jpg", "BN"),
    ("File:Big amount of Restoration work - panoramio.jpg", "BN"),
    ("File:Faudari Matha area - panoramio.jpg", "BN"),
    ("File:Jajpur, Odisha, India - panoramio (2).jpg", "BN"),
    ("File:These Guys restorinbg the broken Baitrani Embarkment near Patapur-Banapur line - panoramio.jpg", "BN"),
    # --- AM: Agronomic measures (bench terracing, contour bund, agro-forestry) ---
    ("File:Attapady-hills.jpg", "AM"),
    ("File:Attappadi.jpg", "AM"),
    ("File:Chooralmala Road (8).jpg", "AM"),
    ("File:Kanthalloor landscape 02.JPG", "AM"),
    ("File:Terrace farming-scene from KALIKAVU, WANDOOR (2094228200).jpg", "AM"),
    # --- VM: Vegetative measures (block plantation, grass turfing, farm forestry) ---
    ("File:Acacia sadhana.JPG", "VM"),
    ("File:Children planting in Chalakudy River bank.JPG", "VM"),
    ("File:Tree Plantation Drive by Maharashtra Forest Department.jpg", "VM"),
    # --- LS: Livestock (animal health camp, shelter for cattle) ---
    ("File:A goat shed in a village of Assam.jpg", "LS"),
    ("File:A goat shed in a village of Assam-2.jpg", "LS"),
    ("File:Cattle rearing near Kedarnath.jpg", "LS"),
    # --- LH: Livelihood (horticulture, sericulture, fisheries, weaving/handloom) ---
    ("File:Cleaning silkworms.jpg", "LH"),
    ("File:Handloom Weaving.jpg", "LH"),
    ("File:Fish farm 1.JPG", "LH"),
    ("File:Fish farm 2.JPG", "LH"),
    ("File:ചെമ്മീൻ കെട്ട്.jpg", "LH"),  # shrimp-farming enclosure bund, Kochi backwaters
    # --- NC: Nala-Channels — small field/village-scale channels only (large
    # engineered canals like Bhakra/Sardar Sarovar/Narayanpur excluded, a
    # different scale from a watershed-programme nala/channel work) ---
    ("File:Canaldoddaghatta.jpg", "NC"),
    ("File:Dhamanagar, Odisha 756117, India - panoramio (1).jpg", "NC"),
    ("File:Water pathway in farm.jpg", "NC"),
    ("File:Mudachikkadu11.JPG", "NC"),
    ("File:Udaipur (distrito) 2002 19.jpg", "NC"),
    # --- NONE: deliberate distractors — real photos showing none of the 9 ---
    ("File:Dried Apricots for Sale in a Market, Leh, Ladakh 01.jpg", "NONE"),
    ("File:Bus in Assam Guwahati IMG 3859.jpg", "NONE"),
    ("File:ISBT Guwahati.jpg", "NONE"),
]

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(s: str | None) -> str | None:
    if not s:
        return s
    return _HTML_TAG_RE.sub("", s).strip() or None


def safe_slug(title: str, max_len: int = 60) -> str:
    """ASCII-safe filename stem from a Commons title (several titles are in
    Malayalam/Assamese/Odia script) — the manifest keeps the real title;
    this is only for the local filesystem path."""
    name = title.removeprefix("File:")
    name = Path(name).stem
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    ascii_name = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_name).strip("-").lower()
    return (ascii_name or "photo")[:max_len]


def api_get(session: requests.Session, params: dict) -> dict:
    params = {**params, "format": "json"}
    for attempt in range(6):
        resp = session.get(API, params=params, timeout=30)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", "5"))
            print(f"  rate-limited, sleeping {wait + 1}s", file=sys.stderr)
            time.sleep(wait + 1)
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError("too many 429 responses from Commons API")


def fetch_imageinfo(session: requests.Session, titles: list[str]) -> dict[str, dict]:
    """One batched query per <=50 titles (MediaWiki's non-bot limit)."""
    out: dict[str, dict] = {}
    for i in range(0, len(titles), 50):
        batch = titles[i : i + 50]
        data = api_get(
            session,
            {
                "action": "query",
                "titles": "|".join(batch),
                "prop": "imageinfo",
                "iiprop": "url|extmetadata|size|mime",
                "iiurlwidth": THUMB_WIDTH,
            },
        )
        pages = data.get("query", {}).get("pages", {})
        for _, page in pages.items():
            title = page.get("title")
            infos = page.get("imageinfo")
            if title and infos:
                out[title] = infos[0]
        time.sleep(1.2)
    return out


def download_file(session: requests.Session, url: str, dest: Path) -> int:
    if dest.exists() and dest.stat().st_size > 0:
        return dest.stat().st_size
    for attempt in range(6):
        resp = session.get(url, timeout=60)
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", "5"))
            print(f"  rate-limited on download, sleeping {wait + 1}s", file=sys.stderr)
            time.sleep(wait + 1)
            continue
        resp.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(resp.content)
        return len(resp.content)
    raise RuntimeError(f"too many 429 responses downloading {url}")


def main() -> None:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    titles = [t for t, _ in CURATED_PHOTOS]
    print(f"Fetching imageinfo for {len(titles)} curated files...", file=sys.stderr)
    infomap = fetch_imageinfo(session, titles)

    manifest: list[dict] = []
    missing: list[str] = []
    for idx, (title, code) in enumerate(CURATED_PHOTOS, start=1):
        info = infomap.get(title)
        if not info:
            print(f"  MISSING from Commons response: {title}", file=sys.stderr)
            missing.append(title)
            continue

        thumb_url = info.get("thumburl") or info["url"]
        ext = Path(urlsplit(thumb_url).path).suffix or ".jpg"
        slug = safe_slug(title)
        local_name = f"{code.lower()}_{idx:02d}_{slug}{ext}"
        local_path = OUT_DIR / code / local_name

        try:
            size_bytes = download_file(session, thumb_url, local_path)
        except requests.RequestException as exc:
            print(f"  DOWNLOAD FAILED for {title}: {exc}", file=sys.stderr)
            missing.append(title)
            continue

        meta = info.get("extmetadata", {})
        manifest.append(
            {
                "id": f"real_{idx:03d}",
                "ground_truth_category": code,
                "commons_title": title,
                "file_page_url": info.get("descriptionurl"),
                "image_url": thumb_url,
                "local_path": str(local_path.relative_to(OUT_DIR.parent.parent)),
                "author": strip_html(meta.get("Artist", {}).get("value")),
                "license_short": meta.get("LicenseShortName", {}).get("value"),
                "license_url": meta.get("LicenseUrl", {}).get("value"),
                "credit": strip_html(meta.get("Credit", {}).get("value")),
                "description": strip_html(meta.get("ImageDescription", {}).get("value")),
                "width": info.get("width"),
                "height": info.get("height"),
                "downloaded_bytes": size_bytes,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "source": "Wikimedia Commons",
            }
        )
        print(f"  [{idx}/{len(CURATED_PHOTOS)}] {code:5s} {local_name} ({size_bytes} bytes)", file=sys.stderr)
        # upload.wikimedia.org (the image CDN, separate from the api.php
        # endpoint) applies its own burst limit that returns a long
        # Retry-After (observed: 600s) once tripped -- paced conservatively
        # here since a fresh 10-minute ban per retrigger is far more costly
        # than a few extra seconds per file for a one-time ~45-file fetch.
        time.sleep(3.0)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"\nWrote {len(manifest)} entries to {MANIFEST_PATH}", file=sys.stderr)
    if missing:
        print(f"WARNING: {len(missing)} file(s) could not be fetched/downloaded: {missing}", file=sys.stderr)


if __name__ == "__main__":
    main()
