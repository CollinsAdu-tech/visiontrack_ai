# VisionTrack AI -- frontend image
#
# Stage 1: build the static Vite bundle.
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: serve it with nginx, proxying API calls to the backend
# service so the SPA can keep using relative paths (/detect/image etc)
# in production exactly as it does against Vite's dev proxy.
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
