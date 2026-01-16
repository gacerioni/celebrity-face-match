#!/usr/bin/env python3
"""
Check status of celebrity database preparation.
Shows which celebrities have images and which are missing.
"""
from modules.celeb_list import load_celebrities
from pathlib import Path
import config
import json

def main():
    celebs = load_celebrities(config.CELEBRITY_LIST)
    metadata_path = Path(config.METADATA_PATH)
    
    print("="*70)
    print("CELEBRITY DATABASE STATUS")
    print("="*70)
    
    with_images = []
    without_images = []
    
    for celeb in celebs:
        slug = celeb["slug"]
        metadata_file = metadata_path / f"{slug}.json"
        
        if metadata_file.exists():
            # Check if has images
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get("images") and len(data["images"]) > 0:
                    with_images.append(celeb)
                else:
                    without_images.append(celeb)
        else:
            without_images.append(celeb)
    
    total = len(celebs)
    success_count = len(with_images)
    missing_count = len(without_images)
    success_rate = (success_count / total * 100) if total > 0 else 0
    
    print(f"Total celebrities: {total}")
    print(f"✓ With images: {success_count} ({success_rate:.1f}%)")
    print(f"✗ Missing images: {missing_count} ({100-success_rate:.1f}%)")
    print("="*70)
    
    if missing_count > 0:
        print(f"\n📋 Missing celebrities (showing first 20):")
        for i, celeb in enumerate(without_images[:20], 1):
            print(f"  {i}. {celeb['name']} ({celeb.get('category', 'unknown')})")
        
        if missing_count > 20:
            print(f"  ... and {missing_count - 20} more")
        
        print(f"\n💡 Run 'python prepare_database.py' to fetch missing images")
    else:
        print(f"\n✓ All celebrities have images! Database is complete.")
    
    print("="*70)
    
    # Category breakdown
    print(f"\n📊 Breakdown by category:")
    categories = {}
    for celeb in with_images:
        cat = celeb.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: {count}")

if __name__ == "__main__":
    main()

