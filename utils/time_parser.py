"""
Time parsing utilities for Controller Bot
"""
import re
from datetime import datetime, timedelta
from typing import Optional
from config import IST

TIME_FORMAT_HELP = """**⏰ Time Format Guide:**

**Full Format:** dd/mm hh:mm (e.g., 5/10 15:00)
**Time Only:** hh:mm (e.g., 15:00)

All times in IST timezone."""

def parse_time_input(time_str: str) -> Optional[datetime]:
    if not time_str or not isinstance(time_str, str):
        return None

    time_str = time_str.strip()
    current_time = datetime.now(IST)

    # Pattern: dd/mm hh:mm
    pattern1 = r"^(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2})$"
    match1 = re.match(pattern1, time_str)

    if match1:
        day = int(match1.group(1))
        month = int(match1.group(2))
        hour = int(match1.group(3))
        minute = int(match1.group(4))

        if not (1 <= day <= 31 and 1 <= month <= 12 and 0 <= hour <= 23 and 0 <= minute <= 59):
            return None

        try:
            target_time = current_time.replace(
                month=month, day=day, hour=hour, minute=minute, 
                second=0, microsecond=0
            )

            if target_time < current_time:
                target_time = target_time.replace(year=target_time.year + 1)

            return target_time
        except ValueError:
            return None

    # Pattern: hh:mm
    pattern2 = r"^(\d{1,2}):(\d{2})$"
    match2 = re.match(pattern2, time_str)

    if match2:
        hour = int(match2.group(1))
        minute = int(match2.group(2))

        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return None

        target_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if target_time <= current_time:
            target_time += timedelta(days=1)

        return target_time

    return None

def format_time_display(dt: datetime) -> str:
    return dt.strftime('%d/%m/%Y %H:%M IST')
