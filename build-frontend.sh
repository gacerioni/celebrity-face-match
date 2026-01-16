#!/bin/bash

# Build and push frontend image only
# Usage: ./build-frontend.sh [version] [ws_url] [api_url]

set -e

DOCKER_USERNAME="gacerioni"
VERSION="${1:-latest}"
WS_URL="${2:-ws://localhost:8000/ws}"
API_URL="${3:-http://localhost:8000}"
IMAGE="${DOCKER_USERNAME}/celebrity-face-match-frontend"

echo "🔨 Building Frontend Image"
echo "==========================="
echo "Image: ${IMAGE}:${VERSION}"
echo "Platforms: linux/amd64, linux/arm64"
echo "WebSocket URL: ${WS_URL}"
echo "API URL: ${API_URL}"
echo ""

# Ensure buildx builder exists
if ! docker buildx ls | grep -q "multiarch-builder"; then
    docker buildx create --name multiarch-builder --use
    docker buildx inspect --bootstrap
else
    docker buildx use multiarch-builder
fi

# Build and push
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -f frontend/Dockerfile \
    --build-arg VITE_WS_URL="${WS_URL}" \
    --build-arg VITE_API_URL="${API_URL}" \
    -t ${IMAGE}:${VERSION} \
    -t ${IMAGE}:latest \
    --push \
    frontend/

echo ""
echo "✅ Frontend image pushed: ${IMAGE}:${VERSION}"
echo ""
echo "Configuration:"
echo "  WebSocket: ${WS_URL}"
echo "  API: ${API_URL}"
echo ""

