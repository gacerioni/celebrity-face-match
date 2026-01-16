#!/usr/bin/env python3
"""
Live Webcam Celebrity Face Match - Reactive Real-time Demo
Separate from the main app - this is the "wow factor" demo version!
"""
import gradio as gr
import redis
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import config
import time
import threading

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

# Global state for performance optimization
last_embedding = None
last_embedding_time = 0
last_matches = None  # Cache last search results
last_search_time = 0  # When we last searched Redis
last_status = "📹 Waiting for webcam..."  # Cache last status
last_celeb_images = [None, None, None, None, None]  # Cache last celebrity images
PROCESS_INTERVAL = 3.0  # Only process face detection every 3 seconds
processing_lock = threading.Lock()
cache = {}

def get_redis_client():
    """Connect to Redis."""
    return redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_DB,
        decode_responses=False
    )

def extract_face_embedding(image: np.ndarray):
    """Extract face embedding from image array."""
    try:
        encodings = face_recognition.face_encodings(image)
        if len(encodings) == 0:
            return None, None
        
        # Get face location for bounding box
        face_locations = face_recognition.face_locations(image)
        return encodings[0], face_locations[0] if face_locations else None
        
    except Exception as e:
        print(f"Error extracting embedding: {e}")
        return None, None

def search_similar_faces(redis_client, query_embedding: np.ndarray, top_k: int = 5):
    """Search for similar faces using vector similarity."""
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

def download_celebrity_image(url):
    """Download celebrity image or load from local file (with caching)."""
    if url in cache:
        return cache[url]

    try:
        # Check if it's a local file path
        if url.startswith('data/') or url.startswith('./data/') or url.startswith('/'):
            from pathlib import Path
            file_path = Path(url)
            if file_path.exists():
                img = Image.open(file_path)
                cache[url] = img
                return img
            else:
                print(f"Local file not found: {url}")
                return None

        # Otherwise, download from URL
        headers = {"User-Agent": "CelebFaceMatch/1.0"}
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        cache[url] = img
        return img
    except Exception as e:
        print(f"Failed to load image: {e}")
        return None

def draw_face_box(image: Image.Image, face_location, color="lime", width=3):
    """Draw bounding box around detected face."""
    if face_location is None:
        return image
    
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)
    
    # face_location is (top, right, bottom, left)
    top, right, bottom, left = face_location
    
    # Draw rectangle
    draw.rectangle(
        [(left, top), (right, bottom)],
        outline=color,
        width=width
    )
    
    # Add label
    try:
        draw.text((left, top - 20), "FACE DETECTED", fill=color)
    except:
        pass
    
    return img_copy

def process_frame(frame):
    """
    Process webcam frame in real-time.
    Returns: status_text, annotated_frame, match1, match2, match3, match4, match5
    """
    global last_embedding, last_embedding_time, last_matches, last_search_time
    global last_status, last_celeb_images

    if not FACE_RECOGNITION_AVAILABLE:
        return "❌ face_recognition not installed", frame, None, None, None, None, None

    if frame is None:
        return "📹 Waiting for webcam...", None, None, None, None, None, None

    current_time = time.time()
    time_since_last_process = current_time - last_search_time

    # Fast path: Just return cached results if we processed recently
    if time_since_last_process < PROCESS_INTERVAL and last_matches is not None:
        # Still detect and draw face box for visual feedback
        if isinstance(frame, Image.Image):
            frame_array = np.array(frame)
        else:
            frame_array = frame

        embedding, face_location = extract_face_embedding(frame_array)

        if embedding is not None and face_location is not None:
            # Draw face bounding box
            frame_pil = Image.fromarray(frame_array) if isinstance(frame_array, np.ndarray) else frame
            annotated_frame = draw_face_box(frame_pil, face_location)
        else:
            annotated_frame = frame

        # Return cached results with updated countdown
        time_remaining = PROCESS_INTERVAL - time_since_last_process

        # Build status with countdown but keep all match info
        if last_matches:
            top_match = last_matches[0]
            similarity = (1 - top_match['score']) * 100

            status = f"✅ **MATCH FOUND!** ⚡ (cached)\n\n"
            status += f"🏆 **Top Match: {top_match['name']}**\n"
            status += f"📊 Similarity: **{similarity:.1f}%**\n"
            status += f"🔄 Next update in: {time_remaining:.1f}s\n\n"
            status += "**All Matches:**\n"
            for idx, match in enumerate(last_matches, 1):
                sim = (1 - match['score']) * 100
                status += f"{idx}. {match['name']} - {sim:.1f}%\n"
        else:
            status = last_status

        return status, annotated_frame, last_celeb_images[0], last_celeb_images[1], last_celeb_images[2], last_celeb_images[3], last_celeb_images[4]

    # Slow path: Actually process the frame
    # Acquire lock to prevent concurrent processing
    if not processing_lock.acquire(blocking=False):
        # Return cached results if we're still processing
        return last_status, frame, last_celeb_images[0], last_celeb_images[1], last_celeb_images[2], last_celeb_images[3], last_celeb_images[4]

    try:
        start_time = time.time()
        current_time = time.time()

        # Convert PIL to numpy
        if isinstance(frame, Image.Image):
            frame_array = np.array(frame)
        else:
            frame_array = frame

        # Extract face embedding
        embedding, face_location = extract_face_embedding(frame_array)

        if embedding is None:
            annotated = Image.fromarray(frame_array) if isinstance(frame_array, np.ndarray) else frame
            return "👤 No face detected - please position your face in the frame", annotated, None, None, None, None, None

        # Draw face bounding box
        frame_pil = Image.fromarray(frame_array) if isinstance(frame_array, np.ndarray) else frame
        annotated_frame = draw_face_box(frame_pil, face_location)

        # Do full Redis search (we only get here every 5 seconds)
        try:
            redis_client = get_redis_client()
        except Exception as e:
            return f"❌ Redis error: {e}", annotated_frame, None, None, None, None, None

        try:
            matches = search_similar_faces(redis_client, embedding, top_k=5)
        except Exception as e:
            return f"❌ Search error: {e}", annotated_frame, None, None, None, None, None

        if not matches:
            return "✅ Face detected but no matches found", annotated_frame, None, None, None, None, None

        # Cache the results
        last_matches = matches
        last_search_time = current_time

        # Download celebrity images
        celeb_images = []
        for i in range(min(5, len(matches))):
            img = download_celebrity_image(matches[i]['image_url'])
            celeb_images.append(img)

        # Pad with None
        while len(celeb_images) < 5:
            celeb_images.append(None)

        # Cache celebrity images
        last_celeb_images = celeb_images

        # Build status text
        elapsed = time.time() - start_time
        top_match = matches[0]
        similarity = (1 - top_match['score']) * 100

        status = f"✅ **MATCH FOUND!** 🔍\n\n"
        status += f"🏆 **Top Match: {top_match['name']}**\n"
        status += f"📊 Similarity: **{similarity:.1f}%**\n"
        status += f"⚡ Processing time: {elapsed:.2f}s\n\n"
        status += "**All Matches:**\n"
        for idx, match in enumerate(matches, 1):
            sim = (1 - match['score']) * 100
            status += f"{idx}. {match['name']} - {sim:.1f}%\n"

        # Cache status
        last_status = status

        return status, annotated_frame, celeb_images[0], celeb_images[1], celeb_images[2], celeb_images[3], celeb_images[4]

    finally:
        processing_lock.release()

# Create Gradio interface with live webcam
with gr.Blocks(title="🎭 Live Celebrity Face Match", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🎭 Live Celebrity Face Match
        ### Real-time reactive face detection demo!

        **How it works:**
        1. Click "Start Webcam" below
        2. Position your face in the frame
        3. Watch as it automatically detects and matches your face in real-time!

        *Webcam updates smoothly, face matching every 3s - optimized for performance*
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            # Webcam input with streaming
            webcam = gr.Image(
                sources=["webcam"],
                streaming=True,
                label="📹 Live Webcam Feed",
                type="pil"
            )

            status_text = gr.Markdown(
                "👤 **Status:** Waiting for webcam...",
                label="Status"
            )

        with gr.Column(scale=1):
            gr.Markdown("### 🏆 Top 5 Celebrity Matches")

            with gr.Row():
                match1 = gr.Image(label="1st", show_label=True, height=150)
                match2 = gr.Image(label="2nd", show_label=True, height=150)

            with gr.Row():
                match3 = gr.Image(label="3rd", show_label=True, height=150)
                match4 = gr.Image(label="4th", show_label=True, height=150)

            with gr.Row():
                match5 = gr.Image(label="5th", show_label=True, height=150)

    # Real-time processing - triggers every time webcam updates
    webcam.stream(
        fn=process_frame,
        inputs=[webcam],
        outputs=[status_text, webcam, match1, match2, match3, match4, match5],
        stream_every=0.2,  # Stream at ~5 FPS - balanced performance
        show_progress="hidden"
    )

    gr.Markdown(
        """
        ---
        ### 💡 Tips for best results:
        - 📸 Good lighting helps!
        - 👤 Face the camera directly
        - 🎯 Get close enough so your face fills the frame
        - ⏱️ Webcam updates smoothly, matching every 3 seconds

        ### 🔧 Technical Details:
        - **Face Detection:** dlib ResNet-34 (128-d embeddings)
        - **Search Engine:** Redis Vector Search (cosine similarity)
        - **Database:** 1000+ Brazilian celebrities
        - **Performance:** Optimized for smooth real-time matching!

        *Want the static upload version? Check out `app.py`*
        """
    )

if __name__ == "__main__":
    if not FACE_RECOGNITION_AVAILABLE:
        print("❌ face_recognition not installed. Run: pip install face-recognition")
    else:
        print("🚀 Starting LIVE Celebrity Face Match Demo...")
        print("📹 This version uses real-time webcam streaming!")
        print("🌐 Opening on http://localhost:7860")
        demo.launch(share=False)

