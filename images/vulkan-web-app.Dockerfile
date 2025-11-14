# Python image: Build the OpenAPI spec
ARG PYTHON_VERSION="3.12"
FROM python:${PYTHON_VERSION} AS python-package

# Build arguments for PyPI package installation
ARG USE_PYPI=false
ARG VULKAN_VERSION
ARG VULKAN_ENGINE_VERSION

RUN pip install uv

# Copy local files (always needed for dev builds and vulkan-server which is not on PyPI)
# Copy root pyproject.toml to provide workspace context for vulkan-server (which is a workspace member)
COPY vulkan /workspace/vulkan
COPY vulkan-engine /workspace/vulkan-engine
COPY vulkan-server /workspace/vulkan-server
COPY scripts /workspace/scripts

# Conditional installation: Use PyPI packages for production builds, local copy for development
WORKDIR /workspace
RUN if [ "$USE_PYPI" = "true" ]; then \
      echo "Installing vulkanlabs-vulkan and vulkanlabs-vulkan-engine from PyPI (production build)..."; \
      uv pip install --system --no-cache \
        "vulkanlabs-vulkan==${VULKAN_VERSION}" \
        "vulkanlabs-vulkan-engine==${VULKAN_ENGINE_VERSION}" && \
      rm -rf /workspace/vulkan /workspace/vulkan-engine && \
      echo "Installing vulkan-server from local copy..."; \
      uv pip install --system --no-cache /workspace/vulkan-server; \
    else \
      echo "Using local packages (development build)..."; \
      uv pip install --system --no-cache /workspace/vulkan /workspace/vulkan-engine /workspace/vulkan-server; \
    fi

RUN TOOLING_MODE=true uv run python /workspace/scripts/export-openapi.py --out /workspace/generated/openapi.json

# OpenAPI Generator CLI: Generate TypeScript client code from OpenAPI spec
FROM openapitools/openapi-generator-cli:latest AS openapi
COPY --from=python-package /workspace/generated/openapi.json /app/openapi.json
RUN docker-entrypoint.sh generate -g typescript-fetch -i /app/openapi.json -o /app/frontend/packages/client-open/src --additional-properties="modelPropertyNaming=original"

# Node.js image: Build the Next.js application
FROM node:23-alpine AS base

FROM base AS turbo
WORKDIR /app
RUN npm install turbo --global
COPY ./frontend/ .
RUN turbo prune --docker "@vulkanlabs/app-open"

# Install dependencies
FROM base AS builder
# Check https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine to understand why libc6-compat might be needed.
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY --from=turbo /app/out/json/ .
RUN npm install

COPY --from=turbo /app/out/full/ .
COPY --from=openapi /app/frontend/packages/client-open/src ./packages/client-open/src
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ARG NEXT_PUBLIC_VULKAN_SERVER_URL
ENV NEXT_PUBLIC_VULKAN_SERVER_URL=${NEXT_PUBLIC_VULKAN_SERVER_URL}

ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs
# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder --chown=nextjs:nodejs /app/apps/open/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/open/.next/static ./apps/open/.next/static
COPY --from=builder --chown=nextjs:nodejs /app/apps/open/public ./apps/open/public

USER nextjs

EXPOSE 3000
ENV PORT=3000

# server.js is created by next build from the standalone output
# https://nextjs.org/docs/pages/api-reference/next-config-js/output
ENV HOSTNAME="0.0.0.0"
CMD ["node", "apps/open/server.js"]