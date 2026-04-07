"""
app/llm/generator.py
---------------------
LLM Response Generator — Ollama Integration with Dual Mode Support

UPDATED: Now supports both:
- Grounded Mode: Answers from documents (RAG)
- General Mode: Answers general questions (no documents needed)

Academic Note (SEPM):
- This is PHASE 2 of RAG (generation)
- Phase 1 (retrieval) happens in rag/engine.py
- NEW: Can work without retrieval context
- Grounding strategy prevents hallucination in grounded mode

PROVIDER DECISION:
- Using Ollama with gemma3:1b (local, offline, free)
- Rationale: academic prototype, no API cost, privacy preserved
- Temperature 0.3 → deterministic, factual responses

SETUP:
    brew install ollama
    ollama pull gemma3:1b
    ollama serve
"""

import logging
import requests
from typing import Optional
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Ollama config ─────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL    = "gemma3:1b"
OLLAMA_TIMEOUT  = 120


# ── System prompts ────────────────────────────────────────────────────────────

# For document-based questions (when context is available)
GROUNDED_SYSTEM_PROMPT = """You are a helpful personal knowledge assistant for a Second Brain application.

STRICT RULES you MUST follow:
1. Answer ONLY using the information provided in the CONTEXT below.
2. If the context does not contain enough information to answer, say exactly:
   "I don't have enough information in your knowledge base to answer this."
3. Do NOT make up facts, dates, names, or figures not in the context.
4. Be concise, clear, and direct.
5. Always refer to the context as "your knowledge base" or "your documents".

These rules ensure your answers are grounded in your actual uploaded documents."""

# For general questions (when no context or context is irrelevant)
GENERAL_SYSTEM_PROMPT = """You are a helpful AI assistant in a Second Brain application.

You can answer general knowledge questions, have conversations, and provide assistance.
Be friendly, helpful, and conversational.

If asked about uploaded documents or the knowledge base specifically, remind the user they can upload documents to query them."""


# ── Prompt templates ──────────────────────────────────────────────────────────

GROUNDED_PROMPT_TEMPLATE = """{system_prompt}

{context}

USER QUESTION: {query}

ANSWER (based only on the context above):"""


GENERAL_PROMPT_TEMPLATE = """{system_prompt}

USER QUESTION: {query}

ANSWER:"""


class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    MOCK   = "mock"


class LLMGenerator:
    """
    Generates LLM responses using Ollama (local, offline).
    
    NEW: Supports dual modes:
    - Grounded mode: Answers from provided context (documents)
    - General mode: Answers general questions (no context needed)
    
    Academic Note:
    - Singleton pattern: one instance reused across requests
    - Strategy pattern: provider can be swapped (OLLAMA / MOCK)
    - Grounding = LLM only answers from provided context
    - Low temperature (0.3) = more deterministic, factual answers
    """

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.OLLAMA,
        temperature: float = 0.3,
        max_tokens: int = 1024
    ):
        self.provider    = provider
        self.temperature = temperature
        self.max_tokens  = max_tokens
        self._test_connection()

    def _test_connection(self):
        """Tests connection to Ollama on startup."""
        if self.provider == LLMProvider.MOCK:
            logger.info("[LLMGenerator] Using MOCK provider — no Ollama needed")
            return

        try:
            resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            if resp.ok:
                models = [m["name"] for m in resp.json().get("models", [])]
                logger.info(f"[LLMGenerator] ✅ Ollama connected. Models: {models}")

                if not any(OLLAMA_MODEL in m for m in models):
                    logger.warning(f"[LLMGenerator] ⚠️  Model '{OLLAMA_MODEL}' not found!")
                    logger.warning(f"[LLMGenerator]    Run: ollama pull {OLLAMA_MODEL}")
            else:
                logger.warning("[LLMGenerator] ⚠️  Ollama responded with error")
        except requests.exceptions.ConnectionError:
            logger.warning("[LLMGenerator] ⚠️  Ollama not running!")
            logger.warning("[LLMGenerator]    Start with: ollama serve")
            logger.warning("[LLMGenerator]    Falling back to MOCK provider")
            self.provider = LLMProvider.MOCK

    def generate(self, query: str, context: str = "") -> dict:
        """
        Generates a response.
        
        NEW BEHAVIOR:
        - If context provided and substantial: Use grounded mode (RAG)
        - If context empty/short: Use general mode (can answer anything)
        
        This allows the chatbot to work WITHOUT documents!

        Args:
            query:   User's question
            context: Retrieved context string (optional, can be empty)

        Returns dict:
            answer:   LLM response text
            grounded: True if response is based on documents
            mode:     "grounded" or "general"
            provider: which provider was used
        """
        
        # ── Decide mode based on context availability ─────────────────────────
        has_meaningful_context = context and len(context.strip()) > 100
        mode = "grounded" if has_meaningful_context else "general"
        
        logger.info(f"[LLMGenerator] Mode: {mode} | Context: {len(context) if context else 0} chars")

        # ── Build prompt based on mode ────────────────────────────────────────
        if mode == "grounded":
            prompt = GROUNDED_PROMPT_TEMPLATE.format(
                system_prompt=GROUNDED_SYSTEM_PROMPT,
                context=context,
                query=query
            )
        else:
            prompt = GENERAL_PROMPT_TEMPLATE.format(
                system_prompt=GENERAL_SYSTEM_PROMPT,
                query=query
            )

        # ── Generate ──────────────────────────────────────────────────────────
        if self.provider == LLMProvider.MOCK:
            answer = self._mock_generate(query, mode)
        else:
            answer = self._ollama_generate(prompt)

        # ── Check grounding (only relevant in grounded mode) ──────────────────
        grounded = mode == "grounded" and self._check_grounding(answer)

        logger.info(f"[LLMGenerator] ✅ Mode: {mode}, Grounded: {grounded}, Length: {len(answer)}")

        return {
            "answer":    answer,
            "grounded":  grounded,
            "mode":      mode,
            "provider":  self.provider,
            "timestamp": datetime.utcnow().isoformat()
        }

    def _ollama_generate(self, prompt: str) -> str:
        """
        Calls Ollama API to generate a response.

        Uses /api/generate endpoint (non-streaming for simplicity).
        """
        try:
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model":  OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature":  self.temperature,
                        "num_predict":  self.max_tokens,
                        "top_p":        0.9,
                        "repeat_penalty": 1.1
                    }
                },
                timeout=OLLAMA_TIMEOUT
            )

            if response.ok:
                result = response.json()
                answer = result.get("response", "").strip()

                if not answer:
                    logger.warning("[LLMGenerator] Ollama returned empty response")
                    return "I was unable to generate a response. Please try again."

                logger.info(f"[LLMGenerator] Ollama response: {len(answer)} chars")
                return answer

            else:
                logger.error(f"[LLMGenerator] Ollama HTTP error: {response.status_code}")
                logger.error(f"[LLMGenerator] Response: {response.text[:200]}")
                return f"Ollama error: {response.status_code}. Is '{OLLAMA_MODEL}' model pulled?"

        except requests.exceptions.Timeout:
            logger.error("[LLMGenerator] Ollama request timed out")
            return "Request timed out. The model may be loading — please try again."

        except requests.exceptions.ConnectionError:
            logger.error("[LLMGenerator] Cannot connect to Ollama")
            return "Cannot connect to Ollama. Run: ollama serve"

        except Exception as e:
            logger.error(f"[LLMGenerator] Unexpected error: {e}")
            return f"Unexpected error: {str(e)}"

    def _mock_generate(self, query: str, mode: str) -> str:
        """
        Mock response for testing without Ollama.
        """
        if mode == "grounded":
            return (
                f"[MOCK GROUNDED] I would answer '{query}' based on your documents. "
                f"Install Ollama and run 'ollama pull {OLLAMA_MODEL}' for real responses."
            )
        else:
            return (
                f"[MOCK GENERAL] I would answer '{query}' using general knowledge. "
                f"Install Ollama and run 'ollama pull {OLLAMA_MODEL}' for real responses."
            )

    def _check_grounding(self, answer: str) -> bool:
        """
        Checks if the response appears to be grounded in the provided context.

        Looks for signals that the LLM followed grounding instructions.
        A grounded response either:
        - References the context/documents
        - Explicitly says it doesn't know
        - Doesn't appear to be hallucinating
        """
        answer_lower = answer.lower()

        # Positive grounding signals
        grounded_signals = [
            "based on",
            "according to",
            "your knowledge base",
            "your documents",
            "the context",
            "as mentioned",
            "i don't have enough information",
            "the document",
            "in your"
        ]

        # Hallucination signals (bad signs)
        hallucination_signals = [
            "i believe",
            "i think",
            "i'm not sure but",
            "probably",
            "as far as i know",
            "in general,"
        ]

        has_grounding    = any(s in answer_lower for s in grounded_signals)
        has_hallucination = any(s in answer_lower for s in hallucination_signals)

        # Grounded if has positive signals and no hallucination signals
        # OR if it's a refusal ("I don't have enough information")
        is_refusal = "don't have enough information" in answer_lower

        return (has_grounding and not has_hallucination) or is_refusal

    def get_status(self) -> dict:
        """Returns provider status."""
        if self.provider == LLMProvider.MOCK:
            return {"provider": "mock", "status": "ready"}

        try:
            resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
            if resp.ok:
                models = [m["name"] for m in resp.json().get("models", [])]
                model_ready = any(OLLAMA_MODEL in m for m in models)
                return {
                    "provider":    "ollama",
                    "status":      "ready" if model_ready else "model_missing",
                    "model":       OLLAMA_MODEL,
                    "model_ready": model_ready,
                    "all_models":  models
                }
        except Exception:
            pass

        return {"provider": "ollama", "status": "offline", "model": OLLAMA_MODEL}


# ── Singleton instance ────────────────────────────────────────────────────────
_generator_instance: Optional[LLMGenerator] = None


def get_generator() -> LLMGenerator:
    """
    Returns singleton LLMGenerator instance.

    Academic Note: Singleton pattern avoids re-loading/re-connecting
    on every request — efficient for production and demos.
    """
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = LLMGenerator(
            provider=LLMProvider.OLLAMA,
            temperature=0.3,
            max_tokens=1024
        )
    return _generator_instance