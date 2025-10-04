"""
Time parsing utilities for Controller Bot
Supports IST timezone and dd/mm hh:mm format
"""
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple
from config import IST

def parse_time_input(time_str: str) -> Optional[datetime]:
    """
    Parse user time input in format:
    - dd/mm hh:mm (5/10 15:00)
    - hh:mm (15:00) - defaults to today

    Returns datetime in IST timezone
    """
    time_str = time_str.strip()

    # Pattern for dd/mm hh:mm
    full_pattern = r'^(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2})$'
    # Pattern for hh:mm
    time_pattern = r'^(\d{1,2}):(\d{2})$'

    now = datetime.now(IST)

    # Try full format first (dd/mm hh:mm)
    match = re.match(full_pattern, time_str)
    if match:
        day, month, hour, minute = map(int, match.groups())

        # Validate inputs
        if not (1 <= day <= 31 and 1 <= month <= 12 and 0 <= hour <= 23 and 0 <= minute <= 59):
            return None

        try:
            # Use current year
            target_time = datetime(now.year, month, day, hour, minute, tzinfo=IST)

            # If date is in the past, assume next year
            if target_time < now:
                target_time = target_time.replace(year=now.year + 1)

            return target_time
        except ValueError:
            return None

    # Try time only format (hh:mm)
    match = re.match(time_pattern, time_str)
    if match:
        hour, minute = map(int, match.groups())

        # Validate time
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return None

        # Use today's date
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If time is in the past today, assume tomorrow
        if target_time <= now:
            target_time += timedelta(days=1)

        return target_time

    return None

def format_time_display(dt: datetime) -> str:
    """Format datetime for display to user"""
    return dt.strftime("%d/%m/%Y %H:%M IST")

def time_until_display(target_time: datetime) -> str:
    """Show human-readable time until target"""
    now = datetime.now(IST)
    diff = target_time - now

    if diff.days > 0:
        return f"{diff.days} days, {diff.seconds//3600} hours"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minutes"
    else:
        return "less than a minute"

def validate_future_time(dt: datetime, min_delay_minutes: int = 1) -> bool:
    """Check if datetime is far enough in the future"""
    now = datetime.now(IST)
    min_time = now + timedelta(minutes=min_delay_minutes)
    return dt > min_time

# Example usage and format hints for users
TIME_FORMAT_HELP = """
⏰ **Time Format Examples:**

**Full format (with date):**
• `5/10 15:00` - Oct 5th at 3:00 PM
• `25/12 09:30` - Dec 25th at 9:30 AM

**Time only (today/tomorrow):**
• `15:00` - Today at 3:00 PM (or tomorrow if past)
• `09:30` - Today at 9:30 AM (or tomorrow if past)

**Notes:**
• All times are in IST (Indian Standard Time)
• Use 24-hour format (00:00 to 23:59)
• If date is not specified, assumes today or tomorrow
"""
