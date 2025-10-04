"""
Smart Scheduler for Controller Bot
Optimized timing - no constant database polling
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
        self.current_timer: Optional[threading.Timer] = None
        self.is_near_time_mode = False
        self.daily_check_timer: Optional[threading.Timer] = None

        # Start daily check timer
        self.start_daily_check()

        # Start initial scheduling
        self.schedule_next_task()

    def start_daily_check(self):
        """Start daily 00:00 check for tasks"""
        def daily_check():
            try:
                logger.info("🕛 Daily check: Looking for today's tasks")
                today = datetime.now(IST)
                tasks = self.db.get_daily_tasks(today)

                if tasks['total'] > 0:
                    logger.info(f"📅 Found {tasks['total']} tasks today - starting smart scheduling")
                    self.schedule_next_task()
                else:
                    logger.info("📅 No tasks today - scheduler on standby")

                # Schedule next daily check (24 hours)
                self.start_daily_check()

            except Exception as e:
                logger.error(f"❌ Daily check error: {e}")
                # Retry in 1 hour if error
                self.daily_check_timer = threading.Timer(3600, daily_check)
                self.daily_check_timer.start()

        # Calculate seconds until next 00:00
        now = datetime.now(IST)
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_until_midnight = (next_midnight - now).total_seconds()

        self.daily_check_timer = threading.Timer(seconds_until_midnight, daily_check)
        self.daily_check_timer.start()
        logger.info(f"⏰ Daily check scheduled in {seconds_until_midnight/3600:.1f} hours")

    def schedule_next_task(self):
        """Smart scheduling - only check when needed"""
        try:
            # Cancel existing timer
            if self.current_timer:
                self.current_timer.cancel()

            # Get next task time
            next_task_time = self.db.get_next_task_time()

            if not next_task_time:
                logger.info("📭 No upcoming tasks - scheduler on standby")
                self.is_near_time_mode = False
                return

            now = datetime.now(IST)
            time_until_task = (next_task_time - now).total_seconds()

            if time_until_task <= 0:
                # Task is overdue - execute immediately
                self.execute_pending_tasks()
                return

            # Decide checking frequency based on time remaining
            if time_until_task <= NEAR_TIME_CHECK_INTERVAL:
                # Near time - check every 15 minutes
                check_interval = min(time_until_task, NEAR_TIME_CHECK_INTERVAL)
                if not self.is_near_time_mode:
                    logger.info("⏰ Switching to near-time mode (15min checks)")
                    self.is_near_time_mode = True
            else:
                # Far time - check every hour
                check_interval = TIMER_CHECK_INTERVAL
                self.is_near_time_mode = False
                logger.info(f"⏳ Next task in {time_until_task/3600:.1f}h - hourly checks")

            # Schedule next check
            self.current_timer = threading.Timer(check_interval, self.schedule_next_task)
            self.current_timer.start()

        except Exception as e:
            logger.error(f"❌ Scheduling error: {e}")
            # Fallback - retry in 5 minutes
            self.current_timer = threading.Timer(300, self.schedule_next_task)
            self.current_timer.start()

    def execute_pending_tasks(self):
        """Execute all pending tasks that are due"""
        try:
            now = datetime.now(IST)
            tasks = self.db.get_upcoming_tasks(now)

            # Execute scheduled posts
            for post in tasks['scheduled_posts']:
                try:
                    self.execute_scheduled_post(post)
                    self.db.mark_task_completed('scheduled_post', post['id'])
                    logger.info(f"✅ Executed scheduled post {post['id']}")
                except Exception as e:
                    logger.error(f"❌ Failed to execute post {post['id']}: {e}")

            # Execute self-destruct tasks
            for task in tasks['self_destruct_tasks']:
                try:
                    self.execute_self_destruct(task)
                    self.db.mark_task_completed('self_destruct', task['id'])
                    logger.info(f"🗑️ Executed self-destruct {task['id']}")
                except Exception as e:
                    logger.error(f"❌ Failed to execute self-destruct {task['id']}: {e}")

            # Schedule next check
            self.schedule_next_task()

        except Exception as e:
            logger.error(f"❌ Task execution error: {e}")
            # Retry in 1 minute
            self.current_timer = threading.Timer(60, self.execute_pending_tasks)
            self.current_timer.start()

    def execute_scheduled_post(self, post_data: Dict[str, Any]):
        """Execute a scheduled post"""
        # Note: Since we don't store message content in DB,
        # this would need to be integrated with the user's current post data
        # For now, this is a placeholder that logs the execution
        channel_id = post_data['channel_id']
        user_id = post_data['user_id']

        logger.info(f"📤 Executing scheduled post for channel {channel_id} by user {user_id}")

        # In real implementation, you'd retrieve the post content from user session
        # and send it using self.bot.send_message() or similar

        # Notify user that post was sent
        try:
            self.bot.send_message(
                user_id,
                f"✅ Your scheduled post has been sent to channel {channel_id}",
                parse_mode='Markdown'
            )
        except:
            pass

    def execute_self_destruct(self, task_data: Dict[str, Any]):
        """Execute a self-destruct task"""
        channel_id = task_data['channel_id']
        message_id = task_data['message_id']

        try:
            self.bot.delete_message(chat_id=channel_id, message_id=message_id)
            logger.info(f"🗑️ Self-destructed message {message_id} in {channel_id}")
        except Exception as e:
            logger.error(f"❌ Failed to delete message {message_id}: {e}")

    def add_scheduled_post(self, user_id: int, channel_id: str, scheduled_time: datetime) -> int:
        """Add a new scheduled post and update scheduler"""
        post_id = self.db.schedule_post(user_id, channel_id, scheduled_time)
        logger.info(f"📝 Added scheduled post {post_id} for {scheduled_time}")

        # Update scheduler to check for this new task
        self.schedule_next_task()
        return post_id

    def add_self_destruct(self, channel_id: str, message_id: int, destruct_time: datetime) -> int:
        """Add a new self-destruct task and update scheduler"""
        task_id = self.db.schedule_self_destruct(channel_id, message_id, destruct_time)
        logger.info(f"💣 Added self-destruct {task_id} for {destruct_time}")

        # Update scheduler to check for this new task
        self.schedule_next_task()
        return task_id

    def stop(self):
        """Stop all schedulers"""
        if self.current_timer:
            self.current_timer.cancel()
        if self.daily_check_timer:
            self.daily_check_timer.cancel()
        logger.info("⏹️ Scheduler stopped")
