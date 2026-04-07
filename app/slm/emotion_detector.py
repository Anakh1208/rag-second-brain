"""
app/slm/emotion_detector.py
---------------------------
Lightweight keyword-based emotion/tone detector (SLM component).

Returns: (Emotion, confidence: float, explanation: str)
"""

from enum import Enum
import re


class Emotion(Enum):
    NEUTRAL   = "neutral"
    STRESSED  = "stressed"
    CURIOUS   = "curious"
    HAPPY     = "happy"
    SAD       = "sad"
    ANXIOUS   = "anxious"
    FRUSTRATED = "frustrated"


# ── Keyword rules (first match wins) ─────────────────────────────────────────
_RULES = [
    (Emotion.STRESSED,    r"\b(stressed|overwhelmed|too much|burnout|exhausted|swamped|drowning)\b"),
    (Emotion.ANXIOUS,     r"\b(anxious|worried|nervous|scared|afraid|panic|fear|dread)\b"),
    (Emotion.FRUSTRATED,  r"\b(frustrated|annoyed|angry|irritated|fed up|sick of|hate)\b"),
    (Emotion.SAD,         r"\b(sad|depressed|unhappy|miserable|down|upset|crying|lonely)\b"),
    (Emotion.HAPPY,       r"\b(happy|excited|great|awesome|fantastic|wonderful|love|joy|thrilled)\b"),
    (Emotion.CURIOUS,     r"\b(curious|wondering|interesting|interesting|fascinated|want to know|tell me|how does|why does)\b"),
]

# ── Tone instruction map ──────────────────────────────────────────────────────
_TONE_INSTRUCTIONS = {
    Emotion.STRESSED:    "Be calm, empathetic, and concise. Acknowledge the user's stress before answering.",
    Emotion.ANXIOUS:     "Be gentle, reassuring, and structured. Break information into small steps.",
    Emotion.FRUSTRATED:  "Be patient and direct. Avoid lengthy preambles — get to the point.",
    Emotion.SAD:         "Be warm, compassionate, and supportive. Acknowledge their feelings.",
    Emotion.HAPPY:       "Match their positive energy. Be enthusiastic and encouraging.",
    Emotion.CURIOUS:     "Be detailed and educational. Satisfy their curiosity with depth.",
    Emotion.NEUTRAL:     "Be clear, professional, and helpful.",
}

# ── Support-mode trigger emotions ─────────────────────────────────────────────
_SUPPORT_EMOTIONS = {Emotion.STRESSED, Emotion.ANXIOUS, Emotion.SAD}


def detect_emotion(text: str) -> tuple:
    """
    Detect the emotional tone of a user query.

    Args:
        text: Raw user input string.

    Returns:
        (Emotion, confidence: float, explanation: str)
    """
    lowered = text.strip().lower()

    for emotion, pattern in _RULES:
        match = re.search(pattern, lowered, re.IGNORECASE)
        if match:
            confidence = 0.85
            explanation = f"Matched '{emotion.value}' via keyword: '{match.group()}'"
            return emotion, confidence, explanation

    return Emotion.NEUTRAL, 0.60, "No strong emotional signal detected; defaulting to NEUTRAL"


def get_tone_instruction(text: str) -> str:
    """
    Return a tone/style instruction string for the LLM based on detected emotion.

    Args:
        text: Raw user input string.

    Returns:
        A string instruction to prepend to the LLM prompt.
    """
    emotion, _, _ = detect_emotion(text)
    return _TONE_INSTRUCTIONS.get(emotion, _TONE_INSTRUCTIONS[Emotion.NEUTRAL])


def needs_support(text: str) -> bool:
    """
    Return True if the detected emotion warrants emotional support mode.

    Args:
        text: Raw user input string.

    Returns:
        bool
    """
    emotion, _, _ = detect_emotion(text)
    return emotion in _SUPPORT_EMOTIONS
