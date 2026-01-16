#!/bin/bash

# Build and push backend image only
# Usage: ./build-backend.sh [version]

set -e

DOCKER_USERNAME="gacerioni"
VERSION="${1:-latest}"
IMAGE="${DOCKER_USERNAME}/celebrity-face-match-backend"

echo "🔨 Building Backend Image"
echo "=========================="
echo "Image: ${IMAGE}:${VERSION}"
echo "Platforms: linux/amd64, linux/arm64"
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
    -f backend/Dockerfile \
    -t ${IMAGE}:${VERSION} \
    -t ${IMAGE}:latest \
    --push \
    .

echo ""
echo "✅ Backend image pushed: ${IMAGE}:${VERSION}"
echo ""

