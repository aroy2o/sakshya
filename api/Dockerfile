# SAKSHYA API image.
#
# Build context is the REPO ROOT, not /api — app/config.py resolves
# scripts/output, scripts/output/registry and scripts/real_photos via paths
# relative to the process's own cwd (GEOSPATIAL_OUTPUT_DIR=../scripts/output
# etc., see api/.env.example). This Dockerfile reproduces that same
# api/ + scripts/ sibling layout inside the image so none of those relative
# defaults need to change for the container to work.
#
# requests>=2.32 is a real runtime dependency (api/services/vision_providers/
# ollama_provider.py imports it unconditionally, and that import chain loads
# at app startup via app/routers/assets.py) even though production doesn't
# call Ollama yet — see api/requirements.txt.
FROM python:3.12-slim

WORKDIR /app

COPY api/requirements.txt ./api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

COPY api/ ./api/
COPY scripts/output/ ./scripts/output/
COPY scripts/real_photos/ ./scripts/real_photos/

WORKDIR /app/api

# Fresh checkout safety net: app/main.py mounts /static/photos on this dir
# and mkdir(parents=True, exist_ok=True)'s it at startup anyway, but this
# keeps the image correct even if api/app/static/photos/ ever ends up empty
# (e.g. .gitkeep-only) at build time.
RUN mkdir -p app/static/photos

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)" || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
