"""
app/slm/date_detector.py
------------------------
Lightweight rule-based date/time detector (SLM component).

Parses natural-language temporal references into structured dicts:
    [{"raw": str, "datetime": datetime | None}]
"""

import re
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MONTHS = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}


def _ordinal_to_int(s: str) -> int:
    """Convert '1st', '2nd', '22nd', '10th' → int."""
    return int(re.sub(r"(st|nd|rd|th)$", "", s.strip(), flags=re.I))


# ---------------------------------------------------------------------------
# Main detector
# ---------------------------------------------------------------------------

def detect_dates(text: str) -> list:
    """
    Detect temporal references in *text* and return a list of dicts.

    Each dict has:
        raw      – the matched substring
        datetime – a Python datetime object (or None if unparseable)

    Args:
        text: Raw user input.

    Returns:
        List of detected date dicts (may be empty).
    """
    now = datetime.now()
    results = []

    # ── Relative keywords ────────────────────────────────────────────────────
    relative_patterns = [
        (r"\btoday\b",     timedelta(days=0)),
        (r"\btomorrow\b",  timedelta(days=1)),
        (r"\bday after tomorrow\b", timedelta(days=2)),
        (r"\bnext week\b", timedelta(weeks=1)),
        (r"\bnext month\b", None),   # handled specially
    ]
    for pattern, delta in relative_patterns:
        m = re.search(pattern, text, re.I)
        if m:
            if delta is not None:
                dt = now + delta
            else:
                # next month — same day, month + 1
                month = now.month % 12 + 1
                year  = now.year + (1 if now.month == 12 else 0)
                dt = now.replace(month=month, year=year)
            results.append({"raw": m.group(), "datetime": dt})

    # ── "on <day> <month>" or "<day>th of <month>" ──────────────────────────
    explicit_pattern = (
        r"\b(?:on\s+)?(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?"
        r"(january|february|march|april|may|june|july|august|september|"
        r"october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)"
        r"(?:\s+(\d{4}))?\b"
    )
    for m in re.finditer(explicit_pattern, text, re.I):
        day   = int(m.group(1))
        month = _MONTHS[m.group(2).lower()]
        year  = int(m.group(3)) if m.group(3) else now.year
        try:
            dt = datetime(year, month, day, now.hour, now.minute)
            # If date is in the past this year, bump to next year
            if dt < now and not m.group(3):
                dt = dt.replace(year=year + 1)
        except ValueError:
            dt = None
        results.append({"raw": m.group(), "datetime": dt})

    # ── "at <H>pm / <H>:<MM>am" ─────────────────────────────────────────────
    time_pattern = r"\bat\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b"
    for m in re.finditer(time_pattern, text, re.I):
        hour   = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        period = (m.group(3) or "").lower()
        if period == "pm" and hour < 12:
            hour += 12
        elif period == "am" and hour == 12:
            hour = 0
        dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        results.append({"raw": m.group(), "datetime": dt})

    # Deduplicate by raw string
    seen = set()
    unique = []
    for r in results:
        if r["raw"] not in seen:
            seen.add(r["raw"])
            unique.append(r)

    return unique
