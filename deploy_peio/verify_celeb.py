#!/usr/bin/env python3
"""Sanity-check the celeb vector index: query with a stored embedding and confirm
the same celebrity comes back as the closest match (score ~0). Proves the whole
match pipeline (index + KNN + cosine) end to end, without needing a webcam."""
import os
import redis
from redis.commands.search.query import Query

r = redis.from_url(os.getenv("REDIS_URI", "redis://celeb-redis:6379"), decode_responses=False)
IDX = os.getenv("REDIS_INDEX_NAME", "celeb_faces_idx")

info = r.ft(IDX).info()
num = info.get("num_docs") if isinstance(info, dict) else dict(zip(info[::2], info[1::2])).get(b"num_docs")
print(f"index {IDX}: num_docs={num}")

_, keys = r.scan(0, match="celeb:*", count=200)
probe = keys[len(keys) // 2]  # some arbitrary celeb
h = r.hgetall(probe)
name = h[b"name"].decode()
emb = h[b"embedding"]

q = (Query("*=>[KNN 3 @embedding $v AS score]")
     .return_fields("name", "category", "score").sort_by("score").dialect(2))
res = r.ft(IDX).search(q, query_params={"v": emb})

print(f'query = "{name}"  -> top 3:')
for d in res.docs:
    nm = d.name.decode() if isinstance(d.name, bytes) else d.name
    print(f'   {nm:<28} score={float(d.score):.4f}')
top = res.docs[0].name.decode() if isinstance(res.docs[0].name, bytes) else res.docs[0].name
print("SELF-MATCH OK" if top == name else "SELF-MATCH MISMATCH")
