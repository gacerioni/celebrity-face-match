#!/usr/bin/env python3
"""
Load embeddings_dump.jsonl into Redis and (re)create the celeb_faces_idx vector index.
Runs on the server (only needs redis-py, no dlib / no Wikimedia). Idempotent.

Env:
  DUMP              path to the jsonl dump           (default /data/embeddings_dump.jsonl)
  REDIS_URI         redis connection                 (default redis://127.0.0.1:6379)
  REDIS_INDEX_NAME  vector index name                (default celeb_faces_idx)
  REDIS_KEY_PREFIX  hash key prefix                  (default celeb)
"""
import base64
import json
import os

import redis
from redis.commands.search.field import TextField, TagField, VectorField
try:
    from redis.commands.search.index_definition import IndexDefinition, IndexType
except (ImportError, ModuleNotFoundError):
    from redis.commands.search.indexDefinition import IndexDefinition, IndexType

DUMP = os.getenv("DUMP", "/data/embeddings_dump.jsonl")
URI = os.getenv("REDIS_URI", "redis://127.0.0.1:6379")
IDX = os.getenv("REDIS_INDEX_NAME", "celeb_faces_idx")
PFX = os.getenv("REDIS_KEY_PREFIX", "celeb")

r = redis.from_url(URI, decode_responses=False)
r.ping()

# Clean slate: drop the index and any existing celeb:* keys so reloads are deterministic.
try:
    r.ft(IDX).dropindex()
    print(f"dropped existing index {IDX}")
except Exception:
    pass
cur = 0
deleted = 0
while True:
    cur, keys = r.scan(cur, match=f"{PFX}:*", count=1000)
    if keys:
        r.delete(*keys)
        deleted += len(keys)
    if cur == 0:
        break
if deleted:
    print(f"cleared {deleted} old {PFX}:* keys")

schema = (
    TextField("name"),
    TextField("slug"),
    TagField("category"),
    TextField("source"),
    # L2 (Euclidean) is the metric dlib/face_recognition embeddings are trained
    # for; COSINE piled distinct faces into a narrow 0.93+ band and mis-ranked
    # ~24% of top matches.
    VectorField("embedding", "FLAT",
                {"TYPE": "FLOAT32", "DIM": 128, "DISTANCE_METRIC": "L2"}),
)
r.ft(IDX).create_index(
    schema, definition=IndexDefinition(prefix=[f"{PFX}:"], index_type=IndexType.HASH)
)
print(f"created index {IDX}")

n = 0
with open(DUMP) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue  # tolerate a partial final line if the dump is still being written
        r.hset(f"{PFX}:{d['slug']}", mapping={
            "name": d["name"],
            "slug": d["slug"],
            "category": d.get("category", "unknown"),
            "source": d.get("source", "unknown"),
            "image_url": d.get("image_url", ""),
            "embedding": base64.b64decode(d["embedding"]),
        })
        n += 1

info = r.ft(IDX).info()
num_docs = info.get("num_docs") if isinstance(info, dict) else \
    dict(zip(info[::2], info[1::2])).get(b"num_docs")
print(f"loaded {n} celebs; index num_docs={num_docs}")
