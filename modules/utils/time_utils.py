"""
Time Utilities
Helper functions for timestamp formatting and time calculations
"""

from datetime import datetime, timedelta
from typing import Optional, Union


def get_timestamp(format_string: str = "%Y%m%d_%H%M%S") -> str:
    """
    Get current timestamp as formatted string

    Args:
        format_string: strftime format string

    Returns:
        Formatted timestamp string
    """
    return datetime.now().strftime(format_string)


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "2h 30m 15s")
    """
    if seconds < 0:
        return "0s"

    # Break down into components
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:  # Always show seconds if nothing else
        if millisecs > 0 and not hours and not minutes:
            parts.append(f"{secs}.{millisecs:03d}s")
        else:
            parts.append(f"{secs}s")

    return " ".join(parts)


def parse_datetime(date_string: str, format_string: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """
    Parse datetime string to datetime object

    Args:
        date_string: Date/time string to parse
        format_string: strptime format string

    Returns:
        datetime object or None if parsing fails
    """
    try:
        return datetime.strptime(date_string, format_string)
    except ValueError:
        return None


def time_ago(dt: datetime) -> str:
    """
    Convert datetime to human-readable "time ago" format

    Args:
        dt: datetime object

    Returns:
        Human-readable time ago string (e.g., "2 hours ago")
    """
    now = datetime.now()
    diff = now - dt

    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"


def is_within_days(dt: datetime, days: int) -> bool:
    """
    Check if datetime is within specified number of days from now

    Args:
        dt: datetime to check
        days: Number of days

    Returns:
        True if within specified days, False otherwise
    """
    now = datetime.now()
    diff = now - dt
    return diff.days <= days


def add_days(dt: datetime, days: int) -> datetime:
    """
    Add days to datetime

    Args:
        dt: Base datetime
        days: Number of days to add (can be negative)

    Returns:
        New datetime with days added
    """
    return dt + timedelta(days=days)


def get_date_range(start: datetime, end: datetime) -> list[datetime]:
    """
    Get list of dates between start and end (inclusive)

    Args:
        start: Start datetime
        end: End datetime

    Returns:
        List of datetime objects for each day in range
    """
    dates = []
    current = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = end.replace(hour=0, minute=0, second=0, microsecond=0)

    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)

    return dates
