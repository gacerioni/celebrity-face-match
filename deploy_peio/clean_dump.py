#!/usr/bin/env python3
"""Dedup the raw embeddings dump into the clean seed the server loads.
Collapses identical-image clusters (L2 < 0.05) to one representative and drops
junk non-person article names. data/embeddings_dump.jsonl -> data/celeb_dump_clean.jsonl."""
import base64
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parent.parent
SRC = ROOT / "data" / "embeddings_dump.jsonl"
DST = ROOT / "data" / "celeb_dump_clean.jsonl"
JUNK = re.compile(r'^(discografia|discography)\b|\((álbum|album|filme|film|canção|single|banda|EP|turnê)\)', re.I)

recs = []
for line in open(SRC):
    try:
        d = json.loads(line)
    except Exception:
        continue
    d["_v"] = np.frombuffer(base64.b64decode(d["embedding"]), dtype=np.float32).astype(np.float64)
    recs.append(d)

n = len(recs)
X = np.vstack([r["_v"] for r in recs])
names = [r["name"] for r in recs]

sq = (X * X).sum(1)
D2 = sq[:, None] + sq[None, :] - 2 * X @ X.T
np.fill_diagonal(D2, 1e9)
L2 = np.sqrt(np.clip(D2, 0, None))

parent = list(range(n))
def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a
for i, j in np.argwhere(np.triu(L2 < 0.05, 1)):
    parent[find(int(i))] = find(int(j))

clusters = defaultdict(list)
for i in range(n):
    clusters[find(i)].append(i)

keep, dup, junk = set(), 0, 0
for idxs in clusters.values():
    cand = [i for i in idxs if not JUNK.search(names[i])]
    if not cand:
        junk += len(idxs)
        continue
    winner = min(cand, key=lambda i: (len(names[i]), names[i]))
    keep.add(winner)
    dup += len(idxs) - 1
    junk += len(idxs) - len(cand)
for i in list(keep):
    if JUNK.search(names[i]):
        keep.discard(i)
        junk += 1

kept = sorted(keep)
with open(DST, "w") as f:
    for i in kept:
        r = recs[i]
        f.write(json.dumps({k: r[k] for k in ("slug", "name", "category", "source", "image_url", "embedding")},
                           ensure_ascii=False) + "\n")
print(f"{n} -> {len(kept)} faces (dropped dup={dup} junk={junk}) -> {DST.name}")
