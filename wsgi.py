import os
import logging
from main import app, setup_scheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create scheduler when running with Gunicorn
scheduler = None

# Get worker ID
worker_id = os.environ.get("GUNICORN_WORKER_ID", "0")

# Only start scheduler on first worker
if worker_id == "0" or worker_id == 0:
    scheduler = setup_scheduler()
    if scheduler:
        try:
            scheduler.start()
            logger.info("Scheduler started in worker 0")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")

# Provide app for Gunicorn
application = app

if __name__ == "__main__":
    application.run()
