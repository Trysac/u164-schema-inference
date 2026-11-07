"""Format detectors for date and RFC 3339 date-time strings."""

from __future__ import annotations

import re
from datetime import date

# Date regex: YYYY-MM-DD
_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")

# RFC 3339 section 5.6 date-time regex
_DATETIME_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})[Tt](\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?([Zz]|[+-]\d{2}:\d{2})$"
)


def detect_format(s: str) -> str | None:
    """Detect if string matches 'date' or 'date-time' format, else return None."""
    # Check date first if length is 10
    if len(s) == 10:
        m = _DATE_RE.match(s)
        if m:
            year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
            try:
                date(year, month, day)
                return "date"
            except ValueError:
                return None

    # Check date-time
    m = _DATETIME_RE.match(s)
    if m:
        year = int(m.group(1))
        month = int(m.group(2))
        day = int(m.group(3))
        hour = int(m.group(4))
        minute = int(m.group(5))
        second = int(m.group(6))
        tz = m.group(8)

        try:
            date(year, month, day)
        except ValueError:
            return None

        # In RFC 3339 leap second 60 is permitted; seconds must be 0-60
        if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 60):
            return None

        if tz not in ("Z", "z"):
            sign = tz[0]
            tz_hour = int(tz[1:3])
            tz_min = int(tz[4:6])
            if not (0 <= tz_hour <= 23 and 0 <= tz_min <= 59):
                return None
            if sign not in ("+", "-"):
                return None

        return "date-time"

    return None
