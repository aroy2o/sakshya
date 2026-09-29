# Deployment runbook — SAKSHYA on AWS EC2 (free tier)

This is a from-scratch, no-other-context-needed walkthrough for standing up
SAKSHYA on a single AWS EC2 free-tier instance and wiring up automatic
redeploys from GitHub. If you're reading this to do the deploy, you don't
need to have been part of any prior conversation about how this was built —
everything you need is here or linked from here.

## What you're deploying

One Docker image (built from [`deploy/Dockerfile`](../deploy/Dockerfile))
that runs three processes inside a single container, supervised by
`supervisord`:

- **mongod** — the database, data on a named Docker volume
- **the FastAPI api** — Python/Uvicorn, talks to mongod on `127.0.0.1`
- **nginx** — serves the built React frontend and reverse-proxies `/api/*`
  to the api process

One exposed port (80). One `docker run` on the server. Measured resource
use while running with the demo dataset loaded: **~160 MB RAM**, image size
**~1.3 GB** — any free-tier instance handles this with room to spare.

A separate `docker-compose.yml` at the repo root also exists (mongo + api +
web as 3 containers) if a multi-container setup is ever wanted instead —
this runbook is for the single-container `deploy/` path, which is what
[`.github/workflows/ci-cd.yml`](../.github/workflows/ci-cd.yml) actually
builds and deploys.

**Known, deliberate gaps** (not bugs — decisions already made):
- The AI vision classifier (`POST /assets/{id}/classify`, backed by a local
  Ollama model) is **not wired into this deploy**. The endpoint will error
  per-request; everything else works normally. Revisit later if a real
  hosted vision provider gets chosen.
- Google Earth Engine is never called by the live api or web — it's
  offline/scripts-only by design (CLAUDE.md's precompute-first rule) — so
  nothing GEE-related needs to exist on the server at all.

---

## Part A — Launch the EC2 instance

In the AWS Console → EC2 → Launch instance:

1. **AMI**: Ubuntu Server 22.04 LTS (look for "Free tier eligible" tag)
2. **Instance type**: whatever is tagged "Free tier eligible" (t2.micro or
   t3.micro — 1 vCPU, 1 GB RAM). That's ~6x the RAM this actually uses.
3. **Key pair**: create a new one, name it something like `sakshya-deploy`,
   download the `.pem` file. You cannot download it again later — keep it.
4. **Storage**: default (8–30 GB gp3) is plenty; the image is ~1.3 GB.
5. **Network settings / security group** — this is the most common thing
   people get wrong: the default only opens port 22 (SSH). Add a second
   inbound rule:
   - Type: **HTTP**, Port: **80**, Source: **0.0.0.0/0** (anywhere)

   Without this, the container will run fine but the site will just hang
   or time out from a browser.
6. Launch it.

### Give it a stable IP (recommended)

EC2's default public IP changes if the instance is ever stopped and
restarted. To avoid that silently breaking the deploy later:

- EC2 → **Elastic IPs** → Allocate Elastic IP address
- Select it → **Actions** → **Associate Elastic IP address** → pick your
  new instance

Use this Elastic IP everywhere below (as `<SERVER_IP>`).

---

## Part B — One-time server setup

SSH in (replace with your actual key path and IP):

```bash
chmod 400 sakshya-deploy.pem
ssh -i sakshya-deploy.pem ubuntu@<SERVER_IP>
```

Once connected, run:

```bash
# Install Docker
curl -fsSL https://get.docker.com | sudo sh

# Let the ubuntu user run docker without sudo — the automated CD pipeline
# connects as this user and runs plain `docker` commands, not `sudo docker`
sudo usermod -aG docker $USER
# Log out and reconnect for this to take effect for YOU. (Not required for
# the automated pipeline — every SSH session it opens is a fresh login, so
# the group membership is already active for it the moment this command runs.)
exit
```

Reconnect (`ssh -i sakshya-deploy.pem ubuntu@<SERVER_IP>`), then create the
server's environment file. This is the **one file CD never touches** — it
stays put across every redeploy, only the image changes:

```bash
sudo mkdir -p /opt/sakshya
sudo tee /opt/sakshya/.env > /dev/null <<'EOF'
CORS_ORIGINS=http://<SERVER_IP>
PHOTO_PUBLIC_BASE_URL=http://<SERVER_IP>/api/static/photos
THEMATIC_PUBLIC_BASE_URL=http://<SERVER_IP>/api/static/geospatial
GOOGLE_APPLICATION_CREDENTIALS=
GEE_PROJECT_ID=
VISION_API_KEY=
VISION_API_PROVIDER=
EOF
```

Replace **both** occurrences of `<SERVER_IP>` with the real Elastic IP
before running this. (No `MONGO_URI` needed — `deploy/supervisord.conf`
already points the api at the mongod running in the same container,
regardless of what's in this file.)

If you get a real domain later, this is the only file that needs editing
(swap `http://<SERVER_IP>` for `https://your-domain`) — everything else
about the deploy stays the same.

---

## Part C — Wire up GitHub Actions

On `https://github.com/aroy2o/sakshya` → **Settings** → **Secrets and
variables** → **Actions** → **New repository secret**, add three:

| Secret name | Value |
|---|---|
| `DEPLOY_HOST` | the Elastic IP from Part A |
| `DEPLOY_USER` | `ubuntu` |
| `DEPLOY_SSH_KEY` | the **entire contents** of `sakshya-deploy.pem`, including the `-----BEGIN...-----` / `-----END...-----` lines |

That's the only manual GitHub setup needed. `.github/workflows/ci-cd.yml`
already exists and already knows what to do once these three exist:
- `api-tests` and `web-build` run on every push/PR (pytest + lint for the
  api, tsc + build + lint for the web) — these already run regardless of
  whether the secrets above exist.
- `deploy` runs only on pushes to `main`, and only actually does anything
  once it detects all three secrets are present. Before that, it shows as
  a green checkmark that did nothing (by design — it can't fail over
  secrets that were never expected to exist yet).

---

## Part D — Trigger the first deploy

Once the three secrets exist, either:
- Push any commit to `main`, **or**
- Go to the repo's **Actions** tab → **CI/CD** workflow → **Run workflow**
  (this uses the `workflow_dispatch` trigger — no empty commit needed)

Watch it run: `api-tests` → `web-build` → `deploy`. The `deploy` job:
1. Builds `deploy/Dockerfile` and pushes it to `ghcr.io/aroy2o/sakshya`
2. SSHes into the server, logs the server into `ghcr.io` (using the same
   short-lived token the job itself has — no extra secret, and it logs
   back out when done), pulls the new image, stops/removes any existing
   `sakshya` container, and starts a new one with:
   - `--restart unless-stopped` (survives a reboot)
   - `-v sakshya_mongo_data:/data/db` and
     `-v sakshya_photos:/app/api/app/static/photos` (both persist across
     redeploys — only `docker volume rm` would lose them, not a normal
     redeploy)
   - `--env-file /opt/sakshya/.env` (the file from Part B)

If this is the very first run, expect it to take a few minutes (Docker
build + image push + first-time `apt`/pip layer caching on the runner).
Every run after this one is much faster (Actions caches build layers).

---

## Part E — Verify it actually worked

From your own machine (not the server):

```bash
curl -i http://<SERVER_IP>/               # expect: 200, HTML
curl -s http://<SERVER_IP>/api/health     # expect: {"status":"ok"}
curl -s http://<SERVER_IP>/api/mws        # expect: [] (empty — no data loaded yet, see Part F)
```

If `curl` hangs instead of connecting: check the security group's inbound
port-80 rule from Part A — this is the #1 cause.

On the server, you can also check all three processes directly:

```bash
docker exec sakshya supervisorctl status
# expect: mongod RUNNING, api RUNNING, nginx RUNNING

docker logs sakshya --tail 50   # combined logs of all three processes
```

---

## Part F — Load the real demo dataset

A fresh deploy has an empty database — `GET /mws` returns `[]`. This repo
carries a curated, already-real dataset (real SLUSI Marigaon boundary + 17
real WDC-PMKSY-anchored field records + their matching photos, which ship
baked into the image itself) as three files at the repo root:
`backup_mws.jsonl`, `backup_field_record.jsonl`, `backup_asset_evidence.jsonl`.

This is a **one-time step** — the data lives in the named volume from then
on and survives every future redeploy.

On the server:

```bash
git clone https://github.com/aroy2o/sakshya.git
cd sakshya

docker cp backup_mws.jsonl sakshya:/tmp/mws.jsonl
docker cp backup_field_record.jsonl sakshya:/tmp/field_record.jsonl
docker cp backup_asset_evidence.jsonl sakshya:/tmp/asset_evidence.jsonl

docker exec sakshya mongoimport --db sakshya --collection mws --file /tmp/mws.jsonl
docker exec sakshya mongoimport --db sakshya --collection field_record --file /tmp/field_record.jsonl
docker exec sakshya mongoimport --db sakshya --collection asset_evidence --file /tmp/asset_evidence.jsonl

# field_record.photo1_url was stored as a full absolute URL at the time each
# record was originally created (not recomputed on read) — it still says
# http://localhost:8000/..., wherever it happened to be created. Point it at
# this server's real PHOTO_PUBLIC_BASE_URL or every photo in the dashboard 404s.
NEW_BASE=$(docker exec sakshya printenv PHOTO_PUBLIC_BASE_URL | tr -d '\r')
docker exec sakshya mongosh --quiet sakshya --eval "
  db.field_record.updateMany(
    { photo1_url: { \$regex: '^http://localhost:8000/static/photos/' } },
    [ { \$set: { photo1_url: { \$replaceOne: {
          input: '\$photo1_url',
          find: 'http://localhost:8000/static/photos',
          replacement: '${NEW_BASE}' } } } } ]
  )
"
```

Verify:

```bash
curl -s http://<SERVER_IP>/api/mws
# expect: one mws doc, "name": "Marigaon"

curl -s http://<SERVER_IP>/api/mws/4120883730/assets
# expect: a FeatureCollection with 17 features
```

Open `http://<SERVER_IP>/` in a browser — the command-strip beat should
show real figures (≈76.5% geotagged, REAL·CITED badges), and the "Project
view" beat should show the real Marigaon boundary with 17 asset pins.

---

## Ongoing: how redeploys work from here

Nothing further to do manually. Every push to `main` (after `api-tests`
and `web-build` pass) rebuilds the image and redeploys it automatically.
The database and photos volumes are untouched by a redeploy — only the
application code changes.

If `/opt/sakshya/.env` ever needs to change (new domain, CORS change,
etc.), edit it directly on the server and restart the container once:
```bash
docker restart sakshya
```
CD never overwrites this file, so this is safe to hand-edit any time.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `curl` to the server hangs/times out | Security group missing the port-80 inbound rule | Part A, step 5 |
| `deploy` job stays "skipped" forever | One of the 3 secrets is missing/misnamed | Re-check exact names in Part C |
| SSH step fails with a host-key or connection error | Wrong `DEPLOY_HOST`, or the instance's security group doesn't allow port 22 from GitHub's runners | Confirm you can `ssh` in manually with the same IP/key first |
| `docker pull` fails with `unauthorized`/401 on the server | Should be handled automatically (the deploy step logs the server into ghcr.io using the run's own token) — if it still happens, the `packages: write` permission block in `ci-cd.yml` may have been edited/removed | Re-check `permissions:` at the top of `ci-cd.yml` |
| Every photo in the dashboard 404s after a fresh Part F restore | `PHOTO_PUBLIC_BASE_URL` in `/opt/sakshya/.env` doesn't match `<SERVER_IP>`, or the rewrite step's `NEW_BASE` came back empty | `docker exec sakshya printenv PHOTO_PUBLIC_BASE_URL` and compare against what's actually in `.env` |
| `api` never goes `RUNNING` in `supervisorctl status`, keeps restarting | mongod itself is unhealthy (rare) — `wait-for-mongo.sh` handles the normal startup race, this would mean mongod itself is failing | `docker exec sakshya cat /var/log/supervisor/*mongod*` (or `docker logs sakshya`) for the real mongod error |
| Browser console shows "Worker failed to load" on the map beat | Known, pre-existing, cosmetic — a MapLibre/Vite production-build quirk unrelated to this deploy. The map still renders correctly (boundary, pins, tiles) despite it. | No action needed |
