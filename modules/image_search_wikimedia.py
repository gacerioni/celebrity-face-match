import requests

# Use Portuguese Wikipedia for Brazilian celebrities
API_URL_PT = "https://pt.wikipedia.org/w/api.php"
API_URL_EN = "https://en.wikipedia.org/w/api.php"

# User-Agent is required by Wikimedia API
HEADERS = {
    "User-Agent": "CelebFaceMatch/1.0 (Brazilian Celebrity Face Recognition Project; Educational Use)"
}

def search_image_wikimedia(name: str):
    """
    Search for celebrity image on Wikipedia.
    Tries Portuguese Wikipedia first, then English as fallback.
    """
    # Try Portuguese Wikipedia first (better for Brazilian celebs)
    result = _search_wikipedia(name, API_URL_PT)
    if result:
        return result

    # Fallback to English Wikipedia
    result = _search_wikipedia(name, API_URL_EN)
    if result:
        return result

    return None

def _search_wikipedia(name: str, api_url: str):
    """Helper function to search a specific Wikipedia API"""
    params = {
        "action": "query",
        "format": "json",
        "prop": "pageimages",
        "piprop": "original",
        "titles": name
    }
    try:
        resp = requests.get(api_url, params=params, headers=HEADERS, timeout=10)
        resp.raise_for_status()  # Raise exception for bad status codes

        pages = resp.json().get("query", {}).get("pages", {})
        for p in pages.values():
            if "original" in p:
                source = "wikimedia-pt" if "pt.wikipedia" in api_url else "wikimedia-en"
                return {"url": p["original"]["source"], "source": source}
    except Exception as e:
        # Silently fail and let caller try fallback
        pass
    return None
