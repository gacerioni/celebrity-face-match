#!/usr/bin/env python3
"""
FastAPI backend for Celebrity Face Match - Modern Real-time Demo
Async WebSocket-based architecture for smooth, responsive UI
"""
import asyncio
import base64
import io
import json
import os
import time
from typing import Optional, Dict, List
from contextlib import asynccontextmanager

import numpy as np
import redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
import requests

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

# Import config from parent directory
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
import config

# Global state
redis_client = None
image_cache = {}
processing_queue = None


def get_redis_client():
    """Create Redis client from environment variables or config"""
    # Check for Redis Cloud URI first (production)
    redis_uri = os.getenv('REDIS_URI')

    if redis_uri:
        print(f"🔗 Connecting to Redis Cloud...")
        return redis.from_url(redis_uri, decode_responses=False)

    # Fall back to host/port configuration (local development)
    redis_host = os.getenv('REDIS_HOST', config.REDIS_HOST)
    redis_port = int(os.getenv('REDIS_PORT', config.REDIS_PORT))
    redis_db = int(os.getenv('REDIS_DB', config.REDIS_DB))

    print(f"🔗 Connecting to Redis at {redis_host}:{redis_port}")
    return redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        decode_responses=False
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global redis_client, processing_queue

    # Startup
    print("🚀 Starting Celebrity Face Match Backend...")
    processing_queue = asyncio.Queue()
    redis_client = get_redis_client()

    # Test Redis connection
    try:
        redis_client.ping()
        print(f"✅ Connected to Redis successfully")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")

    # Start background worker
    asyncio.create_task(background_worker())
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")
    if redis_client:
        redis_client.close()


app = FastAPI(title="Celebrity Face Match API", lifespan=lifespan)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def background_worker():
    """Background worker to process face detection tasks"""
    print("🔧 Background worker started")
    while True:
        try:
            task = await processing_queue.get()
            # Process task here if needed
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Worker error: {e}")


def extract_face_embedding(image_array: np.ndarray) -> tuple[Optional[np.ndarray], Optional[tuple]]:
    """Extract face embedding and location from image array"""
    if not FACE_RECOGNITION_AVAILABLE:
        return None, None
    
    try:
        encodings = face_recognition.face_encodings(image_array)
        if len(encodings) == 0:
            return None, None
        
        face_locations = face_recognition.face_locations(image_array)
        return encodings[0], face_locations[0] if face_locations else None
    except Exception as e:
        print(f"Face extraction error: {e}")
        return None, None


def search_similar_faces(query_embedding: np.ndarray, top_k: int = 5) -> List[Dict]:
    """Search for similar faces using Redis vector similarity"""
    from redis.commands.search.query import Query
    
    query_vector = query_embedding.astype(np.float32).tobytes()
    
    query = (
        Query(f"*=>[KNN {top_k} @embedding $vec AS score]")
        .return_fields("name", "slug", "category", "source", "image_url", "score")
        .sort_by("score")
        .dialect(2)
    )
    
    results = redis_client.ft(config.REDIS_INDEX_NAME).search(
        query,
        query_params={"vec": query_vector}
    )
    
    matches = []
    for doc in results.docs:
        matches.append({
            "name": doc.name.decode() if isinstance(doc.name, bytes) else doc.name,
            "slug": doc.slug.decode() if isinstance(doc.slug, bytes) else doc.slug,
            "category": doc.category.decode() if isinstance(doc.category, bytes) else doc.category,
            "image_url": doc.image_url.decode() if isinstance(doc.image_url, bytes) else doc.image_url,
            "score": float(doc.score)
        })
    
    return matches


def download_celebrity_image(url: str) -> Optional[str]:
    """Download celebrity image and return as base64"""
    if url in image_cache:
        return image_cache[url]
    
    try:
        # Check if local file
        if url.startswith('data/') or url.startswith('./data/'):
            file_path = Path(__file__).parent.parent / url
            if file_path.exists():
                img = Image.open(file_path)
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                image_cache[url] = img_str
                return img_str
        
        # Download from URL
        headers = {"User-Agent": "CelebFaceMatch/2.0"}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()

        img = Image.open(io.BytesIO(response.content))
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        image_cache[url] = img_str
        return img_str
    except Exception as e:
        print(f"Failed to load image {url}: {e}")
        return None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Celebrity Face Match API",
        "face_recognition": FACE_RECOGNITION_AVAILABLE,
        "redis": redis_client is not None
    }


@app.get("/api/stats")
async def get_stats():
    """Get database statistics"""
    try:
        info = redis_client.ft(config.REDIS_INDEX_NAME).info()
        num_docs = info.get('num_docs', 0)
        return {
            "total_celebrities": num_docs,
            "index_name": config.REDIS_INDEX_NAME
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time face matching"""
    await websocket.accept()
    print("🔌 WebSocket client connected")

    try:
        while True:
            # Receive frame from client
            data = await websocket.receive_json()

            if data.get("type") == "frame":
                # Process frame in background to avoid blocking
                asyncio.create_task(process_frame_async(websocket, data))

    except WebSocketDisconnect:
        print("🔌 WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")


async def process_frame_async(websocket: WebSocket, data: Dict):
    """Process a single frame asynchronously"""
    try:
        start_time = time.time()

        # Decode base64 image
        image_data = data.get("image", "").split(",")[1] if "," in data.get("image", "") else data.get("image", "")
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        image_array = np.array(image)

        # Extract face embedding (this is the slow part)
        embedding, face_location = await asyncio.to_thread(extract_face_embedding, image_array)

        if embedding is None:
            await websocket.send_json({
                "type": "result",
                "status": "no_face",
                "message": "No face detected - please position your face in the frame"
            })
            return

        # Search Redis (fast!)
        search_start = time.time()
        matches = await asyncio.to_thread(search_similar_faces, embedding, 5)
        search_time = time.time() - search_start

        if not matches:
            await websocket.send_json({
                "type": "result",
                "status": "no_matches",
                "message": "Face detected but no matches found"
            })
            return

        # No server-side image fetch. Each user's browser loads the celebrity
        # photo directly from match['image_url']. Previously the VM downloaded
        # the 5 match images per frame from Wikimedia; those blocking calls hit
        # 429 rate limits and starved the event-loop thread pool, which froze
        # *other* connected users. Browser-direct = zero image I/O on the box,
        # so concurrent users no longer block each other.
        for match in matches:
            match['similarity'] = (1 - match['score']) * 100

        total_time = time.time() - start_time

        # Send results
        await websocket.send_json({
            "type": "result",
            "status": "success",
            "matches": matches,
            "face_location": face_location,
            "processing_time": round(total_time, 3),
            "search_time": round(search_time, 3)
        })

    except Exception as e:
        print(f"Frame processing error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

