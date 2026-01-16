"""
Merge the original curated celebrity list with the generated Wikipedia list.
Removes duplicates and creates a comprehensive combined list.
"""
import json
import re

def slugify(name: str) -> str:
    """Convert name to slug for comparison"""
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")

def normalize_name(name: str) -> str:
    """Normalize name for better duplicate detection"""
    # Remove common suffixes and prefixes
    name = name.strip()
    # Remove disambiguation
    if "(" in name:
        name = name.split("(")[0].strip()
    return name

def merge_lists(
    original_file: str = "data/celebrities_seed.json",
    generated_file: str = "data/celebrities_generated.json",
    output_file: str = "data/celebrities_combined.json"
):
    """
    Merge two celebrity lists, removing duplicates.
    """
    # Load both files
    with open(original_file, 'r', encoding='utf-8') as f:
        original = json.load(f)
    
    with open(generated_file, 'r', encoding='utf-8') as f:
        generated = json.load(f)
    
    # Track unique celebrities by normalized name
    seen_slugs = set()
    combined = []
    
    # Add original list first (these are curated, so they take priority)
    for celeb in original:
        name = celeb["name"]
        slug = slugify(normalize_name(name))
        
        if slug not in seen_slugs:
            seen_slugs.add(slug)
            combined.append({
                "name": name,
                "category": celeb.get("category", "auto"),
                "source": "curated"
            })
    
    original_count = len(combined)
    
    # Add generated list, skipping duplicates
    for celeb in generated:
        name = normalize_name(celeb["name"])
        slug = slugify(name)
        
        if slug not in seen_slugs:
            seen_slugs.add(slug)
            combined.append({
                "name": name,
                "category": celeb.get("category", "auto"),
                "source": "wikipedia"
            })
    
    # Sort by name
    combined.sort(key=lambda x: x["name"])
    
    # Save combined list
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined, f, indent=4, ensure_ascii=False)
    
    # Print summary
    print(f"{'='*60}")
    print(f"Celebrity List Merge Summary:")
    print(f"  Original curated list: {original_count}")
    print(f"  Generated from Wikipedia: {len(generated)}")
    print(f"  Duplicates removed: {original_count + len(generated) - len(combined)}")
    print(f"  Total unique celebrities: {len(combined)}")
    print(f"\nSaved to: {output_file}")
    print(f"{'='*60}")
    
    return combined

if __name__ == "__main__":
    merge_lists()

