"""
Face detection module using OpenCV's DNN face detector.
Validates that images contain clear, single faces suitable for facial recognition.
"""
import cv2
import numpy as np
import requests
from io import BytesIO
from typing import Dict, List, Optional, Tuple
import config

# User-Agent for image downloads
HEADERS = {
    "User-Agent": "CelebFaceMatch/1.0 (Brazilian Celebrity Face Recognition Project; Educational Use)"
}

# Global detector (lazy loaded)
_face_detector = None

def _get_face_detector():
    """
    Lazy load the OpenCV DNN face detector.
    Uses a pre-trained Caffe model for face detection.
    """
    global _face_detector
    
    if _face_detector is None:
        try:
            # Try to load OpenCV's DNN face detector
            # This uses a pre-trained ResNet-based model
            modelFile = "models/res10_300x300_ssd_iter_140000.caffemodel"
            configFile = "models/deploy.prototxt"
            
            _face_detector = cv2.dnn.readNetFromCaffe(configFile, modelFile)
        except Exception as e:
            # Fallback to Haar Cascade if DNN model not available
            try:
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                _face_detector = cv2.CascadeClassifier(cascade_path)
            except Exception as e2:
                print(f"Warning: Could not load face detector: {e2}")
                _face_detector = None
    
    return _face_detector

def download_image_to_memory(url: str) -> Optional[np.ndarray]:
    """
    Download image from URL and convert to OpenCV format.
    Returns numpy array (BGR format) or None if failed.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=15, stream=True)
        response.raise_for_status()
        
        # Read image into memory
        image_data = BytesIO(response.content)
        image_array = np.asarray(bytearray(image_data.read()), dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        return image
    except Exception as e:
        return None

def detect_faces_dnn(image: np.ndarray, confidence_threshold: float = 0.5) -> List[Dict]:
    """
    Detect faces using OpenCV DNN detector.
    Returns list of face detections with bounding boxes and confidence scores.
    """
    detector = _get_face_detector()
    if detector is None or not isinstance(detector, cv2.dnn_Net):
        return []

    h, w = image.shape[:2]

    # Prepare blob for DNN
    blob = cv2.dnn.blobFromImage(
        cv2.resize(image, (300, 300)),
        1.0,
        (300, 300),
        (104.0, 177.0, 123.0)
    )

    detector.setInput(blob)
    detections = detector.forward()

    faces = []
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]

        if confidence > confidence_threshold:
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (x1, y1, x2, y2) = box.astype("int")

            faces.append({
                "bbox": (int(x1), int(y1), int(x2 - x1), int(y2 - y1)),  # Convert to Python int
                "confidence": float(confidence),
                "area": int((x2 - x1) * (y2 - y1))
            })

    return faces

def detect_faces_haar(image: np.ndarray) -> List[Dict]:
    """
    Detect faces using Haar Cascade (fallback method).
    Returns list of face detections with bounding boxes.
    """
    detector = _get_face_detector()
    if detector is None or not isinstance(detector, cv2.CascadeClassifier):
        return []

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces_rects = detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )

    faces = []
    for (x, y, w, h) in faces_rects:
        faces.append({
            "bbox": (int(x), int(y), int(w), int(h)),  # Convert to Python int
            "confidence": 1.0,
            "area": int(w * h)
        })

    return faces

def validate_image_with_face_detection(url: str) -> Dict:
    """
    Download and validate image for face detection quality.
    
    Returns dict with:
        - valid: bool - whether image passes all checks
        - face_count: int - number of faces detected
        - faces: list - face detection details
        - reason: str - reason for failure (if invalid)
        - image_size: tuple - (width, height) of image
    """
    result = {
        "valid": False,
        "face_count": 0,
        "faces": [],
        "reason": "",
        "image_size": (0, 0)
    }
    
    # Download image
    image = download_image_to_memory(url)
    if image is None:
        result["reason"] = "Failed to download image"
        return result
    
    h, w = image.shape[:2]
    result["image_size"] = (int(w), int(h))  # Convert to Python int
    
    # Check minimum image size
    if w < config.MIN_IMAGE_WIDTH or h < config.MIN_IMAGE_HEIGHT:
        result["reason"] = f"Image too small: {w}x{h} (min: {config.MIN_IMAGE_WIDTH}x{config.MIN_IMAGE_HEIGHT})"
        return result
    
    # Detect faces
    detector = _get_face_detector()
    if isinstance(detector, cv2.dnn_Net):
        faces = detect_faces_dnn(image, config.MIN_FACE_CONFIDENCE)
    else:
        faces = detect_faces_haar(image)
    
    result["faces"] = faces
    result["face_count"] = len(faces)
    
    # Validate face count
    if len(faces) == 0:
        result["reason"] = "No faces detected"
        return result
    
    if len(faces) > config.MAX_FACES_ALLOWED:
        result["reason"] = f"Too many faces: {len(faces)} (max: {config.MAX_FACES_ALLOWED})"
        return result
    
    # Check face size
    largest_face = max(faces, key=lambda f: f["area"])
    face_w, face_h = largest_face["bbox"][2], largest_face["bbox"][3]
    
    if face_w < config.MIN_FACE_SIZE or face_h < config.MIN_FACE_SIZE:
        result["reason"] = f"Face too small: {face_w}x{face_h} (min: {config.MIN_FACE_SIZE})"
        return result
    
    # All checks passed!
    result["valid"] = True
    result["reason"] = "OK"
    return result

