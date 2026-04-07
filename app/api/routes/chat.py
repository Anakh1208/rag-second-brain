"""
app/api/routes/chat.py
----------------------
Chat API Routes - Complete RAG Pipeline Integration

UPDATED: Now supports both grounded (with documents) and general (without documents) modes

Academic Note (for SEPM viva):
- Integrates all RAG components into a single API endpoint
- Orchestrates: SLM Analysis → Retrieval → Generation → Response
- NEW: Auto-switches between grounded and general chat modes
- Demonstrates separation of concerns (retrieval vs. generation)
- RESTful API design with proper HTTP semantics
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
from datetime import datetime

# Import RAG components
from app.rag.engine import RAGRetriever
from app.llm.generator import LLMGenerator, LLMProvider, get_generator

# Import SLM components
from app.slm.intent_detector import detect_intent, Intent
from app.slm.emotion_detector import detect_emotion, get_tone_instruction, needs_support, Emotion
from app.slm.date_detector import detect_dates

logger = logging.getLogger(__name__)

# ==============================================================================
# ROUTER INITIALIZATION
# ==============================================================================
router = APIRouter()

# ==============================================================================
# REQUEST/RESPONSE MODELS
# ==============================================================================

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's question or query",
        example="What is machine learning?"
    )
    top_k: Optional[int] = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of chunks to retrieve"
    )
    temperature: Optional[float] = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="LLM temperature (0=deterministic, 1=creative)"
    )


class SourceChunk(BaseModel):
    """Model for source chunk information."""
    chunk_id: str
    document_id: str
    chunk_index: int
    similarity_score: float
    rank: int
    chunk_text: Optional[str] = None


class ChatResponse(BaseModel):
    """
    Response model for chat endpoint.
    
    NEW FIELDS:
    - intent: User's detected intent
    - emotion: User's emotional tone
    - support_mode: Whether emotional support is active
    - dates_detected: Any temporal references found
    - mode: "grounded" or "general"
    """
    query: str
    answer: str
    grounded: bool
    mode: str  # NEW: "grounded" or "general"
    intent: str
    emotion: str
    support_mode: bool
    sources: List[SourceChunk]
    dates_detected: List[str]
    timestamp: str
    retrieval_stats: dict
    generation_stats: dict


# ==============================================================================
# GLOBAL INSTANCES (Singleton Pattern)
# ==============================================================================

_retriever: Optional[RAGRetriever] = None
_generator: Optional[LLMGenerator] = None


def get_rag_retriever() -> RAGRetriever:
    """Returns singleton RAG retriever instance."""
    global _retriever
    if _retriever is None:
        logger.info("[Chat] Initializing RAG Retriever...")
        _retriever = RAGRetriever()
        logger.info("[Chat] ✓ RAG Retriever ready")
    return _retriever


def get_llm() -> LLMGenerator:
    """Returns singleton LLM generator instance."""
    global _generator
    if _generator is None:
        logger.info("[Chat] Initializing LLM Generator...")
        _generator = get_generator()
        logger.info("[Chat] ✓ LLM Generator ready")
    return _generator


# ==============================================================================
# CHAT ENDPOINT
# ==============================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint - Complete Hybrid SLM + LLM RAG pipeline.
    
    NEW BEHAVIOR:
    - Works WITHOUT documents (general mode)
    - Works WITH documents (grounded mode)
    - Auto-detects which mode to use
    
    Flow:
    1. SLM Analysis (intent, emotion, dates)
    2. RAG Retrieval (if index available)
    3. LLM Generation (grounded OR general)
    4. Return structured response
    """
    
    logger.info("=" * 60)
    logger.info(f"[Chat] Query: '{request.query[:80]}'")
    logger.info("=" * 60)
    
    query = request.query.strip()
    
    # ── PHASE 0: SLM Analysis ─────────────────────────────────────────────────
    logger.info("[PHASE 0] Running SLM analysis...")
    
    # Intent detection
    intent, intent_conf, intent_explanation = detect_intent(query)
    logger.info(f"  Intent: {intent} ({intent_conf:.2f}) — {intent_explanation}")
    
    # Emotion detection
    emotion, emotion_conf, emotion_explanation = detect_emotion(query)
    logger.info(f"  Emotion: {emotion} ({emotion_conf:.2f}) — {emotion_explanation}")
    
    # Date detection
    detected_dates = detect_dates(query)
    logger.info(f"  Dates: {len(detected_dates)} found")
    
    # Auto support mode
    support_mode = needs_support(query)
    logger.info(f"  Support Mode: {'ON (auto)' if support_mode else 'OFF'}")
    
    # ── Handle non-question intents directly ──────────────────────────────────
    if intent == Intent.GREETING:
        return ChatResponse(
            query=query,
            answer="Hello! 👋 I'm your Second Brain assistant. I can answer general questions or help you query your uploaded documents!",
            grounded=False,
            mode="general",
            intent=intent.value,
            emotion=emotion.value,
            support_mode=support_mode,
            sources=[],
            dates_detected=[d["raw"] for d in detected_dates],
            timestamp=datetime.utcnow().isoformat(),
            retrieval_stats={},
            generation_stats={"skipped": "greeting intent"}
        )
    
    # ── Handle REMINDER intent ────────────────────────────────────────────────
    if intent == Intent.REMINDER:
        if detected_dates:
            from app.slm.reminder_manager import ReminderManager
            reminder_manager = ReminderManager()
            reminder_date = detected_dates[0]["datetime"]
            reminder = reminder_manager.create_reminder(
                user_message=query,
                reminder_text=query,
                reminder_date=reminder_date,
            )
            logger.info(f"[Chat] ✅ Reminder created: id={reminder['id']}, date={reminder_date}")
            return ChatResponse(
                query=query,
                answer=(
                    f"✅ Reminder set! I'll remind you about:\n\n"
                    f"*{query}*\n\n"
                    f"on **{reminder_date.strftime('%B %d, %Y at %I:%M %p')}**"
                ),
                grounded=False,
                mode="reminder",
                intent=intent.value,
                emotion=emotion.value,
                support_mode=False,
                sources=[],
                dates_detected=[d["raw"] for d in detected_dates],
                timestamp=datetime.utcnow().isoformat(),
                retrieval_stats={},
                generation_stats={"reminder_created": True, "reminder_id": reminder["id"]},
            )
        else:
            return ChatResponse(
                query=query,
                answer=(
                    "⚠️ I couldn't detect a date in your reminder. "
                    "Please specify when you want to be reminded — for example:\n"
                    "- *'Remind me on 10th April'*\n"
                    "- *'Remind me tomorrow at 5pm'*"
                ),
                grounded=False,
                mode="general",
                intent=intent.value,
                emotion=emotion.value,
                support_mode=False,
                sources=[],
                dates_detected=[],
                timestamp=datetime.utcnow().isoformat(),
                retrieval_stats={},
                generation_stats={},
            )

    # ── PHASE 1: RAG Retrieval (OPTIONAL - may not be available) ─────────────
    logger.info("[PHASE 1] RAG Retrieval (attempting)...")
    
    retriever = get_rag_retriever()
    context_text = ""
    retrieved_chunks = []
    retrieval_stats = {}
    
    # Try to retrieve context, but DON'T fail if index isn't ready
    if retriever.get_stats().get("status") == "ready":
        try:
            retrieval_result = retriever.retrieve_context(
                query=query,
                top_k=request.top_k
            )
            
            context_text = retrieval_result["context_text"]
            retrieved_chunks = retrieval_result["retrieved_chunks"]
            retrieval_stats = retrieval_result["retrieval_stats"]
            
            logger.info(f"  ✓ Retrieved: {len(retrieved_chunks)} chunks, context={len(context_text)} chars")
            
        except Exception as e:
            logger.warning(f"  ⚠ Retrieval failed: {e}")
            logger.info(f"  → Falling back to general mode")
            context_text = ""
            retrieval_stats = {"mode": "general", "reason": "retrieval_error"}
    else:
        logger.info(f"  ⚠ Index not ready - using general mode")
        retrieval_stats = {"mode": "general", "reason": "index_not_ready"}
    
    # ── PHASE 2: Enrich prompt with SLM emotion context ───────────────────────
    logger.info("[PHASE 2] Enriching prompt with SLM emotion context...")
    
    tone_instruction = get_tone_instruction(query)
    
    # Add tone instruction if support mode is active and we have context
    if support_mode and context_text:
        context_text = f"[TONE INSTRUCTION: {tone_instruction}]\n\n{context_text}"
        logger.info(f"  Tone injected: {tone_instruction}")
    
    # ── PHASE 3: LLM Generation (WORKS WITH OR WITHOUT CONTEXT) ───────────────
    logger.info("[PHASE 3] LLM Generation...")
    
    generator = get_llm()
    
    # Update temperature if specified
    if request.temperature != generator.temperature:
        generator.temperature = request.temperature
    
    # Generate (context can be empty - generator handles it)
    gen_result = generator.generate(
        query=query,
        context=context_text  # Empty string = general mode, filled = grounded mode
    )
    
    answer = gen_result["answer"]
    grounded = gen_result["grounded"]
    mode = gen_result.get("mode", "unknown")
    
    logger.info(f"  ✓ Generated: mode={mode}, grounded={grounded}, length={len(answer)}")
    
    # ── PHASE 4: Build Response ───────────────────────────────────────────────
    
    # Format sources for frontend
    sources = [
        SourceChunk(
            chunk_id=chunk["chunk_id"],
            document_id=chunk["document_id"],
            chunk_index=chunk.get("chunk_index", 0),
            similarity_score=chunk["similarity_score"],
            rank=chunk.get("rank", 0),
            chunk_text=chunk["chunk_text"][:200] + "..." if len(chunk["chunk_text"]) > 200 else chunk["chunk_text"]
        )
        for chunk in retrieved_chunks[:5]
    ]
    
    generation_stats = {
        "provider": str(gen_result.get("provider", "unknown")),
        "temperature": request.temperature,
        "grounded": grounded,
        "mode": mode
    }
    
    logger.info("=" * 60)
    logger.info(f"[Chat] ✅ Done — mode={mode}, intent={intent}, emotion={emotion}, grounded={grounded}")
    logger.info("=" * 60)
    
    return ChatResponse(
        query=query,
        answer=answer,
        grounded=grounded,
        mode=mode,
        intent=intent.value,
        emotion=emotion.value,
        support_mode=support_mode,
        sources=sources,
        dates_detected=[d["raw"] for d in detected_dates],
        timestamp=datetime.utcnow().isoformat(),
        retrieval_stats=retrieval_stats,
        generation_stats=generation_stats
    )


# ==============================================================================
# HEALTH CHECK ENDPOINT
# ==============================================================================

@router.get("/chat/health")
async def chat_health():
    """
    Health check for chat system.
    
    Returns system status and component readiness.
    """
    
    try:
        retriever = get_rag_retriever()
        generator = get_llm()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "rag_retriever": retriever.get_stats(),
                "llm_generator": generator.get_status(),
                "slm_modules": {
                    "intent_detector": "ready",
                    "emotion_detector": "ready",
                    "date_detector": "ready"
                }
            }
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# ==============================================================================
# STATISTICS ENDPOINT
# ==============================================================================

@router.get("/chat/stats")
async def chat_stats():
    """
    Returns statistics about the RAG system.
    """
    
    try:
        retriever = get_rag_retriever()
        generator = get_llm()
        
        return {
            "retrieval": retriever.get_stats(),
            "generation": generator.get_status(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Stats retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stats: {str(e)}"
        )