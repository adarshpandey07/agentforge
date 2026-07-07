# syntax=docker/dockerfile:1
# ---------- deps: install node_modules only when lockfile changes ----------
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci || npm install

# ---------- build: compile Next.js standalone output ----------
FROM node:20-alpine AS build
WORKDIR /app
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL} \
    NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# ---------- runner: minimal non-root runtime ----------
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN addgroup -S nodejs -g 1001 && adduser -S nextjs -u 1001

# Next.js standalone output (requires `output: "standalone"` in next.config)
COPY --from=build --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=build --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=build --chown=nextjs:nodejs /app/public ./public

USER nextjs
EXPOSE 3000

CMD ["node", "server.js"]
