from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Academic Note:
    - Used to verify backend availability
    - Common practice in service-oriented architectures
    """
    return {
        "status": "ok",
        "message": "Hybrid RAG Second Brain backend is running"
    }
