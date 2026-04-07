"""
app/slm/intent_detector.py
--------------------------
Lightweight keyword-based intent detector (SLM component).

Returns: (Intent, confidence: float, explanation: str)
"""

from enum import Enum
import re

class Intent(Enum):
    GREETING    = "greeting"
    QUESTION    = "question"
    COMMAND     = "command"
    FAREWELL    = "farewell"
    FEEDBACK    = "feedback"
    UNKNOWN     = "unknown"
    REMINDER    = "reminder"


# Keyword rules — ordered by priority (first match wins)
_RULES = [
    (Intent.GREETING,  r"\b(hi|hello|hey|greetings|good\s+(morning|afternoon|evening)|what'?s\s+up)\b"),
    (Intent.FAREWELL,  r"\b(bye|goodbye|see\s+you|take\s+care|ciao|later)\b"),
    (Intent.FEEDBACK,  r"\b(thanks?|thank\s+you|great|good\s+job|well\s+done|awesome|cheers)\b"),
    # Reminder intent — checked before COMMAND/QUESTION so it takes priority
    (Intent.REMINDER,  r"\b(remind\s+(me|us)|set\s+a?\s*reminder|don't\s+forget|make\s+sure.*remember|alert\s+me|notify\s+me)\b"),
    (Intent.COMMAND,   r"\b(summarize|list|show|find|search|upload|delete|create|generate|explain|give\s+me)\b"),
    (Intent.QUESTION,  r"(\?|^(what|who|where|when|why|how|is|are|was|were|can|could|should|would|do|does|did)\b)"),
]

def detect_intent(text: str) -> tuple:
    """
    Detect the intent of a user query.

    Args:
        text: Raw user input string.

    Returns:
        (Intent, confidence: float, explanation: str)
    """
    lowered = text.strip().lower()

    for intent, pattern in _RULES:
        match = re.search(pattern, lowered, re.IGNORECASE)
        if match:
            confidence = 0.90
            explanation = f"Matched pattern for '{intent.value}': '{match.group()}'"
            return intent, confidence, explanation

    return Intent.UNKNOWN, 0.50, "No strong signal detected; defaulting to UNKNOWN"
