#!/usr/bin/env python3
"""
Prepare celebrity face database with intelligent image search and validation.
INCREMENTAL: Skips celebrities that already have valid images.
"""
from modules.celeb_list import load_celebrities
from modules.image_search_wikimedia import search_image_wikimedia
from modules.image_search_duckduckgo import search_free_images
from modules.image_search_fallback import search_fallback_images_multiple
from modules.image_validator import validate_image
from modules.metadata_store import save_metadata
import config
import time
import sys
import os
import json
from pathlib import Path

# Import face detection if enabled
if config.FACE_DETECTION_ENABLED:
    try:
        from modules.face_detector import validate_image_with_face_detection
        FACE_DETECTION_AVAILABLE = True
    except ImportError:
        print("⚠️  Face detection not available. Install: pip install opencv-python")
        FACE_DETECTION_AVAILABLE = False
else:
    FACE_DETECTION_AVAILABLE = False

def metadata_exists(slug: str) -> bool:
    """Check if metadata file already exists for this celebrity."""
    metadata_path = Path(config.METADATA_PATH) / f"{slug}.json"
    return metadata_path.exists()

def load_existing_metadata(slug: str) -> dict:
    """Load existing metadata if it exists."""
    metadata_path = Path(config.METADATA_PATH) / f"{slug}.json"
    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def has_valid_image(slug: str) -> bool:
    """Check if celebrity already has a valid image in metadata."""
    metadata = load_existing_metadata(slug)
    if metadata and "images" in metadata and len(metadata["images"]) > 0:
        # Has at least one image
        return True
    return False

def search_with_validation(name: str, retry_count: int = 0) -> dict:
    """
    Search for celebrity image with multi-source fallback and validation.

    Strategy (in order of priority):
    1. Wikipedia (FREE, high quality)
    2. Google/Bing scraping (FREE, no API key needed!)
    3. Google/Bing API (optional, requires API keys)
    4. Validate each candidate with face detection
    """
    candidates = []

    # 1. Try Wikipedia first (always free, high quality)
    print(f"  → Trying Wikipedia (free)...")
    wiki_result = search_image_wikimedia(name)
    if wiki_result:
        candidates.append(wiki_result)
        print(f"    ✓ Found Wikipedia image")

    # 2. Try free web scraping (Google + Bing - NO API KEY NEEDED!)
    print(f"  → Trying Google/Bing scraping (FREE, no API key)...")
    free_results = search_free_images(name, max_results=10)
    if free_results:
        candidates.extend(free_results)
        print(f"    ✓ Found {len(free_results)} image(s) via scraping")

    # 3. Try API-based search if enabled (OPTIONAL - requires API keys)
    if config.ENABLE_FALLBACK_SEARCH:
        print(f"  → Trying Google/Bing API (optional, requires keys)...")
        api_results = search_fallback_images_multiple(name, max_results=5)
        if api_results:
            candidates.extend(api_results)
            print(f"    ✓ Found {len(api_results)} image(s) via API")

    if not candidates:
        print(f"  ✗ No images found from any source")
        return None

    print(f"  → Validating {len(candidates)} candidate(s)...")

    # Validate each candidate
    for idx, candidate in enumerate(candidates, 1):
        url = candidate.get("url")
        if not url:
            continue

        print(f"    [{idx}/{len(candidates)}] Checking {candidate.get('source', 'unknown')}...", end=" ")

        # Basic validation
        if not validate_image(url):
            print("✗ Invalid image")
            continue

        # Face detection validation
        if FACE_DETECTION_AVAILABLE:
            validation = validate_image_with_face_detection(url)
            if validation["valid"]:
                print(f"✓ Valid! ({validation.get('num_faces', 1)} face(s))")
                return {**candidate, "validation": validation}
            else:
                reason = validation.get("reason", "unknown")
                print(f"✗ {reason}")
        else:
            print("✓ Valid (no face detection)")
            return candidate

    print(f"  ✗ No valid images after validation")
    return None

def main(force_reprocess: bool = False, only_missing: bool = True):
    """
    Main function to prepare celebrity database.

    Args:
        force_reprocess: If True, reprocess all celebrities even if they have images
        only_missing: If True, only process celebrities without images (INCREMENTAL)
    """
    celebs = load_celebrities(config.CELEBRITY_LIST)

    print("="*70)
    print("CELEBRITY FACE DATABASE PREPARATION (INCREMENTAL)")
    print("="*70)
    print(f"Total celebrities: {len(celebs)}")
    print(f"Face detection: {'ON' if FACE_DETECTION_AVAILABLE else 'OFF'}")
    print(f"Fallback search: {'ON' if config.ENABLE_FALLBACK_SEARCH else 'OFF'}")
    print(f"Mode: {'FORCE REPROCESS' if force_reprocess else 'INCREMENTAL (skip existing)'}")
    print("="*70)

    # Filter celebrities based on mode
    if not force_reprocess and only_missing:
        print("\n🔍 Checking existing metadata...")
        celebs_to_process = []
        skipped = 0

        for celeb in celebs:
            if has_valid_image(celeb["slug"]):
                skipped += 1
            else:
                celebs_to_process.append(celeb)

        print(f"✓ Found {skipped} celebrities with images (skipping)")
        print(f"→ Processing {len(celebs_to_process)} celebrities without images")
        celebs = celebs_to_process

    if len(celebs) == 0:
        print("\n✓ All celebrities already have images! Nothing to do.")
        print("  Use --force to reprocess all celebrities.")
        return

    stats = {
        "total": len(celebs),
        "success": 0,
        "failed": 0,
        "skipped": 0
    }
    start_time = time.time()

    for idx, celeb in enumerate(celebs, 1):
        name = celeb["name"]
        slug = celeb["slug"]

        print(f"\n[{idx}/{len(celebs)}] {name}")

        result = search_with_validation(name)

        if result:
            metadata = {
                "name": name,
                "slug": slug,
                "category": celeb.get("category", "auto"),
                "images": [result]
            }
            save_metadata(slug, metadata)
            print(f"  ✓ Saved: {result.get('source', 'unknown')}")
            stats["success"] += 1
        else:
            print(f"  ✗ No valid image found")
            stats["failed"] += 1

        time.sleep(config.REQUEST_DELAY)

        # Progress update every 20 celebrities
        if idx % 20 == 0:
            rate = stats["success"] / idx * 100 if idx > 0 else 0
            elapsed = time.time() - start_time
            avg_time = elapsed / idx
            remaining = (len(celebs) - idx) * avg_time

            print(f"\n{'='*70}")
            print(f"Progress: {idx}/{len(celebs)} ({rate:.1f}% success)")
            print(f"Time: {elapsed:.0f}s elapsed, ~{remaining:.0f}s remaining")
            print(f"{'='*70}")

    # Summary
    elapsed = time.time() - start_time
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total processed: {stats['total']}")
    print(f"✓ Success: {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
    print(f"✗ Failed: {stats['failed']}")
    print(f"Time: {elapsed:.1f}s ({elapsed/stats['total']:.2f}s per celebrity)")
    print(f"{'='*70}")

    # Show failed celebrities for retry
    if stats['failed'] > 0:
        print(f"\n💡 TIP: To improve success rate:")
        print(f"   1. Set up Google/Bing API keys (see README)")
        print(f"   2. Run again - script is incremental, will only retry failed ones")
        print(f"   3. Manually add images to data/metadata/<slug>.json")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Prepare celebrity face database (INCREMENTAL)")
    parser.add_argument("--force", action="store_true",
                       help="Force reprocess all celebrities (ignore existing)")
    parser.add_argument("--test", type=int, metavar="N",
                       help="Test mode: only process first N celebrities")

    args = parser.parse_args()

    # Test mode
    if args.test:
        celebs = load_celebrities(config.CELEBRITY_LIST)[:args.test]
        print(f"TEST MODE: Processing {args.test} celebrities\n")
        for i, c in enumerate(celebs, 1):
            print(f"  {i}. {c['name']}")
        input("\nPress ENTER to continue...")

        # Temporarily override config
        original_list = config.CELEBRITY_LIST
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(celebs, f)
            config.CELEBRITY_LIST = f.name

        main(force_reprocess=args.force)

        # Restore
        config.CELEBRITY_LIST = original_list
    else:
        main(force_reprocess=args.force)

