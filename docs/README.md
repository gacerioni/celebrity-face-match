# Documentation

---

## 📚 Essential Guides

### 1. [DATABASE_SETUP.md](./DATABASE_SETUP.md) ⭐ **START HERE**

**Build your celebrity face database from scratch:**
- Create celebrity list (JSON)
- Download & validate images
- Extract face embeddings
- Build Redis vector index

This is the core of the project. Everything else depends on this.

### 2. [DOCKER_BUILD.md](./DOCKER_BUILD.md)

**Build custom Docker images:**
- Multi-architecture builds (amd64, arm64)
- Environment variables
- Frontend URL configuration
- Push to Docker Hub

### 3. [DEVELOPMENT.md](./DEVELOPMENT.md)

**Local development setup:**
- Running locally without Docker
- Project structure
- Development workflow
- Debugging tips

---

## 🚀 Quick Start

### Build the Database

```bash
# 1. Download face detection models
python scripts/download_face_models.py

# 2. Scrape celebrity images
python prepare_database.py

# 3. Build vector index in Redis
python build_vector_db.py
```

See [DATABASE_SETUP.md](./DATABASE_SETUP.md) for details.

### Run the App

```bash
# With Docker
export REDIS_URI="redis://localhost:6379"
docker compose up -d

# Without Docker
./run.sh
```

---

## 🐳 Deployment

Use Docker Compose - that's it. How you serve it is up to you:

```yaml
# docker-compose.yml
services:
  backend:
    image: gacerioni/celebrity-face-match-backend:latest
    environment:
      - REDIS_URI=${REDIS_URI}

  frontend:
    image: gacerioni/celebrity-face-match-frontend:latest
```

Put it behind nginx, Traefik, Caddy, AWS ALB, whatever you want. Not our problem.

---

## 📖 What Each Guide Covers

### DATABASE_SETUP.md
- ✅ Celebrity list format
- ✅ Image scraping pipeline
- ✅ Face detection & validation
- ✅ Embedding extraction
- ✅ Redis vector index creation
- ✅ Adding custom faces

### DOCKER_BUILD.md
- ✅ Building backend image
- ✅ Building frontend image (with custom URLs)
- ✅ Multi-arch support
- ✅ Environment variables
- ✅ Pushing to Docker Hub

### DEVELOPMENT.md
- ✅ Local setup without Docker
- ✅ Project structure
- ✅ Running backend & frontend
- ✅ Debugging
- ✅ Common tasks

---

## 🆘 Getting Help

1. Read the relevant guide above
2. Check troubleshooting sections
3. Open an issue on GitHub

---

## 📝 Additional Resources

- [Main README](../README.md)
- [Contributing Guide](../CONTRIBUTING.md)
- [Redis Vector Search Docs](https://redis.io/docs/stack/search/reference/vectors/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

