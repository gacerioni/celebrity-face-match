"""
Download pre-trained face detection models for OpenCV.
"""
import os
import requests
from pathlib import Path

MODELS_DIR = "models"

# OpenCV DNN face detector (ResNet-based)
MODELS = {
    "deploy.prototxt": "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt",
    "res10_300x300_ssd_iter_140000.caffemodel": "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
}

def download_file(url: str, filepath: str):
    """Download a file from URL to filepath."""
    print(f"Downloading {os.path.basename(filepath)}...")
    
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filepath, 'wb') as f:
            if total_size == 0:
                f.write(response.content)
            else:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress = (downloaded / total_size) * 100
                        print(f"  Progress: {progress:.1f}%", end='\r')
        
        print(f"  ✓ Downloaded {os.path.basename(filepath)} ({total_size/1024/1024:.1f} MB)")
        return True
        
    except Exception as e:
        print(f"  ✗ Error downloading {os.path.basename(filepath)}: {e}")
        return False

def main():
    print("="*70)
    print("DOWNLOADING FACE DETECTION MODELS")
    print("="*70)
    
    # Create models directory
    Path(MODELS_DIR).mkdir(exist_ok=True)
    print(f"Models directory: {MODELS_DIR}\n")
    
    # Download each model
    success_count = 0
    for filename, url in MODELS.items():
        filepath = os.path.join(MODELS_DIR, filename)
        
        # Skip if already exists
        if os.path.exists(filepath):
            print(f"✓ {filename} already exists, skipping...")
            success_count += 1
            continue
        
        if download_file(url, filepath):
            success_count += 1
    
    print("\n" + "="*70)
    if success_count == len(MODELS):
        print("✓ All models downloaded successfully!")
        print("\nYou can now use face detection in the pipeline.")
    else:
        print(f"⚠ Downloaded {success_count}/{len(MODELS)} models")
        print("\nSome models failed to download. Face detection may not work properly.")
    print("="*70)

if __name__ == "__main__":
    main()

