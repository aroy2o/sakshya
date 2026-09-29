# Multi-stage: build the Vite SPA, then serve the static output through
# nginx (see nginx.conf, which also reverse-proxies /api/* to the api
# container — this image never talks to the API directly at build time).
#
# VITE_API_BASE_URL is a *build-time* arg because Vite inlines
# import.meta.env.* into the bundle at build time, not at container start.
# Default is /api, matching nginx.conf's reverse-proxy prefix — zero
# frontend code change from the existing mock/live toggle in
# src/api/index.ts, just a different build-time value for the same env var
# documented in web/.env.example.
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

ARG VITE_API_MODE=live
ARG VITE_API_BASE_URL=/api
ARG VITE_DEMO_MWS_ID=
ENV VITE_API_MODE=$VITE_API_MODE
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_DEMO_MWS_ID=$VITE_DEMO_MWS_ID

RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
  CMD wget -q --spider http://localhost/ || exit 1
