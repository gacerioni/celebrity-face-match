# Celebrity Face Match 🎭

> Find your celebrity lookalike using AI-powered facial recognition and Redis vector search

[![Live Demo](https://img.shields.io/badge/demo-live-success)](https://celebrity.platformengineer.io)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://hub.docker.com/u/gacerioni)
[![Redis](https://img.shields.io/badge/redis-vector%20search-red)](https://redis.io)

**🎬 [Try Live Demo](https://celebrity.platformengineer.io)** - See it in action!

---

## 🚀 Quick Start

### 1. Get Redis

You need Redis 8+ with built-in vector search:

```bash
# Option A: Redis locally
docker run -d -p 6379:6379 redis:8

# Option B: Redis Cloud (recommended for production)
# Get free instance at: https://redis.com/try-free/
```

### 2. Build the Celebrity Database

This is the core of the project - building your face database:

```bash
# Clone repo
git clone https://github.com/gacerioni/celebrity-face-match.git
cd celebrity-face-match

# Install dependencies
pip install -r requirements.txt

# Download face detection models
python scripts/download_face_models.py

# Step 1: Scrape celebrity images (run multiple times for better coverage)
python prepare_database.py
# This searches Wikimedia for celebrity photos, validates faces, saves metadata

# Step 2: Build vector database in Redis
python build_vector_db.py
# This extracts face embeddings and creates the Redis vector index

# Check progress
python check_status.py
```

**What happens:**
1. `prepare_database.py` - Downloads celebrity images, detects faces, saves to `data/`
2. `build_vector_db.py` - Extracts 128-d embeddings, stores in Redis with vector index
3. You now have a searchable face database!

### 3. Run the App

```bash
# Option A: Docker Compose (easiest)
export REDIS_URI="redis://localhost:6379"  # or your Redis Cloud URI
docker compose up -d
# Access at http://localhost:3000

# Option B: Local development
./run.sh
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

---

## 📊 Building Your Own Celebrity List

The included list has 2,600+ Brazilian celebrities. To customize:

### Edit the Celebrity List

```bash
# Edit data/celebrities_combined.json
[
  {
    "name": "Celebrity Name",
    "slug": "celebrity-name",
    "category": "actor",
    "source": "manual"
  }
]

# Then run the pipeline
python prepare_database.py
python build_vector_db.py
```

### Add Custom Faces

```bash
# Use the web UI
python register_face.py
# Opens at http://localhost:7862
# Upload photo or use webcam to add faces
```

---

## 🏗️ Architecture

```
┌─────────────┐      WebSocket      ┌──────────────┐
│   React     │ ◄─────────────────► │   FastAPI    │
│  Frontend   │                     │   Backend    │
└─────────────┘                     └──────┬───────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │   Redis 8    │
                                    │ Vector Index │
                                    └──────────────┘
```

**How it works:**
1. Webcam captures your face → Frontend
2. WebSocket sends frame → Backend
3. Backend extracts 128-d face embedding
4. Redis vector search finds similar embeddings
5. Results stream back in real-time

---

## 🐳 Docker Deployment

### Using Pre-built Images

```bash
# docker-compose.yml
version: '3.8'
services:
  backend:
    image: gacerioni/celebrity-face-match-backend:latest
    ports:
      - "8000:8000"
    environment:
      - REDIS_URI=${REDIS_URI}

  frontend:
    image: gacerioni/celebrity-face-match-frontend:latest
    ports:
      - "3000:80"
```

```bash
export REDIS_URI="redis://your-redis-uri"
docker compose up -d
```

### Building Your Own Images

```bash
# Build backend
./build-backend.sh

# Build frontend (with custom URLs)
./build-frontend.sh latest \
  "ws://localhost:8000/ws" \
  "http://localhost:8000"
```

---

## 🛠️ Configuration

```bash
# .env file
REDIS_URI=redis://localhost:6379
REDIS_INDEX_NAME=celeb_faces_idx
REDIS_KEY_PREFIX=celeb
```

---

## 📖 Documentation

- **[Database Setup Guide](./docs/DATABASE_SETUP.md)** - Detailed guide on building the celebrity database
- **[Docker Build Guide](./docs/DOCKER_BUILD.md)** - Building custom Docker images
- **[Development Guide](./docs/DEVELOPMENT.md)** - Local development setup

---

## 📊 Performance

- **Search Speed:** <100ms (Redis vector search)
- **Total Processing:** ~500ms (including face detection)
- **Database Size:** 2,600+ celebrities (customizable)
- **Embedding Dimensions:** 128-d vectors
- **Similarity Metric:** Cosine distance

---

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](./CONTRIBUTING.md) first.

---

## 📝 License

MIT License - see [LICENSE](./LICENSE) for details

---

## 👤 Author

**Gabs Cerioni**
Senior Solutions Architect @ Redis
🇧🇷 Brazil

- GitHub: [@gacerioni](https://github.com/gacerioni)
- LinkedIn: [Gabriel Cerioni](https://linkedin.com/in/gabrielcerioni)

