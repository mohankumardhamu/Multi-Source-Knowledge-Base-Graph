# Multi-stage build for production
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files from the frontend directory
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy source code from the frontend directory
COPY frontend/ .

# Build the application
RUN npm run build

# Production stage with Nginx
FROM nginx:alpine

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
