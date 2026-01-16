"""
Free image search using web scraping - NO API KEY REQUIRED!
Uses Google Images via web scraping (legal for personal/educational use).
"""
import requests
import json
import re
from typing import List, Dict
from bs4 import BeautifulSoup
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

def search_google_images_scrape(name: str, max_results: int = 10) -> List[Dict]:
    """
    Search Google Images via web scraping (FREE, no API key).
    Legal for personal/educational use.

    Args:
        name: Celebrity name to search
        max_results: Maximum number of results to return

    Returns:
        List of image results with URLs
    """
    try:
        # Google Images search URL
        search_query = f"{name} retrato foto"
        url = "https://www.google.com/search"
        params = {
            "q": search_query,
            "tbm": "isch",  # Image search
            "hl": "en",
            "safe": "active"
        }

        response = requests.get(url, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        results = []

        # Method 1: Find image URLs in script tags
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'AF_initDataCallback' in script.string:
                # Extract image URLs using regex
                matches = re.findall(r'https://[^"]+\.(?:jpg|jpeg|png|webp)', script.string)
                for match in matches[:max_results]:
                    # Filter out small icons and thumbnails
                    if 'gstatic' not in match and len(match) > 50:
                        results.append({
                            "url": match,
                            "source": "google-scrape",
                            "title": name,
                            "thumbnail": match
                        })

                        if len(results) >= max_results:
                            break

            if len(results) >= max_results:
                break

        # Method 2: Fallback - find img tags
        if len(results) < max_results:
            images = soup.find_all('img')
            for img in images:
                src = img.get('src') or img.get('data-src')
                if src and src.startswith('http') and not src.endswith('.svg'):
                    if 'gstatic' not in src and len(src) > 50:
                        results.append({
                            "url": src,
                            "source": "google-scrape-img",
                            "title": name,
                            "thumbnail": src
                        })

                        if len(results) >= max_results:
                            break

        return results[:max_results]

    except Exception as e:
        print(f"    Google scrape error: {e}")
        return []

def search_bing_images_scrape(name: str, max_results: int = 10) -> List[Dict]:
    """
    Search Bing Images via web scraping (FREE, no API key).

    Args:
        name: Celebrity name to search
        max_results: Maximum number of results to return

    Returns:
        List of image results with URLs
    """
    try:
        # Bing Images search URL
        search_query = f"{name} retrato foto"
        url = "https://www.bing.com/images/search"
        params = {
            "q": search_query,
            "qft": "+filterui:photo-photo",  # Photos only
            "FORM": "IRFLTR"
        }

        response = requests.get(url, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        results = []

        # Find image URLs in data attributes
        images = soup.find_all('a', class_='iusc')
        for img_link in images[:max_results * 2]:  # Get more to filter
            m = img_link.get('m')
            if m:
                try:
                    metadata = json.loads(m)
                    img_url = metadata.get('murl') or metadata.get('turl')
                    if img_url:
                        results.append({
                            "url": img_url,
                            "source": "bing-scrape",
                            "title": metadata.get('t', name),
                            "thumbnail": metadata.get('turl', img_url)
                        })

                        if len(results) >= max_results:
                            break
                except:
                    continue

        return results[:max_results]

    except Exception as e:
        print(f"    Bing scrape error: {e}")
        return []

def search_free_images(name: str, max_results: int = 10) -> List[Dict]:
    """
    Search for images using FREE methods (no API key required).
    Tries multiple sources and combines results.

    Args:
        name: Celebrity name to search
        max_results: Maximum number of results to return

    Returns:
        List of image results with URLs
    """
    all_results = []

    # Try Google Images scraping first (usually best results)
    google_results = search_google_images_scrape(name, max_results=max_results)
    if google_results:
        all_results.extend(google_results)

    # If not enough, try Bing
    if len(all_results) < max_results:
        bing_results = search_bing_images_scrape(name, max_results=max_results - len(all_results))
        if bing_results:
            all_results.extend(bing_results)

    return all_results[:max_results]

# Aliases for backward compatibility
def search_duckduckgo_simple(name: str, max_results: int = 5) -> List[Dict]:
    """Alias for search_free_images (backward compatibility)."""
    return search_free_images(name, max_results)

def search_duckduckgo_images(name: str, max_results: int = 10) -> List[Dict]:
    """Alias for search_free_images (backward compatibility)."""
    return search_free_images(name, max_results)

