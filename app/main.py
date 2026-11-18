import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.schemas import LinkAnalysisRequest, LinkAnalysisResponse
from app.services.analysis_service import AnalysisService

# Setup Logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("link_analysis_api")

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Link Analysis API Service...")
    logger.info(f"Using LLM Provider: {settings.LLM_PROVIDER}")
    yield
    logger.info("Shutting down Link Analysis API Service...")


app = FastAPI(
    title="AI-Powered Website Link Analysis API",
    description="Analyzes website URLs and extracts Competitor, Search Query, SEO, Service, and Target Audience insights using LLMs.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analysis_service = AnalysisService()

# Mount static folder if exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", tags=["UI & Health"], summary="Web Dashboard UI")
async def root():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "status": "online",
        "service": "AI-Powered Website Link Analysis API",
        "docs": "/docs",
        "llm_provider": settings.LLM_PROVIDER,
    }


@app.get("/health", tags=["UI & Health"])
async def health_check():
    return {"status": "healthy"}


@app.post(
    "/link-analysis",
    response_model=LinkAnalysisResponse,
    status_code=status.HTTP_200_OK,
    tags=["Link Analysis"],
    summary="Analyze website content and generate 5-section AI insights",
    response_description="Structured 5-section analysis including Competitor, Queries, SEO, Services, and Audience.",
)
async def analyze_link(payload: LinkAnalysisRequest):
    """
    Main API endpoint:
    - Validates URL and prevents SSRF
    - Scrapes HTML, parses metadata and clean text
    - Sends payload to configured LLM (Gemini / OpenAI)
    - Returns structured JSON adhering to test requirements
    """
    target_url = str(payload.url)
    logger.info(f"Received link analysis request for: {target_url}")

    try:
        result = await analysis_service.analyze_url(target_url)
        return result
    except HTTPException:
        # Re-raise explicit HTTP exceptions
        raise
    except Exception as exc:
        logger.error(f"Unexpected error processing analysis for {target_url}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during analysis: {str(exc)}",
        )

