import json, os

def save_metadata(slug: str, metadata: dict, base_path="data/metadata"):
    os.makedirs(base_path, exist_ok=True)
    with open(f"{base_path}/{slug}.json","w",encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)
