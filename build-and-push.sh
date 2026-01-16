#!/bin/bash

# Build and push multi-architecture Docker images to DockerHub
# Supports: linux/amd64, linux/arm64

set -e

# Configuration
DOCKER_USERNAME="gacerioni"
VERSION="${1:-latest}"  # Default to 'latest' if no version specified

BACKEND_IMAGE="${DOCKER_USERNAME}/celebrity-face-match-backend"
FRONTEND_IMAGE="${DOCKER_USERNAME}/celebrity-face-match-frontend"

echo "=========================================="
echo "🐳 Celebrity Face Match - Docker Build"
echo "=========================================="
echo ""
echo "Docker Username: ${DOCKER_USERNAME}"
echo "Version: ${VERSION}"
echo ""
echo "Images to build:"
echo "  - ${BACKEND_IMAGE}:${VERSION}"
echo "  - ${FRONTEND_IMAGE}:${VERSION}"
echo ""

# Check if logged in to Docker Hub
if ! cat ~/.docker/config.json 2>/dev/null | grep -q "auths"; then
    echo "⚠️  Not logged in to Docker Hub"
    echo "Please run: docker login"
    exit 1
fi

echo "✅ Logged in to Docker Hub"
echo ""

# Create buildx builder if it doesn't exist
if ! docker buildx ls | grep -q "multiarch-builder"; then
    echo "Creating buildx builder..."
    docker buildx create --name multiarch-builder --use
    docker buildx inspect --bootstrap
else
    echo "Using existing buildx builder..."
    docker buildx use multiarch-builder
fi

echo ""
echo "=========================================="
echo "🔨 Building Backend Image"
echo "=========================================="
echo ""

# Build and push backend
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -f backend/Dockerfile \
    -t ${BACKEND_IMAGE}:${VERSION} \
    -t ${BACKEND_IMAGE}:latest \
    --push \
    .

echo ""
echo "✅ Backend image pushed successfully!"
echo ""

echo "=========================================="
echo "🔨 Building Frontend Image"
echo "=========================================="
echo ""

# Build and push frontend
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -f frontend/Dockerfile \
    -t ${FRONTEND_IMAGE}:${VERSION} \
    -t ${FRONTEND_IMAGE}:latest \
    --push \
    frontend/

echo ""
echo "✅ Frontend image pushed successfully!"
echo ""

echo "=========================================="
echo "🎉 Build Complete!"
echo "=========================================="
echo ""
echo "Images published:"
echo "  📦 ${BACKEND_IMAGE}:${VERSION}"
echo "  📦 ${BACKEND_IMAGE}:latest"
echo "  📦 ${FRONTEND_IMAGE}:${VERSION}"
echo "  📦 ${FRONTEND_IMAGE}:latest"
echo ""
echo "Platforms: linux/amd64, linux/arm64"
echo ""
echo "To deploy:"
echo "  1. Set REDIS_URI environment variable"
echo "  2. Run: docker-compose -f docker-compose.prod.yml up -d"
echo ""

