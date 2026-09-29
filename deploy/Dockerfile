# All-in-one SAKSHYA demo image: mongod + api + nginx(web) in a SINGLE
# container, one exposed port (80). This is deliberately a different shape
# from the repo-root docker-compose.yml (3 separate containers) — that one
# stays as-is for a real multi-container cloud deploy later; this one is
# for "run it locally as one thing and look at it" per explicit instruction.
#
# mongo:7's own image is the base (already has mongod + mongosh installed
# and correctly configured /data/db permissions) with python3/nginx/
# supervisor layered on top via apt — cheaper than reconstructing mongo's
# own apt-repo setup on top of a python base image.
#
# Build from the REPO ROOT (needs api/, web/, scripts/output/,
# scripts/real_photos/ all in the build context):
#   docker build -f deploy/Dockerfile -t sakshya-allinone .
#   docker run -d -p 8080:80 --env-file .env --name sakshya sakshya-allinone
#
# supervisord (deploy/supervisord.conf) runs all three processes and
# restarts any that die; deploy/wait-for-mongo.sh keeps uvicorn from racing
# mongod on startup.

FROM node:20-alpine AS web-build
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ .
ARG VITE_API_MODE=live
ARG VITE_API_BASE_URL=/api
ARG VITE_DEMO_MWS_ID=
ENV VITE_API_MODE=$VITE_API_MODE
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_DEMO_MWS_ID=$VITE_DEMO_MWS_ID
RUN npm run build

FROM mongo:7

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-pip nginx supervisor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY api/requirements.txt ./api/requirements.txt
RUN pip3 install --no-cache-dir -r api/requirements.txt

COPY api/ ./api/
COPY scripts/output/ ./scripts/output/
COPY scripts/real_photos/ ./scripts/real_photos/
RUN mkdir -p api/app/static/photos

COPY --from=web-build /web/dist /usr/share/nginx/html

# Ubuntu's nginx package pre-enables its own default site on port 80 — must
# go, or it fights deploy/nginx.conf for the same listen directive.
RUN rm -f /etc/nginx/sites-enabled/default /etc/nginx/sites-available/default
COPY deploy/nginx.conf /etc/nginx/conf.d/sakshya.conf

COPY deploy/wait-for-mongo.sh /app/wait-for-mongo.sh
RUN chmod +x /app/wait-for-mongo.sh
COPY deploy/supervisord.conf /etc/supervisor/conf.d/sakshya.conf

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=6 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost/api/health', timeout=2)" || exit 1

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]
