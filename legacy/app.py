#!/usr/bin/env python3
"""
Gradio UI for Celebrity Face Match
Upload your photo and find your celebrity lookalikes!
"""
import gradio as gr
import redis
import numpy as np
from PIL import Image
import requests
from io import BytesIO
import config

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

def get_redis_client():
    """Connect to Redis."""
    return redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_DB,
        decode_responses=False
    )

def extract_face_embedding(image: Image.Image) -> np.ndarray:
    """Extract face embedding from PIL Image."""
    try:
        # Convert PIL to numpy array
        image_array = np.array(image)
        
        # Extract face encoding
        encodings = face_recognition.face_encodings(image_array)
        
        if len(encodings) == 0:
            return None
        
        return encodings[0]
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def search_similar_faces(redis_client, query_embedding: np.ndarray, top_k: int = 5):
    """Search for similar faces using vector similarity."""
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
            "image_url": doc.image_url.decode() if isinstance(doc.image_url, bytes) else doc.image_url,
            "score": float(doc.score)
        })
    
    return matches

def download_celebrity_image(url):
    """Download celebrity image or load from local file."""
    try:
        # Check if it's a local file path
        if url.startswith('data/') or url.startswith('./data/') or url.startswith('/'):
            from pathlib import Path
            file_path = Path(url)
            if file_path.exists():
                return Image.open(file_path)
            else:
                print(f"Local file not found: {url}")
                return None

        # Otherwise, download from URL
        headers = {"User-Agent": "CelebFaceMatch/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"Failed to load image: {e}")
        return None

def find_celebrity_match(image):
    """Main function to find celebrity matches."""
    if not FACE_RECOGNITION_AVAILABLE:
        return "❌ face_recognition library not installed. Run: pip install face-recognition", None, None, None, None, None

    if image is None:
        return "Please upload an image", None, None, None, None, None

    # Extract face embedding
    embedding = extract_face_embedding(image)

    if embedding is None:
        return "❌ No face detected in the image. Please upload a clear photo with your face.", None, None, None, None, None

    # Connect to Redis
    try:
        redis_client = get_redis_client()
    except Exception as e:
        return f"❌ Could not connect to Redis: {e}\nMake sure Redis is running.", None, None, None, None, None

    # Search for similar faces
    try:
        matches = search_similar_faces(redis_client, embedding, top_k=5)
    except Exception as e:
        return f"❌ Search failed: {e}", None, None, None, None, None

    if not matches:
        return "No matches found", None, None, None, None, None

    # Format results
    result_text = "🎯 **Your Celebrity Lookalikes:**\n\n"

    for idx, match in enumerate(matches, 1):
        similarity = (1 - match['score']) * 100  # Convert distance to similarity percentage
        result_text += f"**{idx}. {match['name']}**\n"
        result_text += f"   Similarity: {similarity:.1f}%\n"
        result_text += f"   Category: {match['category']}\n\n"

    # Download top 5 celebrity images
    celeb_images = []
    for i in range(min(5, len(matches))):
        img = download_celebrity_image(matches[i]['image_url'])
        celeb_images.append(img)

    # Pad with None if less than 5
    while len(celeb_images) < 5:
        celeb_images.append(None)

    return result_text, celeb_images[0], celeb_images[1], celeb_images[2], celeb_images[3], celeb_images[4]

# Create Gradio interface
with gr.Blocks(title="Celebrity Face Match 🎭", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🎭 Celebrity Face Match
        ### Find your Brazilian celebrity lookalike!

        Upload a photo of yourself and discover which Brazilian celebrities you look like most.
        """
    )

    with gr.Row():
        with gr.Column():
            input_image = gr.Image(type="pil", label="Upload Your Photo", sources=["upload", "webcam"])
            submit_btn = gr.Button("Find My Celebrity Match! 🔍", variant="primary", size="lg")

        with gr.Column():
            output_text = gr.Markdown(label="Results")

    gr.Markdown("### 🏆 Top 5 Matches")

    with gr.Row():
        match1 = gr.Image(label="1st Match", show_label=True)
        match2 = gr.Image(label="2nd Match", show_label=True)
        match3 = gr.Image(label="3rd Match", show_label=True)
        match4 = gr.Image(label="4th Match", show_label=True)
        match5 = gr.Image(label="5th Match", show_label=True)

    submit_btn.click(
        fn=find_celebrity_match,
        inputs=[input_image],
        outputs=[output_text, match1, match2, match3, match4, match5]
    )

    gr.Markdown(
        """
        ---
        **How it works:**
        1. Upload a clear photo of your face (or use webcam)
        2. AI extracts your facial features (128-dimensional embedding)
        3. Searches 1000+ Brazilian celebrities using vector similarity
        4. Returns your top 5 matches!

        *Powered by face_recognition + Redis Vector Search*
        """
    )

if __name__ == "__main__":
    if not FACE_RECOGNITION_AVAILABLE:
        print("❌ face_recognition not installed. Run: pip install face-recognition")
    else:
        print("🚀 Starting Celebrity Face Match UI...")
        demo.launch(share=False)

