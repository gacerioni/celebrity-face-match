#!/usr/bin/env python3
"""
Re-seed the Celebrity Face Match vector DB, LOCALLY (uses this repo's .venv which
already has face_recognition + dlib). Produces data/embeddings_dump.jsonl, a durable
artifact the server loads without ever touching Wikimedia again.

- Brazilian celebs: reuse the 2600+ existing data/metadata/*.json (already have image URLs).
- US/international celebs: resolve a portrait via the Wikipedia pageimages API
  (uses an explicit `title` when the plain name is ambiguous, so we never embed a homonym).

Polite to Wikimedia: descriptive User-Agent with contact, throttle + exponential backoff on 429.
Resumable: skips any slug already present in the dump.
"""
import base64
import json
import re
import sys
import time
from io import BytesIO
from pathlib import Path

import numpy as np
import requests
import face_recognition

ROOT = Path(__file__).parent
META = ROOT / "data" / "metadata"
DUMP = ROOT / "data" / "embeddings_dump.jsonl"
US_LIST = ROOT / "data" / "celebrities_us.json"

UA = "CelebFaceMatch/2.0 (https://platformengineer.io; contact gacerioni@gmail.com) educational face-match demo"
HEADERS = {"User-Agent": UA}
DELAY = 0.30          # base politeness delay between network calls
DOWNLOAD_RETRIES = 4  # attempts, with exponential backoff on 429


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower())
    return slug.strip("_")


def wiki_image(title: str):
    """Resolve the lead portrait image URL for a Wikipedia article title."""
    for api in ("https://en.wikipedia.org/w/api.php", "https://pt.wikipedia.org/w/api.php"):
        try:
            r = requests.get(
                api,
                params={"action": "query", "format": "json",
                        "prop": "pageimages", "piprop": "original", "titles": title},
                headers=HEADERS, timeout=12,
            )
            r.raise_for_status()
            for p in r.json().get("query", {}).get("pages", {}).values():
                if "original" in p:
                    src = "wikimedia-en" if "en.wiki" in api else "wikimedia-pt"
                    return p["original"]["source"], src
        except Exception:
            pass
        time.sleep(DELAY)
    return None, None


def download(url: str):
    for attempt in range(DOWNLOAD_RETRIES):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 429:
                time.sleep(2 ** attempt + 1)
                continue
            r.raise_for_status()
            return r.content
        except requests.HTTPError as e:
            code = e.response.status_code if e.response is not None else 0
            if code == 429:
                time.sleep(2 ** attempt + 1)
                continue
            return None  # 404 / 403 / stale -> skip
        except Exception:
            return None
    return None


def embed(content: bytes):
    try:
        img = face_recognition.load_image_file(BytesIO(content))
        encs = face_recognition.face_encodings(img)
        if encs:
            return encs[0].astype(np.float32)
    except Exception:
        pass
    return None


def load_done():
    done = set()
    if DUMP.exists():
        with open(DUMP) as f:
            for line in f:
                try:
                    done.add(json.loads(line)["slug"])
                except Exception:
                    pass
    return done


def append_dump(rec: dict):
    with open(DUMP, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def br_celebs():
    out = []
    for jf in sorted(META.glob("*.json")):
        try:
            d = json.load(open(jf, encoding="utf-8"))
            if d.get("images"):
                img = d["images"][0]
                out.append({"name": d["name"], "slug": d.get("slug", slugify(d["name"])),
                            "category": d.get("category", "auto"),
                            "url": img["url"], "source": img.get("source", "wikimedia")})
        except Exception:
            pass
    return out


def us_celebs():
    if not US_LIST.exists():
        return []
    out = []
    for item in json.load(open(US_LIST, encoding="utf-8")):
        name = item["name"]
        slug = slugify(name)
        cat = item.get("category", "international")
        mpath = META / f"{slug}.json"
        if mpath.exists():
            d = json.load(open(mpath, encoding="utf-8"))
            if d.get("images"):
                img = d["images"][0]
                out.append({"name": name, "slug": slug, "category": cat,
                            "url": img["url"], "source": img.get("source", "wikimedia")})
                continue
        url, src = wiki_image(item.get("title", name))
        if not url:
            print(f"  [US] no wiki image for {name}", flush=True)
            continue
        json.dump({"name": name, "slug": slug, "category": cat,
                   "images": [{"url": url, "source": src}]},
                  open(mpath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        out.append({"name": name, "slug": slug, "category": cat, "url": url, "source": src})
    return out


def main():
    done = load_done()
    print("Resolving US/international portraits via Wikipedia...", flush=True)
    celebs = br_celebs() + us_celebs()

    seen, uniq = set(), []
    for c in celebs:
        if c["slug"] in seen:
            continue
        seen.add(c["slug"])
        uniq.append(c)

    todo = [c for c in uniq if c["slug"] not in done]
    print(f"Total {len(uniq)} celebs | {len(done)} already dumped | {len(todo)} to process", flush=True)

    ok = fail = recovered = 0
    for i, c in enumerate(todo, 1):
        url = c["url"]
        content = download(url)
        emb = embed(content) if content else None

        # Recovery: if the (possibly stale/blocked) URL yields no face, try a
        # fresh portrait straight from Wikipedia's pageimages API.
        if emb is None:
            fresh, src = wiki_image(c.get("title") or c["name"])
            if fresh and fresh != url:
                content = download(fresh)
                e2 = embed(content) if content else None
                if e2 is not None:
                    emb, url, c["source"] = e2, fresh, src
                    recovered += 1

        if emb is not None:
            append_dump({"slug": c["slug"], "name": c["name"], "category": c["category"],
                         "source": c["source"], "image_url": url,
                         "embedding": base64.b64encode(emb.tobytes()).decode()})
            ok += 1
            tag = "OK"
        else:
            fail += 1
            tag = "FAIL"
        if i % 25 == 0 or tag == "FAIL":
            print(f"[{i}/{len(todo)}] {c['name']}: {tag}  (ok={ok} fail={fail})", flush=True)
        time.sleep(DELAY)

    print(f"DONE: ok={ok} (recovered={recovered}) fail={fail} total_in_dump={ok + len(done)}", flush=True)


if __name__ == "__main__":
    main()
