"""
Configuration file for the Celebrity Face Match project.
"""

# Celebrity list to use
# Options:
#   - "data/celebrities_seed.json" - Original curated list (306 celebs)
#   - "data/celebrities_generated.json" - Auto-generated from Wikipedia (2,444 celebs)
#   - "data/celebrities_combined.json" - Combined list (2,659 unique celebs)
CELEBRITY_LIST = "data/celebrities_combined.json"

# Image search settings
SEARCH_TIMEOUT = 10  # seconds
VALIDATE_IMAGES = True

# Metadata storage
METADATA_PATH = "data/metadata"

# Rate limiting (to be nice to Wikipedia)
REQUEST_DELAY = 0.1  # seconds between requests

# Face detection and validation settings
FACE_DETECTION_ENABLED = True
MIN_FACE_SIZE = 80  # Minimum face size in pixels (width or height)
MAX_FACES_ALLOWED = 3  # Maximum number of faces in image (1 = solo portrait only)
MIN_FACE_CONFIDENCE = 0.7  # Minimum confidence score for face detection (0.0-1.0)

# Image search strategy
# NOTE: You DON'T need API keys! Free web scraping works great!
# The script will try:
#   1. Wikipedia (free, high quality)
#   2. Google/Bing scraping (FREE, no API key needed)
#   3. Google/Bing API (optional, only if you set API keys)
ENABLE_FALLBACK_SEARCH = True  # Enable Google/Bing API fallback (requires API keys - OPTIONAL)

# Quality thresholds
MIN_IMAGE_WIDTH = 200  # Minimum image width in pixels
MIN_IMAGE_HEIGHT = 200  # Minimum image height in pixels

# Redis configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_INDEX_NAME = "celeb_faces_idx"
REDIS_KEY_PREFIX = "celeb"
