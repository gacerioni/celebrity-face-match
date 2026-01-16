#!/usr/bin/env python3
"""
Search for similar celebrity faces using an uploaded image.
"""
import sys
import redis
import numpy as np
from typing import List, Dict
import config

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    print("❌ face_recognition required. Install: pip install face-recognition")
    sys.exit(1)

def get_redis_client():
    """Connect to Redis."""
    return redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_DB,
        decode_responses=False
    )

def extract_face_embedding(image_path: str) -> np.ndarray:
    """Extract face embedding from image file."""
    try:
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        
        if len(encodings) == 0:
            print("❌ No face detected in image")
            return None
        
        if len(encodings) > 1:
            print(f"⚠️  Multiple faces detected ({len(encodings)}), using first one")
        
        return encodings[0]
        
    except Exception as e:
        print(f"❌ Error processing image: {e}")
        return None

def search_similar_faces(redis_client, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict]:
    """
    Search for similar faces using vector similarity.
    Returns top K most similar celebrities.
    """
    from redis.commands.search.query import Query
    
    # Convert embedding to bytes
    query_vector = query_embedding.astype(np.float32).tobytes()
    
    # Build KNN query
    query = (
        Query(f"*=>[KNN {top_k} @embedding $vec AS score]")
        .return_fields("name", "slug", "category", "source", "image_url", "score")
        .sort_by("score")
        .dialect(2)
    )
    
    # Execute search
    results = redis_client.ft(config.REDIS_INDEX_NAME).search(
        query,
        query_params={"vec": query_vector}
    )
    
    # Parse results
    matches = []
    for doc in results.docs:
        matches.append({
            "name": doc.name.decode() if isinstance(doc.name, bytes) else doc.name,
            "slug": doc.slug.decode() if isinstance(doc.slug, bytes) else doc.slug,
            "category": doc.category.decode() if isinstance(doc.category, bytes) else doc.category,
            "source": doc.source.decode() if isinstance(doc.source, bytes) else doc.source,
            "image_url": doc.image_url.decode() if isinstance(doc.image_url, bytes) else doc.image_url,
            "score": float(doc.score)
        })
    
    return matches

def main():
    if len(sys.argv) < 2:
        print("Usage: python search_face.py <image_path> [top_k]")
        print("\nExample:")
        print("  python search_face.py my_photo.jpg")
        print("  python search_face.py my_photo.jpg 10")
        sys.exit(1)
    
    image_path = sys.argv[1]
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    print("="*70)
    print("CELEBRITY FACE SEARCH")
    print("="*70)
    print(f"Image: {image_path}")
    print(f"Top matches: {top_k}\n")
    
    # Extract face embedding from query image
    print("Extracting face from image...")
    embedding = extract_face_embedding(image_path)
    
    if embedding is None:
        sys.exit(1)
    
    print("✓ Face detected\n")
    
    # Connect to Redis
    redis_client = get_redis_client()
    
    # Search for similar faces
    print("Searching for similar celebrities...\n")
    matches = search_similar_faces(redis_client, embedding, top_k)
    
    # Display results
    print("="*70)
    print("TOP MATCHES")
    print("="*70)
    
    for idx, match in enumerate(matches, 1):
        print(f"\n{idx}. {match['name']}")
        print(f"   Category: {match['category']}")
        print(f"   Similarity: {1 - match['score']:.2%}")  # Convert distance to similarity
        print(f"   Image: {match['image_url'][:60]}...")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()

