FROM node:20-alpine AS deps

WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder

ARG NEXT_PUBLIC_API_BASE=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE=${NEXT_PUBLIC_API_BASE}

WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY apps/web ./
RUN npm run build

FROM node:20-alpine AS runner

ARG NEXT_PUBLIC_API_BASE=http://localhost:8000
ENV NODE_ENV=production \
    NEXT_PUBLIC_API_BASE=${NEXT_PUBLIC_API_BASE}

WORKDIR /app
COPY --from=builder /app ./

EXPOSE 8080

CMD ["sh", "-c", "npm run start -- --hostname 0.0.0.0 --port ${PORT:-3000}"]
