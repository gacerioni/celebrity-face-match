# Legacy Gradio Demos

These are the original Gradio-based demos, replaced by the modern React frontend.

**Note:** The modern React + FastAPI version is recommended for production use.

---

## Legacy Demos

### 1. Static Upload Demo (`app.py`)

```bash
python legacy/app.py
```

- Upload photos or webcam snapshot
- Shows top 5 matches
- Gradio interface

### 2. Live Webcam Demo (`app_live.py`)

```bash
python legacy/app_live.py
```

- Real-time webcam face matching
- Gradio interface with live updates

### 3. Demo Launcher (`launch_demo.py`)

```bash
python legacy/launch_demo.py
```

Interactive menu to launch any legacy demo.

### 4. Modern Demo Launcher (`start_modern_demo.sh`)

```bash
./legacy/start_modern_demo.sh
```

Legacy script for launching the modern React demo.

**Note:** Use `./run.sh` in the root directory instead.

---

## Why Legacy?

These demos were replaced with a modern React + FastAPI architecture that provides:

- ✅ Better performance (WebSocket vs polling)
- ✅ Modern UI/UX (TailwindCSS)
- ✅ Production-ready (Docker, HTTPS)
- ✅ Mobile responsive
- ✅ Real-time updates

---

## Migration

To use the modern version:

```bash
# From root directory
./run.sh
```

See [../docs/DEVELOPMENT.md](../docs/DEVELOPMENT.md) for details.

