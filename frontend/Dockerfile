# Frontend Dockerfile - Multi-stage build
FROM node:20-alpine as build

WORKDIR /app

# Build arguments for environment variables
ARG VITE_WS_URL=ws://localhost:8000/ws
ARG VITE_API_URL=http://localhost:8000

# Set environment variables for Vite build
ENV VITE_WS_URL=$VITE_WS_URL
ENV VITE_API_URL=$VITE_API_URL

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the app (environment variables will be embedded)
RUN npm run build

# Production stage - serve with nginx
FROM nginx:alpine

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

