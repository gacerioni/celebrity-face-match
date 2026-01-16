# 📊 Building the Celebrity Face Database

This is the core of the project. Here's how to build your own face recognition database from scratch.

---

## 🎯 Overview

Building the database has 3 main steps:

1. **Create celebrity list** → JSON file with names
2. **Download & validate images** → `prepare_database.py`
3. **Build vector index** → `build_vector_db.py`

---

## Step 1: Create Your Celebrity List

Edit `data/celebrities_combined.json`:

```json
[
  {
    "name": "Fernanda Montenegro",
    "slug": "fernanda-montenegro",
    "category": "actor",
    "source": "manual"
  },
  {
    "name": "Pelé",
    "slug": "pele",
    "category": "athlete",
    "source": "manual"
  }
]
```

**Fields:**
- `name` - Full name of the celebrity
- `slug` - URL-safe identifier (lowercase, hyphens)
- `category` - actor, singer, athlete, influencer, politician, etc.
- `source` - manual, generated, scraped, etc.

**Included:** The repo includes 2,600+ Brazilian celebrities already.

---

## Step 2: Download & Validate Images

```bash
# Download face detection models (first time only)
python scripts/download_face_models.py

# Run the image scraper
python prepare_database.py
```

### What This Does

For each celebrity in your JSON:

1. **Searches for images** on:
   - Wikimedia (Portuguese & English)
   - DuckDuckGo (free, no API key needed)
   - Google/Bing (optional, requires API keys)

2. **Validates each image:**
   - Must contain exactly 1 face
   - Face must be clear and well-lit
   - Minimum 300x300 resolution
   - Face must occupy significant portion

3. **Saves results:**
   - Image → `data/custom_images/{slug}.jpg`
   - Metadata → `data/metadata/{slug}.json`

### Incremental Processing

The script is **incremental** - it skips celebrities that already have images:

```bash
# Run 1: ~60% success rate
python prepare_database.py

# Run 2: ~75% success rate (retries failures)
python prepare_database.py

# Run 3: ~85% success rate
python prepare_database.py

# Check progress anytime
python check_status.py
```

### Options

```bash
# Test with 10 celebrities first
python prepare_database.py --test 10

# Force reprocess everything
python prepare_database.py --force
```

### Example Output

```
Processing: Fernanda Montenegro
  ✓ Found image on Wikimedia
  ✓ Face detected
  ✓ Image validated
  ✓ Saved to data/custom_images/fernanda-montenegro.jpg
  ✓ Metadata saved

Processing: Pelé
  ✗ No clear face found, trying next source...
  ✓ Found image on DuckDuckGo
  ✓ Face detected
  ✓ Saved

Progress: 2/2659 (0.08%) | Success: 2 | Failed: 0
```

---

## Step 3: Build Vector Database in Redis

```bash
# Make sure Redis is running
redis-server  # or use Redis Cloud

# Build the vector index
python build_vector_db.py
```

### What This Does

1. **Loads all metadata** from `data/metadata/*.json`
2. **Reads images** from `data/custom_images/*.jpg`
3. **Extracts face embeddings:**
   - Uses dlib ResNet-34 model
   - Generates 128-dimensional vector for each face
   - Vector represents facial features (distances, shapes, etc.)
4. **Stores in Redis:**
   - Key: `celeb:{slug}`
   - Fields: name, category, image_url, embedding (128-d vector)
5. **Creates vector index:**
   - Index name: `celeb_faces_idx`
   - Algorithm: HNSW (fast approximate search)
   - Metric: Cosine similarity

### Redis Schema

```
Key: celeb:fernanda-montenegro
Hash fields:
  name: "Fernanda Montenegro"
  slug: "fernanda-montenegro"
  category: "actor"
  image_url: "data/custom_images/fernanda-montenegro.jpg"
  embedding: [0.123, -0.456, 0.789, ...] (128 floats)
```

### Vector Index

```
Index: celeb_faces_idx
Type: HASH
Fields:
  - embedding (VECTOR, HNSW, COSINE, 128 dimensions)
  - name (TEXT)
  - category (TAG)
```

---

## Step 4: Verify It Works

```bash
# Check database status
python check_status.py

# Test with a photo
python search_face.py my_photo.jpg

# Or start the web UI
./run.sh
```

---

## 🔧 Adding Custom Faces

### Option 1: Web UI (Easiest)

```bash
python register_face.py
# Opens at http://localhost:7862
```

- Upload photo or use webcam
- Enter name and category
- Face is immediately added to Redis

### Option 2: Add to JSON and Rebuild

1. Add to `data/celebrities_combined.json`
2. Run `python prepare_database.py`
3. Run `python build_vector_db.py`

### Option 3: Manual

1. Save image: `data/custom_images/person-name.jpg`
2. Create `data/metadata/person-name.json`:
```json
{
  "name": "Person Name",
  "slug": "person-name",
  "category": "custom",
  "source": "manual",
  "image_url": "data/custom_images/person-name.jpg"
}
```
3. Run `python build_vector_db.py`

---

## 📊 Understanding the Pipeline

```
celebrities_combined.json
         ↓
   prepare_database.py
         ↓
   ┌─────────────────┐
   │ Image Search    │ → Wikimedia, DuckDuckGo, etc.
   │ Face Detection  │ → OpenCV DNN
   │ Validation      │ → Quality checks
   └─────────────────┘
         ↓
   data/custom_images/*.jpg
   data/metadata/*.json
         ↓
   build_vector_db.py
         ↓
   ┌─────────────────┐
   │ Load Images     │
   │ Extract Faces   │ → dlib ResNet-34
   │ Generate Vector │ → 128-d embedding
   │ Store in Redis  │ → Hash + Vector Index
   └─────────────────┘
         ↓
   Redis Vector Database
   (Ready for search!)
```

---

## ⚙️ Configuration

Edit `config.py`:

```python
# Celebrity list
CELEBRITY_LIST = "data/celebrities_combined.json"

# Image search
FACE_DETECTION_ENABLED = True

# Redis
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_INDEX_NAME = "celeb_faces_idx"
REDIS_KEY_PREFIX = "celeb"

# Vector settings
VECTOR_DIMENSIONS = 128
SIMILARITY_METRIC = "COSINE"
```

---

## 🐛 Troubleshooting

### "No face detected"
- Image quality too low
- Multiple faces in image
- Face not clearly visible
- Try different search source

### "Redis connection failed"
- Start Redis: `redis-server` or `docker run -d -p 6379:6379 redis:8`
- Or use Redis Cloud
- Check `REDIS_URI` in config

### Low success rate (<50%)
- Run `prepare_database.py` multiple times
- Check internet connection
- Verify celebrity names are correct

### "Vector index not found"
- Run `python build_vector_db.py`
- Make sure you're using Redis 8+ (has built-in vector search)

---

## 📈 Performance

- **Image download:** ~5 seconds per celebrity
- **Face detection:** ~0.5 seconds per image
- **Embedding extraction:** ~1 second per face
- **Redis storage:** ~0.01 seconds per embedding
- **Total:** ~2,600 celebrities in ~4 hours

**Tips:**
- Run incrementally (skips processed celebrities)
- Use Redis Cloud for production
- Images are cached locally

---

## 🎯 Next Steps

After building the database:

1. **Test it:** `python search_face.py your_photo.jpg`
2. **Run the app:** `./run.sh`
3. **Deploy:** See [DOCKER_BUILD.md](./DOCKER_BUILD.md)

