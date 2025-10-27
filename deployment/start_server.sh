#!/bin/bash

# Run Gunicorn with 4 workers, using Uvicorn worker class
exec gunicorn src.serving.api:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 60 \
  --log-level info \
  --config deployment/gunicorn_conf.py
