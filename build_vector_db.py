#!/usr/bin/env python3
"""
Build Redis vector database from celebrity face metadata.
Downloads images, extracts face embeddings, and stores in Redis.
"""
import os
import json
import redis
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import config

# Face recognition library for embeddings
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    print("⚠️  face_recognition not available. Install: pip install face-recognition")
    FACE_RECOGNITION_AVAILABLE = False

# Redis connection
def get_redis_client():
    """Connect to Redis."""
    return redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_DB,
        decode_responses=False  # We need bytes for vectors
    )

def load_metadata_files() -> List[Dict]:
    """Load all celebrity metadata files."""
    metadata_dir = Path("data/metadata")
    celebs = []
    
    for json_file in metadata_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get("images"):  # Only include if has images
                    celebs.append(data)
        except Exception as e:
            print(f"⚠️  Error loading {json_file}: {e}")
    
    return celebs

def download_and_extract_embedding(image_url: str) -> Optional[np.ndarray]:
    """
    Download image and extract face embedding (128-d vector).
    Returns None if face detection/encoding fails.
    """
    if not FACE_RECOGNITION_AVAILABLE:
        return None
    
    try:
        import requests
        from PIL import Image
        from io import BytesIO
        
        # Download image
        headers = {"User-Agent": "CelebFaceMatch/1.0"}
        response = requests.get(image_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Load image
        image = face_recognition.load_image_file(BytesIO(response.content))
        
        # Extract face encoding (128-d vector)
        encodings = face_recognition.face_encodings(image)
        
        if len(encodings) > 0:
            return encodings[0]  # Return first face encoding
        
        return None
        
    except Exception as e:
        return None

def create_redis_index(redis_client):
    """Create RediSearch index for vector similarity + metadata search."""
    # Import based on redis version
    try:
        from redis.commands.search.field import TextField, TagField, VectorField
        try:
            # redis >= 7.0 (lowercase module name)
            from redis.commands.search.index_definition import IndexDefinition, IndexType
        except (ImportError, ModuleNotFoundError):
            try:
                # redis 6.x (camelCase module name)
                from redis.commands.search.indexDefinition import IndexDefinition, IndexType
            except (ImportError, ModuleNotFoundError):
                # redis 5.x (in __init__)
                from redis.commands.search import IndexDefinition, IndexType
    except ImportError as e:
        print(f"❌ Redis search module not available: {e}")
        print("Make sure you have redis-py with search support installed:")
        print("  pip install 'redis[search]>=5.0'")
        raise

    index_name = config.REDIS_INDEX_NAME

    # Drop existing index if exists
    try:
        redis_client.ft(index_name).dropindex()
        print(f"Dropped existing index: {index_name}")
    except:
        pass

    # Define schema
    schema = (
        TextField("name"),
        TextField("slug"),
        TagField("category"),
        TextField("source"),
        VectorField(
            "embedding",
            "FLAT",  # or "HNSW" for larger datasets
            {
                "TYPE": "FLOAT32",
                "DIM": 128,  # face_recognition uses 128-d embeddings
                "DISTANCE_METRIC": "COSINE"
            }
        )
    )

    # Create index
    redis_client.ft(index_name).create_index(
        schema,
        definition=IndexDefinition(prefix=[f"{config.REDIS_KEY_PREFIX}:"], index_type=IndexType.HASH)
    )

    print(f"✓ Created index: {index_name}")

def store_celebrity_in_redis(redis_client, celeb: Dict, embedding: np.ndarray):
    """Store celebrity data and embedding in Redis."""
    slug = celeb["slug"]
    key = f"{config.REDIS_KEY_PREFIX}:{slug}"
    
    # Prepare data
    image_info = celeb["images"][0]
    
    data = {
        "name": celeb["name"],
        "slug": slug,
        "category": celeb.get("category", "unknown"),
        "source": image_info.get("source", "unknown"),
        "image_url": image_info.get("url", ""),
        "embedding": embedding.astype(np.float32).tobytes()  # Store as bytes
    }
    
    # Store in Redis hash
    redis_client.hset(key, mapping=data)

def main():
    if not FACE_RECOGNITION_AVAILABLE:
        print("❌ face_recognition library required. Install: pip install face-recognition")
        return
    
    print("="*70)
    print("BUILDING REDIS VECTOR DATABASE")
    print("="*70)
    
    # Load metadata
    celebs = load_metadata_files()
    print(f"Loaded {len(celebs)} celebrities with images\n")
    
    # Connect to Redis
    redis_client = get_redis_client()
    print(f"✓ Connected to Redis at {config.REDIS_HOST}:{config.REDIS_PORT}\n")
    
    # Create index
    create_redis_index(redis_client)
    print()

    # Process each celebrity
    success = 0
    failed = 0

    for idx, celeb in enumerate(celebs, 1):
        name = celeb["name"]
        image_url = celeb["images"][0].get("url")

        print(f"[{idx}/{len(celebs)}] {name}...", end=" ")

        # Extract embedding
        embedding = download_and_extract_embedding(image_url)

        if embedding is not None:
            # Store in Redis
            store_celebrity_in_redis(redis_client, celeb, embedding)
            print("✓")
            success += 1
        else:
            print("✗ (no face encoding)")
            failed += 1

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total: {len(celebs)}")
    print(f"✓ Stored in Redis: {success}")
    print(f"✗ Failed: {failed}")
    print(f"{'='*70}")
    print(f"\nRedis index: {config.REDIS_INDEX_NAME}")
    print(f"Key prefix: {config.REDIS_KEY_PREFIX}:*")
    print(f"\nReady for vector similarity search!")

if __name__ == "__main__":
    main()

