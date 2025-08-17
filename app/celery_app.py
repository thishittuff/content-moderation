from celery import Celery
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery instance
celery_app = Celery(
    "content_moderation",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    beat_schedule={
        "cleanup-old-results": {
            "task": "app.tasks.cleanup_old_results",
            "schedule": 3600.0,  # Every hour
        },
    }
)


@celery_app.task(bind=True)
def cleanup_old_results(self):
    """Clean up old moderation results and requests"""
    try:
        logger.info("Starting cleanup of old moderation results")
        # This would be implemented to clean up old data
        # For now, just log the task
        logger.info("Cleanup task completed successfully")
        return {"status": "success", "message": "Cleanup completed"}
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True)
def process_image_moderation(self, image_data: str, email_id: str):
    """Background task for processing image moderation"""
    try:
        logger.info(f"Processing image moderation for {email_id}")
        # This would integrate with the moderation service
        # For now, just log the task
        logger.info("Image moderation task completed successfully")
        return {"status": "success", "email_id": email_id}
    except Exception as e:
        logger.error(f"Image moderation task failed: {e}")
        self.retry(countdown=60, max_retries=3)


if __name__ == "__main__":
    celery_app.start()
