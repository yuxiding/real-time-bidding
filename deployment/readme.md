# Deployment Overview

This folder contains example deployment resources for serving the AuroraBid bidding engine via APIs and monitoring its performance.

## Folder Structure

```
deployment/
├── Dockerfile              # Image definition for containerized deployment
├── start_server.sh         # Shell script to launch FastAPI app
├── gunicorn_conf.py        # Gunicorn config for production serving
├── k8s.yaml                # Kubernetes deployment example (optional)
```

## Deployment Modes

### 1. Local (Dev Mode)
```bash
uvicorn src.serving.api:app --reload --port 8000
```

### 2. Docker (Recommended)
```bash
docker build -t aurora-bid .
docker run -p 8000:8000 aurora-bid
```

### 3. Production (Gunicorn)
```bash
./start_server.sh
```

### 4. Kubernetes (Optional)
Apply `k8s.yaml` to deploy via `kubectl` or `helm`.

---

Logs, latency, and metrics are monitored via `logger.py` and `latency_monitor.py`.
For stress testing and live traffic, use endpoints:
- `/bid`: realtime bidding
- `/health`: readiness probe
