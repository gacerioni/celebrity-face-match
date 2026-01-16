import json, re

def slugify(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")

def load_celebrities(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    celebs = []
    for item in data:
        celebs.append({
            "name": item["name"],
            "slug": slugify(item["name"]),
            "category": item.get("category", "unknown")
        })
    return celebs
