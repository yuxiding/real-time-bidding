# gunicorn_conf.py

bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 60
keepalive = 5
loglevel = "info"
accesslog = "-"  # log to stdout
errorlog = "-"   # log to stderr
