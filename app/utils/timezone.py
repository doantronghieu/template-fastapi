"""Timezone conversion utilities.

Handles conversion between UTC (database storage) and local timezones (display).
Database stores all timestamps in UTC for consistency and portability.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

# Vietnam timezone (UTC+7, no DST)
VIETNAM_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def to_vietnam_time(dt: datetime | None) -> datetime | None:
    """Convert UTC datetime to Vietnam timezone (UTC+7).

    Args:
        dt: UTC datetime object (timezone-aware)

    Returns:
        Datetime converted to Asia/Ho_Chi_Minh timezone, or None if input is None

    Example:
        >>> from datetime import datetime, timezone
        >>> utc_time = datetime(2025, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        >>> vn_time = to_vietnam_time(utc_time)
        >>> print(vn_time)  # 2025-01-15 15:00:00+07:00
    """
    if dt is None:
        return None
    return dt.astimezone(VIETNAM_TZ)


def format_vietnam_time(
    dt: datetime | None, fmt: str = "%d/%m/%Y %H:%M:%S"
) -> str | None:
    """Format datetime in Vietnam timezone with custom pattern.

    Args:
        dt: UTC datetime object (timezone-aware)
        fmt: strftime format pattern (default: "DD/MM/YYYY HH:MM:SS")

    Returns:
        Formatted string in Vietnam timezone, or None if input is None

    Example:
        >>> from datetime import datetime, timezone
        >>> utc_time = datetime(2025, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        >>> formatted = format_vietnam_time(utc_time, "%d/%m/%Y %H:%M")
        >>> print(formatted)  # "15/01/2025 15:00"
    """
    if dt is None:
        return None
    vn_time = to_vietnam_time(dt)
    return vn_time.strftime(fmt) if vn_time else None
