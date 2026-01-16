# 💻 Development Guide

Local development setup for Celebrity Face Match.

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- Redis 8+ (built-in vector search)
- Git

---

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/gacerioni/celebrity-face-match.git
cd celebrity-face-match
```

### 2. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Download face detection models
python scripts/download_face_models.py

# Start Redis 8
docker run -d -p 6379:6379 redis:8
# Or: redis-server (if installed locally)

# Prepare celebrity database (optional - can use existing)
python prepare_database.py
python build_vector_db.py
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

---

## Running Locally

### Option 1: Quick Start Script

```bash
./run.sh
```

Opens:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

### Option 2: Manual (Two Terminals)

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Option 3: Docker Compose

```bash
docker compose up
```

---

## Project Structure

```
celebrity-face-match/
├── backend/              # FastAPI backend
│   ├── main.py          # Main application
│   ├── Dockerfile       # Backend container
│   └── requirements.txt # Python dependencies
├── frontend/            # React frontend
│   ├── src/
│   │   ├── App.jsx     # Main component
│   │   └── index.css   # Styles
│   ├── Dockerfile      # Frontend container
│   └── package.json    # Node dependencies
├── modules/             # Shared Python modules
│   ├── face_detector.py
│   ├── image_downloader.py
│   └── ...
├── scripts/             # Utility scripts
├── data/               # Celebrity data
│   ├── celebrities_combined.json
│   ├── metadata/       # Celebrity metadata
│   └── custom_images/  # Downloaded images
├── docs/               # Documentation
└── config.py           # Configuration
```

---

## Key Files

### Backend

- **`backend/main.py`** - FastAPI app with WebSocket endpoint
- **`build_vector_db.py`** - Builds Redis vector database
- **`prepare_database.py`** - Downloads celebrity images
- **`config.py`** - Configuration settings

### Frontend

- **`frontend/src/App.jsx`** - Main React component
- **`frontend/src/index.css`** - TailwindCSS styles
- **`frontend/vite.config.js`** - Vite configuration

---

## Development Workflow

### 1. Make Changes

Edit files in `backend/` or `frontend/src/`

### 2. Test Locally

```bash
# Backend changes - restart server
cd backend && python main.py

# Frontend changes - hot reload automatic
cd frontend && npm run dev
```

### 3. Build Docker Images

```bash
# Backend
./build-backend.sh

# Frontend
./build-frontend.sh
```

### 4. Test with Docker

```bash
docker compose up
```

---

## Configuration

### Environment Variables

Create `.env` file:

```bash
# Redis
REDIS_URI=redis://localhost:6379
REDIS_INDEX_NAME=celeb_faces_idx

# Optional: Image search APIs
GOOGLE_API_KEY=your_key
GOOGLE_CSE_ID=your_cse_id
BING_API_KEY=your_key
```

### Frontend URLs

Edit `frontend/.env.development`:

```bash
VITE_WS_URL=ws://localhost:8000/ws
VITE_API_URL=http://localhost:8000
```

---

## Testing

### Backend Tests

```bash
# Test Redis connection
python -c "import redis; r=redis.Redis(); print(r.ping())"

# Test face detection
python search_face.py test_image.jpg

# Test API
curl http://localhost:8000/
```

### Frontend Tests

```bash
cd frontend
npm run build  # Test build
npm run preview  # Preview production build
```

---

## Common Tasks

### Add New Celebrity

```bash
# Option 1: Web UI
python register_face.py

# Option 2: Edit JSON
# Add to data/celebrities_combined.json
# Run: python prepare_database.py
# Run: python build_vector_db.py
```

### Rebuild Database

```bash
# Clear Redis
redis-cli FLUSHDB

# Rebuild
python build_vector_db.py
```

### Update Dependencies

```bash
# Backend
pip install -r requirements.txt --upgrade

# Frontend
cd frontend && npm update
```

---

## Debugging

### Enable Debug Logging

```python
# In backend/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check WebSocket Connection

Open browser console (F12) and look for:
```
WebSocket connection established
```

### Redis Debugging

```bash
# Check keys
redis-cli KEYS "celeb:*"

# Check index
redis-cli FT.INFO celeb_faces_idx

# Search test
redis-cli FT.SEARCH celeb_faces_idx "*" LIMIT 0 5
```

---

## Performance Optimization

- **Redis:** Use Redis Cloud for production
- **Images:** Optimize image sizes (max 800x800)
- **Embeddings:** Cache embeddings to avoid recomputation
- **WebSocket:** Use connection pooling for multiple clients

---

For deployment, see [DEPLOYMENT.md](./DEPLOYMENT.md)

