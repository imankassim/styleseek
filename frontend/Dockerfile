# Stage 15 (architecture §20 "containers"). Multi-stage build following Next.js's own
# documented Docker recipe (https://nextjs.org/docs/app/getting-started/deploying#docker),
# using next.config.ts's `output: "standalone"` for a minimal runtime image.
#
# Build from the repo root so this can COPY only the frontend/ subtree:
#   docker build -f frontend/Dockerfile -t styleseek-frontend .
# Run:
#   docker run -p 3000:3000 -e NEXT_PUBLIC_API_BASE_URL=https://api.example.com styleseek-frontend
#
# NEXT_PUBLIC_* variables are baked in at build time (Next.js convention, not a runtime
# override) -- pass --build-arg API_BASE_URL=... if the deployed backend URL differs from the
# default, rather than -e at `docker run`.

FROM node:22-slim AS deps
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

FROM node:22-slim AS builder
WORKDIR /app
ARG API_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE_URL=${API_BASE_URL}
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ .
RUN npm run build

FROM node:22-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
ENV PORT=3000
CMD ["node", "server.js"]
