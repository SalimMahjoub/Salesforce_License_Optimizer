# Multi-stage build for React + Vite frontend
FROM node:20-alpine AS builder
WORKDIR /app

# VITE_* env vars are baked into the bundle at build time
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

COPY package.json package-lock.json* ./
RUN npm ci || npm install

COPY . .
RUN npm run build

# --- Runtime ---
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]

