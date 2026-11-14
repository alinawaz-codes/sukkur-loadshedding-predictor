"""Helper functions: timing, status, countdown, temperature.

All times use Pakistan time (Asia/Karachi), because the website server
(Streamlit Cloud) runs in UTC.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

PK_TZ = ZoneInfo("Asia/Karachi")

# Approximate average temperature of Sukkur for each month (degrees C).
# The user never types temperature: the app uses this table for the chosen date.
MONTHLY_TEMP = {
    1: 14.5, 2: 18.0, 3: 24.0, 4: 30.0, 5: 34.5, 6: 36.5,
    7: 35.0, 8: 34.0, 9: 32.0, 10: 28.0, 11: 21.0, 12: 15.5,
}

DAY_SECONDS = 24 * 3600


def now_pk():
    """Current date and time in Pakistan."""
    return datetime.now(PK_TZ)


def estimated_temperature(day):
    """Average temperature for the month of the given date."""
    return MONTHLY_TEMP[day.month]


def to_minutes(hhmm):
    """'14:30' -> 870 (minutes after midnight)."""
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def fmt_12h(hhmm):
    """'14:30' -> '2:30 PM'."""
    minutes = to_minutes(hhmm)
    hours, mins = divmod(minutes, 60)
    suffix = "AM" if hours < 12 else "PM"
    hours12 = hours % 12 or 12
    return f"{hours12}:{mins:02d} {suffix}"


def duration_minutes(off_hhmm, on_hhmm):
    return to_minutes(on_hhmm) - to_minutes(off_hhmm)


def fmt_duration(minutes):
    """150 -> '2 h 30 min'."""
    hours, mins = divmod(int(minutes), 60)
    if hours and mins:
        return f"{hours} h {mins} min"
    if hours:
        return f"{hours} h"
    return f"{mins} min"


def seconds_since_midnight(moment):
    return moment.hour * 3600 + moment.minute * 60 + moment.second


def live_state(now_seconds, off_hhmm, on_hhmm):
    """Where is 'now' compared with today's outage window?

    Returns (state, seconds_left):
      "BEFORE" -> light is ON, seconds until it goes off
      "DURING" -> light is OFF, seconds until it comes back
      "AFTER"  -> light is ON, seconds until tomorrow's outage starts
    """
    off_sec = to_minutes(off_hhmm) * 60
    on_sec = to_minutes(on_hhmm) * 60
    if now_seconds < off_sec:
        return "BEFORE", off_sec - now_seconds
    if now_seconds < on_sec:
        return "DURING", on_sec - now_seconds
    return "AFTER", (DAY_SECONDS - now_seconds) + off_sec


def fmt_countdown(seconds):
    """3725 -> '1 h 02 min 05 s'  (45 min 20 s style for short times)."""
    seconds = int(seconds)
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours} h {minutes:02d} min {secs:02d} s"
    return f"{minutes} min {secs:02d} s"
