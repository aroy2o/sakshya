#!/usr/bin/env bash
# One-off restore of the curated Reality Pass demo dataset — the real SLUSI
# Marigaon boundary (mws, 1 doc) and 17 real WDC-PMKSY-anchored field
# records/asset_evidence pairs (ids 1-17 in this snapshot, taken 2026-09-28
# — see PROGRESS.md's "Post-reseed reconciliation" section for the fuller
# 18-34-id state this predates; this is the snapshot actually committed to
# the repo as backup_*.jsonl, and it is internally self-consistent: real
# boundary, real work-code format, matching geo scores). The matching photo
# files ship inside the api image itself (api/app/static/photos/, baked in
# at build time) and land in the sakshya_photos named volume the first time
# the api container starts, so running this after `docker compose up -d`
# reunites all three halves (boundary + records + photos) of the dataset.
#
# backup_mws.jsonl was exported from this machine's local dev mongo
# (api/docker-compose.yml, port 27018) at deploy-setup time via
# `mongoexport --db sakshya --collection mws`, same way the other two
# backup_*.jsonl files already in the repo were produced.
#
# Deliberately NOT run automatically on every boot (not part of
# docker-compose.yml) — this only makes sense once, against an empty
# database. Re-running it against a server that already has its own live
# data would duplicate _id's mongoimport can't silently overwrite.
set -euo pipefail
cd "$(dirname "$0")/.."

docker compose up -d mongo api
docker compose exec -T mongo mongosh --quiet --eval "db.adminCommand('ping')" >/dev/null

docker compose cp backup_mws.jsonl mongo:/tmp/mws.jsonl
docker compose cp backup_field_record.jsonl mongo:/tmp/field_record.jsonl
docker compose cp backup_asset_evidence.jsonl mongo:/tmp/asset_evidence.jsonl

docker compose exec -T mongo mongoimport --db sakshya --collection mws --file /tmp/mws.jsonl
docker compose exec -T mongo mongoimport --db sakshya --collection field_record --file /tmp/field_record.jsonl
docker compose exec -T mongo mongoimport --db sakshya --collection asset_evidence --file /tmp/asset_evidence.jsonl

# field_record.photo1_url was stored as a full absolute URL at the time each
# record was originally POSTed (api/app/services/photo_service.py builds it
# from PHOTO_PUBLIC_BASE_URL at *write* time, not read time) — so every row
# in the snapshot still says http://localhost:8000/static/photos/..., the
# value this repo's local dev API had configured when it was exported. Point
# it at whatever this deploy's actual PHOTO_PUBLIC_BASE_URL is now, or the
# photos in every asset drawer 404 despite the files being present.
NEW_PHOTO_BASE=$(docker compose exec -T api printenv PHOTO_PUBLIC_BASE_URL | tr -d '\r')
docker compose exec -T mongo mongosh --quiet sakshya --eval "
  db.field_record.updateMany(
    { photo1_url: { \$regex: '^http://localhost:8000/static/photos/' } },
    [ { \$set: { photo1_url: { \$replaceOne: {
          input: '\$photo1_url',
          find: 'http://localhost:8000/static/photos',
          replacement: '${NEW_PHOTO_BASE}' } } } } ]
  )
"

echo "Restored mws + field_record + asset_evidence into the mongo container's sakshya database, photo1_url rewritten to ${NEW_PHOTO_BASE}."
