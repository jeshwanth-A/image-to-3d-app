#!/bin/bash

# Start FastAPI server in the background
cd /app
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
# Store the process ID to check if it's running
BACKEND_PID=$!

# Wait briefly and check if backend started successfully
sleep 2
if ! ps -p $BACKEND_PID > /dev/null; then
  echo "Backend failed to start properly"
  exit 1
fi

# Replace PORT in nginx config
export PORT="${PORT:-8080}"
sed -i "s/\${PORT}/$PORT/g" /etc/nginx/conf.d/default.conf

# Start nginx in foreground
nginx -g "daemon off;"
