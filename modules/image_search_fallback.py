"""
Fallback image search using Google Custom Search API and web scraping.
"""
import requests
import os
from typing import Optional, Dict, List

HEADERS = {
    "User-Agent": "CelebFaceMatch/1.0 (Brazilian Celebrity Face Recognition Project; Educational Use)"
}

def search_google_images(name: str, max_results: int = 5) -> List[Dict]:
    """
    Search for images using Google Custom Search API.
    Requires GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables.

    Returns list of image results with URLs.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")

    if not api_key or not cse_id:
        # API keys not configured, skip
        return []

    try:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": f"{name} retrato foto",  # "portrait photo" in Portuguese
            "searchType": "image",
            "num": min(max_results, 10),  # API max is 10
            "imgSize": "large",
            "imgType": "face",
            "safe": "active"
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("items", []):
            results.append({
                "url": item.get("link"),
                "source": "google-images",
                "title": item.get("title", ""),
                "thumbnail": item.get("image", {}).get("thumbnailLink", "")
            })

        return results

    except Exception as e:
        return []

def search_bing_images(name: str, max_results: int = 5) -> List[Dict]:
    """
    Search for images using Bing Image Search API.
    Requires BING_API_KEY environment variable.

    Returns list of image results with URLs.
    """
    api_key = os.getenv("BING_API_KEY")

    if not api_key:
        return []

    try:
        url = "https://api.bing.microsoft.com/v7.0/images/search"
        headers = {
            "Ocp-Apim-Subscription-Key": api_key
        }
        params = {
            "q": f"{name} retrato foto",
            "count": min(max_results, 50),
            "imageType": "Photo",
            "size": "Large",
            "safeSearch": "Strict"
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("value", []):
            results.append({
                "url": item.get("contentUrl"),
                "source": "bing-images",
                "title": item.get("name", ""),
                "thumbnail": item.get("thumbnailUrl", "")
            })

        return results

    except Exception as e:
        return []

def search_fallback_image(name: str, source: str = "auto") -> Optional[Dict]:
    """
    Search for celebrity image using fallback sources (Google, Bing).

    Args:
        name: Celebrity name
        source: "auto", "google", or "bing"

    Returns:
        Dict with url and source, or None if not found
    """
    results = []

    if source == "auto" or source == "google":
        results.extend(search_google_images(name, max_results=3))

    if source == "auto" or source == "bing":
        results.extend(search_bing_images(name, max_results=3))

    # Return first result if any found
    if results:
        return results[0]

    return None

def search_fallback_images_multiple(name: str, max_results: int = 5) -> List[Dict]:
    """
    Search for multiple celebrity images using fallback sources.
    Returns list of image results to try.
    """
    results = []

    # Try Google first
    results.extend(search_google_images(name, max_results=max_results))

    # If not enough, try Bing
    if len(results) < max_results:
        results.extend(search_bing_images(name, max_results=max_results - len(results)))

    return results[:max_results]
