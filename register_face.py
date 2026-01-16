#!/usr/bin/env python3
"""
Register Custom Face - Admin UI
Add your friends/custom faces to the vector database
"""
import gradio as gr
import redis
import numpy as np
from PIL import Image
import json
from pathlib import Path
import config
import hashlib
import time

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

def extract_face_embedding(image: np.ndarray):
    """Extract face embedding from image array."""
    try:
        encodings = face_recognition.face_encodings(image)
        if len(encodings) == 0:
            return None, "❌ No face detected in image"
        
        if len(encodings) > 1:
            return None, f"⚠️ Multiple faces detected ({len(encodings)}). Please use image with single face."
        
        return encodings[0], "✅ Face detected successfully"
        
    except Exception as e:
        return None, f"❌ Error extracting face: {e}"

def save_metadata(name: str, slug: str, category: str, image_path: str):
    """Save metadata JSON file."""
    metadata_dir = Path("data/metadata")
    metadata_dir.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        "name": name,
        "slug": slug,
        "category": category,
        "images": [
            {
                "url": image_path,
                "source": "custom",
                "title": f"Custom upload: {name}",
                "validation": {
                    "valid": True,
                    "face_count": 1,
                    "reason": "Manual upload"
                }
            }
        ]
    }
    
    filepath = metadata_dir / f"{slug}.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)
    
    return str(filepath)

def store_in_redis(redis_client, name: str, slug: str, category: str, image_path: str, embedding: np.ndarray):
    """Store face embedding in Redis."""
    key = f"{config.REDIS_KEY_PREFIX}:{slug}"
    
    data = {
        "name": name,
        "slug": slug,
        "category": category,
        "source": "custom",
        "image_url": image_path,
        "embedding": embedding.astype(np.float32).tobytes()
    }
    
    redis_client.hset(key, mapping=data)
    return key

def register_face(image, name: str, category: str):
    """
    Main function to register a custom face.
    Returns: status message, preview image
    """
    if not FACE_RECOGNITION_AVAILABLE:
        return "❌ face_recognition not installed. Run: pip install face-recognition", None
    
    if image is None:
        return "❌ Please upload an image or capture from webcam", None
    
    if not name or not name.strip():
        return "❌ Please enter a name", None
    
    if not category or not category.strip():
        category = "custom"
    
    # Clean inputs
    name = name.strip()
    category = category.strip().lower()
    slug = name.lower().replace(" ", "-").replace("_", "-")
    
    # Convert PIL to numpy if needed
    if isinstance(image, Image.Image):
        image_array = np.array(image)
    else:
        image_array = image
    
    # Extract face embedding
    embedding, message = extract_face_embedding(image_array)
    
    if embedding is None:
        return message, image
    
    # Save image locally
    images_dir = Path("data/custom_images")
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    timestamp = int(time.time())
    image_filename = f"{slug}_{timestamp}.jpg"
    image_path = images_dir / image_filename
    
    # Save image
    if isinstance(image, Image.Image):
        image.save(image_path)
    else:
        Image.fromarray(image_array).save(image_path)
    
    # Save metadata
    try:
        metadata_path = save_metadata(name, slug, category, str(image_path))
    except Exception as e:
        return f"❌ Error saving metadata: {e}", image
    
    # Store in Redis
    try:
        redis_client = get_redis_client()
        redis_key = store_in_redis(redis_client, name, slug, category, str(image_path), embedding)
    except Exception as e:
        return f"❌ Error storing in Redis: {e}\nMetadata saved to: {metadata_path}", image
    
    # Success!
    result = f"""
✅ **Successfully registered!**

**Name:** {name}
**Slug:** {slug}
**Category:** {category}

**Files created:**
- Image: `{image_path}`
- Metadata: `{metadata_path}`
- Redis key: `{redis_key}`

**Embedding:** 128-d vector stored in Redis

🎉 **Ready to use!** This face will now appear in search results.
"""
    
    return result, image

# Create Gradio interface
with gr.Blocks(title="🔧 Register Custom Face", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 🔧 Register Custom Face
        ### Add your friends or custom faces to the database
        
        **Instructions:**
        1. Upload a photo or capture from webcam
        2. Enter the person's name
        3. (Optional) Enter a category
        4. Click "Register Face"
        
        **Requirements:**
        - Image must contain exactly **one face**
        - Good lighting and clear face
        - Face should be front-facing
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            # Image input
            image_input = gr.Image(
                sources=["upload", "webcam"],
                label="📸 Upload Photo or Capture from Webcam",
                type="pil"
            )

            # Input fields
            name_input = gr.Textbox(
                label="👤 Name",
                placeholder="e.g., John Doe",
                info="Required - Full name of the person"
            )

            category_input = gr.Textbox(
                label="🏷️ Category",
                placeholder="e.g., friend, family, colleague",
                value="custom",
                info="Optional - Defaults to 'custom'"
            )

            # Register button
            register_btn = gr.Button("✅ Register Face", variant="primary", size="lg")

        with gr.Column(scale=1):
            # Status output
            status_output = gr.Markdown(
                "👆 Upload an image and fill in the details to get started",
                label="Status"
            )

            # Preview
            preview_output = gr.Image(
                label="Preview",
                type="pil"
            )

    # Wire up the button
    register_btn.click(
        fn=register_face,
        inputs=[image_input, name_input, category_input],
        outputs=[status_output, preview_output]
    )

    gr.Markdown(
        """
        ---
        ### 📝 Notes:

        **What happens when you register:**
        1. ✅ Face is detected and validated (must be exactly 1 face)
        2. ✅ 128-d embedding is extracted using dlib ResNet-34
        3. ✅ Image is saved to `data/custom_images/`
        4. ✅ Metadata is saved to `data/metadata/{slug}.json`
        5. ✅ Embedding is stored in Redis vector database
        6. ✅ Face is immediately searchable!

        **File structure:**
        ```
        data/
        ├── custom_images/
        │   └── john-doe_1234567890.jpg
        └── metadata/
            └── john-doe.json
        ```

        **Redis key format:**
        ```
        celeb:john-doe
        ```

        **To remove a face:**
        1. Delete the metadata file: `data/metadata/{slug}.json`
        2. Delete from Redis: `redis-cli DEL celeb:{slug}`
        3. Rebuild vector DB: `python build_vector_db.py`

        ---

        ### 🔍 Testing:

        After registering, test it:
        ```bash
        # Static demo
        python app.py

        # Live demo
        python app_live.py

        # Command line
        python search_face.py path/to/test/image.jpg
        ```
        """
    )

if __name__ == "__main__":
    if not FACE_RECOGNITION_AVAILABLE:
        print("❌ face_recognition not installed. Run: pip install face-recognition")
    else:
        print("🔧 Starting Face Registration Admin UI...")
        print("🌐 Opening on http://localhost:7862")
        demo.launch(server_port=7862, share=False)

