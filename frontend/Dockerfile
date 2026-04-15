# Stage 1: build
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# VITE_API_URL is injected at build time
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Stage 2: serve with nginx
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# nginx config template: serve SPA and proxy /api to backend
# BACKEND_URL is injected at runtime via envsubst (e.g. https://xxx.up.railway.app)
COPY nginx.conf /etc/nginx/nginx.conf.template

CMD ["/bin/sh", "-c", "echo \"BACKEND_URL is: $BACKEND_URL\" && envsubst '${BACKEND_URL}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf && nginx -g 'daemon off;'"]

EXPOSE 80
