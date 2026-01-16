import requests

# User-Agent is required by many image hosts including Wikimedia
HEADERS = {
    "User-Agent": "CelebFaceMatch/1.0 (Brazilian Celebrity Face Recognition Project; Educational Use)"
}

def validate_image(url: str) -> bool:
    """
    Validate that a URL points to a valid image.
    Returns True if the URL is accessible and returns an image content type.
    """
    try:
        # Use HEAD request to check without downloading the full image
        head = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)

        if head.status_code >= 400:
            return False

        content_type = head.headers.get("Content-Type", "")
        if "image" not in content_type:
            return False

        return True
    except Exception as e:
        # If validation fails, return False
        return False
