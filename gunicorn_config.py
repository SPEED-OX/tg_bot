"""
Gunicorn configuration for Railway deployment
Optimized for running both bot and webapp together
"""
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', 5000)}"
backlog = 2048

# Worker processes
workers = int(os.getenv('GUNICORN_WORKERS', 2))
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "chataudit-bot-webapp"

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# Preload app for better performance
preload_app = True

# Keep alive settings for Railway
worker_tmp_dir = "/dev/shm"
