# Python image: Build the OpenAPI spec
ARG PYTHON_VERSION="3.12"
FROM python:${PYTHON_VERSION} AS python-package

RUN pip install uv
WORKDIR /app
COPY vulkan vulkan
COPY vulkan-server vulkan-server/
COPY scripts scripts
RUN uv pip install --system --no-cache vulkan-server/
RUN uv run python scripts/export-openapi.py --out generated/openapi.json

# OpenAPI Generator CLI: Generate TypeScript client code from OpenAPI spec
FROM openapitools/openapi-generator-cli:latest AS openapi
COPY --from=python-package /app/generated/openapi.json /app/openapi.json
RUN docker-entrypoint.sh generate -g typescript-fetch -i /app/openapi.json -o /app/frontend --additional-properties="modelPropertyNaming=original"

# Node.js image: Build the Next.js application
FROM node:23-alpine AS base

# Install dependencies only when needed
FROM base AS deps
# Check https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine to understand why libc6-compat might be needed.
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Install dependencies based on the preferred package manager
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY ./frontend/ .
COPY --from=openapi /app/frontend ./generated

ARG NEXT_PUBLIC_VULKAN_SERVER_URL
ENV NEXT_PUBLIC_VULKAN_SERVER_URL=${NEXT_PUBLIC_VULKAN_SERVER_URL}

# Next.js collects completely anonymous telemetry data about general usage.
# Learn more here: https://nextjs.org/telemetry
# Uncomment the following line in case you want to disable telemetry during the build.
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ARG NEXT_PUBLIC_VULKAN_SERVER_URL
ENV NEXT_PUBLIC_VULKAN_SERVER_URL=${NEXT_PUBLIC_VULKAN_SERVER_URL}

ENV NODE_ENV=production
# Uncomment the following line in case you want to disable telemetry during runtime.
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000

# server.js is created by next build from the standalone output
# https://nextjs.org/docs/pages/api-reference/next-config-js/output
ENV HOSTNAME="0.0.0.0"
CMD ["node", "server.js"]