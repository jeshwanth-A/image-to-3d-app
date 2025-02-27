import os
import logging
import traceback
from main import app, setup_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create scheduler when running with Gunicorn
scheduler = None

try:
    # Get worker ID
    worker_id = os.environ.get("GUNICORN_WORKER_ID", "0")
    
    # Only start scheduler on first worker
    if worker_id == "0" or worker_id == 0:
        logger.info("Starting scheduler in worker 0")
        scheduler = setup_scheduler()
        if scheduler:
            try:
                scheduler.start()
                logger.info("Scheduler started in worker 0")
            except Exception as e:
                logger.error(f"Failed to start scheduler: {e}")
                logger.error(traceback.format_exc())
except Exception as e:
    logger.error(f"Error setting up scheduler in wsgi.py: {e}")
    logger.error(traceback.format_exc())

# Provide app for Gunicorn
application = app

if __name__ == "__main__":
    application.run()
