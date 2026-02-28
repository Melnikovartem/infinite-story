"""Main FastAPI application for Infinite Story Engine."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Infinite Story Engine",
    description="AI-powered interactive storytelling platform",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for MVP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "infinite-story-engine"}


# Import and include routers
from app.routes import sessions, reports, progress

app.include_router(sessions.router, prefix="/api", tags=["sessions"])
app.include_router(reports.router, prefix="/api", tags=["reports"])
app.include_router(progress.router, prefix="/api", tags=["progress"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Infinite Story Engine API",
        "version": "0.1.0",
        "docs": "/docs"
    }
