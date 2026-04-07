from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.scheduler.reminder_scheduler import start_reminder_scheduler
from dotenv import load_dotenv

# Import routes
from app.api.routes import health, chat, documents, index
load_dotenv()
# -----------------------------------------------------------------------------
# CREATE FASTAPI APP
# -----------------------------------------------------------------------------
app = FastAPI(
    title="Hybrid SLM + LLM RAG Second Brain",
    description="Academic prototype for SEPM course",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)
@app.on_event("startup")
async def startup_event():
    start_reminder_scheduler()

# -----------------------------------------------------------------------------
# CORS MIDDLEWARE (KEEP AS-IS)
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Dev mode (OK for SEPM)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# PATH CONFIGURATION
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

# Serve static files (optional but correct)
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "frontend" / "static"),
    name="static"
)

# Jinja2 templates
templates = Jinja2Templates(
    directory=BASE_DIR / "frontend" / "templates"
)

# -----------------------------------------------------------------------------
# API ROUTES
# -----------------------------------------------------------------------------
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
app.include_router(index.router, prefix="/api", tags=["Index"])

# -----------------------------------------------------------------------------
# UI ROUTE (THIS IS THE MISSING PIECE)
# -----------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
async def serve_ui(request: Request):
    """
    Serves the ChatGPT-style UI (index.html)
    """
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

# -----------------------------------------------------------------------------
# STARTUP LOG
# -----------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    import logging
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("RAG Second Brain Server Started")
    logger.info("UI available at http://127.0.0.1:8000/")
    logger.info("API docs at http://127.0.0.1:8000/api/docs")
    logger.info("=" * 60)
    # Start background reminder scheduler
    start_reminder_scheduler()
    logger.info("Reminder scheduler started")

# -----------------------------------------------------------------------------
# MAIN ENTRY
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
