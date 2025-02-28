import multiprocessing

# Bind to 0.0.0.0:5000
bind = "0.0.0.0:5000"

# Number of worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"

# Timeout in seconds
timeout = 120

# Log settings
loglevel = "info"
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr

# Enable threading
threads = 2

# Max requests per worker before restart
max_requests = 1000
max_requests_jitter = 50

# Preload app to improve performance
preload_app = True

# Process naming
proc_name = "image-to-3d-app"
