<<<<<<< HEAD
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
=======
"""
Infinite Story Engine - FastAPI Application

Main entry point for the REST API server.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, timezone, UTC
import logging

from app.config import settings

# Set up logging
logger = logging.getLogger("infinite_story")

# Create FastAPI application
app = FastAPI(
    title="Infinite Story Engine",
    description="AI-powered interactive storytelling engine",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
>>>>>>> origin/master
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
<<<<<<< HEAD
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
=======
    """
    Health check endpoint.
    
    Returns:
        dict: Status information
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "0.1.0"
    }


@app.get("/api/status")
async def status():
    """
    Server status endpoint.
    
    Returns information about the server and configuration.
    """
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "debug": settings.debug,
        "timestamp": datetime.now(UTC).isoformat(),
        "data_dir": settings.data_dir,
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions with consistent format."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
>>>>>>> origin/master
