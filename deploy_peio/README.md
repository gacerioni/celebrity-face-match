# Deploy — celeb.platformengineer.io

How this demo runs in production, on the shared `gabs-demos` VM behind Caddy.

## Architecture

```
browser (webcam)
   │  wss://celeb.platformengineer.io/ws
   ▼
Caddy (TLS, single ingress)
   ├── /ws, /api/*  →  celeb-backend  (FastAPI, 127.0.0.1:8070)
   └── /*           →  celeb-frontend (nginx SPA, 127.0.0.1:3090)
                              │
                        celeb-redis (Redis 8, vector search)
```

Every container binds to loopback only; Caddy is the sole public ingress.

## Seed (2-step, Wikimedia-free at deploy time)

Face embedding is done **once, locally** (this repo's `.venv` has `face_recognition`/dlib)
and captured in a durable dump, so the server never scrapes Wikimedia:

```bash
# 1. Embed locally -> data/embeddings_dump.jsonl  (Brazilian metadata + US list)
.venv/bin/python reseed_local.py

# 2. On the VM, load the dump into celeb-redis + build the index (redis-py only)
DUMP=/data/embeddings_dump.jsonl REDIS_URI=redis://celeb-redis:6379 python load_dump.py
```

- Brazilian celebrities come from `data/metadata/*.json` (Wikimedia portrait URLs).
- US / international names live in `data/celebrities_us.json`; `reseed_local.py` resolves
  each portrait via the Wikipedia `pageimages` API (uses an explicit `title` for homonyms).
- The dump (`data/embeddings_dump.jsonl`, base64 float32) is git-ignored; regenerate it,
  or keep a copy, for an instant no-Wikimedia restore.

## Bring the stack up

```bash
# frontend image bakes the WS URL at build time
docker build --build-arg VITE_WS_URL=wss://celeb.platformengineer.io/ws \
  -t celeb-frontend:peio frontend

docker compose -f deploy_peio/docker-compose.celeb.yml up -d

# load seed into celeb-redis (see step 2 above), then:
sudo python3 deploy_peio/fix_caddy_celeb.py deploy_peio/celeb_block.caddy
sudo systemctl reload caddy
```

## Files

| File | Purpose |
|---|---|
| `docker-compose.celeb.yml` | celeb-redis + celeb-backend (:8070) + celeb-frontend (:3090) |
| `celeb_block.caddy` | Caddy site block (WS + API → backend, rest → SPA) |
| `fix_caddy_celeb.py` | idempotently replace the site block in `/etc/caddy/Caddyfile` |
