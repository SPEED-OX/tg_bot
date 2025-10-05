"""
Smart scheduler for Controller Bot
"""
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
from database.models import DatabaseManager
from config import IST, TIMER_CHECK_INTERVAL, NEAR_TIME_CHECK_INTERVAL, DAILY_CHECK_TIME

logger = logging.getLogger(__name__)

class SmartScheduler:
    def __init__(self, bot, db: DatabaseManager):
        self.bot = bot
        self.db = db
        self.timer: Optional[threading.Timer] = None
        self.is_running = False
        self.start()

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.schedule_next_check()
            logger.info("Smart scheduler started")

    def stop(self):
        self.is_running = False
        if self.timer:
            self.timer.cancel()
        logger.info("Smart scheduler stopped")

    def schedule_next_check(self):
        if not self.is_running:
            return

        interval = TIMER_CHECK_INTERVAL
        self.timer = threading.Timer(interval, self.check_and_execute_tasks)
        self.timer.daemon = True
        self.timer.start()

    def check_and_execute_tasks(self):
        if not self.is_running:
            return

        try:
            current_time = datetime.now(IST)
            logger.info(f"Checking for tasks at: {current_time}")

        except Exception as e:
            logger.error(f"Error during task check: {e}")
        finally:
            self.schedule_next_check()

    def add_scheduled_post(self, user_id: int, channel_id: str, scheduled_time: datetime) -> int:
        try:
            post_id = self.db.schedule_post(user_id, channel_id, scheduled_time)
            logger.info(f"Scheduled post added: ID {post_id}")
            return post_id
        except Exception as e:
            logger.error(f"Error adding scheduled post: {e}")
            raise
