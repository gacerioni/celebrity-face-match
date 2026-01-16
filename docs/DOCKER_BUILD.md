# 🐳 Docker Build Guide

Build multi-architecture Docker images for Celebrity Face Match.

---

## Prerequisites

1. **Docker Desktop** or **Docker Engine** (19.03+)
2. **Docker Buildx** (included in Docker Desktop)
3. **Docker Hub account** (logged in: `docker login`)

---

## Quick Build

### Build Both Images

```bash
# Build and push both backend and frontend
./build-and-push.sh
```

### Build Backend Only

```bash
./build-backend.sh
```

### Build Frontend Only

```bash
# For local development (localhost)
./build-frontend.sh

# For production (with custom URLs)
./build-frontend.sh latest \
  "wss://yourdomain.com/api/ws" \
  "https://yourdomain.com/api"
```

---

## Manual Build

### Backend

```bash
# Create buildx builder (first time only)
docker buildx create --name multiarch-builder --use
docker buildx inspect --bootstrap

# Build and push
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f backend/Dockerfile \
  -t gacerioni/celebrity-face-match-backend:latest \
  --push \
  .
```

### Frontend

```bash
# Build with environment variables
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f frontend/Dockerfile \
  --build-arg VITE_WS_URL="wss://yourdomain.com/api/ws" \
  --build-arg VITE_API_URL="https://yourdomain.com/api" \
  -t gacerioni/celebrity-face-match-frontend:latest \
  --push \
  frontend/
```

---

## Environment Variables

### Backend (Runtime)

Set via Docker Compose or environment:

```bash
REDIS_URI=redis://username:password@host:port/db
REDIS_INDEX_NAME=celeb_faces_idx
REDIS_KEY_PREFIX=celeb
```

### Frontend (Build-time)

**Important:** Frontend URLs are baked into the build!

```bash
# For local development
VITE_WS_URL=ws://localhost:8000/ws
VITE_API_URL=http://localhost:8000

# For production with nginx
VITE_WS_URL=wss://yourdomain.com/api/ws
VITE_API_URL=https://yourdomain.com/api

# For production without nginx (direct access)
VITE_WS_URL=ws://yourdomain.com:8080/ws
VITE_API_URL=http://yourdomain.com:8080
```

**Note:** Use `wss://` for HTTPS, `ws://` for HTTP

---

## Multi-Architecture Support

Images support both:
- `linux/amd64` (Intel/AMD processors)
- `linux/arm64` (Apple Silicon, AWS Graviton)

This allows deployment on:
- AWS EC2 (x86 or ARM)
- Apple Silicon Macs
- Raspberry Pi
- Any ARM-based cloud instances

---

## Image Tags

```bash
# Latest (default)
gacerioni/celebrity-face-match-backend:latest
gacerioni/celebrity-face-match-frontend:latest

# Specific version
gacerioni/celebrity-face-match-backend:v1.0.0
gacerioni/celebrity-face-match-frontend:v1.0.0
```

---

## Local Testing

### Test Backend

```bash
docker run -p 8000:8000 \
  -e REDIS_URI="redis://localhost:6379" \
  gacerioni/celebrity-face-match-backend:latest
```

### Test Frontend

```bash
docker run -p 3000:80 \
  gacerioni/celebrity-face-match-frontend:latest
```

### Test with Docker Compose

```bash
# Local development
docker compose up

# Production
docker compose -f docker-compose.prod.yml up
```

---

## Troubleshooting

### Buildx not found

```bash
# Install buildx
docker buildx install

# Or use Docker Desktop (includes buildx)
```

### Multi-platform build fails

```bash
# Remove and recreate builder
docker buildx rm multiarch-builder
docker buildx create --name multiarch-builder --use
docker buildx inspect --bootstrap
```

### Push permission denied

```bash
# Login to Docker Hub
docker login

# Verify username matches in scripts
# Update DOCKER_USERNAME in build scripts if needed
```

### Frontend URLs wrong

Frontend URLs are set at **build time**, not runtime!

To change URLs, you must **rebuild** the frontend:

```bash
./build-frontend.sh latest \
  "wss://new-domain.com/api/ws" \
  "https://new-domain.com/api"
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Push

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Build and push
        run: ./build-and-push.sh
```

---

## Image Sizes

- **Backend:** ~1.2GB (includes face_recognition, OpenCV, dlib)
- **Frontend:** ~50MB (nginx + static files)

---

For deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md)

