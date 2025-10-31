"""
Main FastAPI application
Entry point for the RAG system
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.api.routes import router
from src.config import Config, logger


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management
    """
    # Startup
    logger.info("[v0] === APPLICATION STARTUP ===")
    logger.info(f"[v0] {Config.APP_NAME} v{Config.APP_VERSION}")
    logger.info(f"[v0] Debug Mode: {Config.DEBUG}")
    logger.info(f"[v0] LLM Provider: {Config.LLM_PROVIDER}")
    logger.info(f"[v0] Embedding Model: {Config.EMBEDDING_MODEL}")
    logger.info(f"[v0] Qdrant: {Config.QDRANT_HOST}:{Config.QDRANT_PORT}")
    logger.info("[v0] === STARTUP COMPLETE ===\n")
    
    yield
    
    # Shutdown
    logger.info("\n[v0] === APPLICATION SHUTDOWN ===")
    logger.info("[v0] Gracefully shutting down...")
    logger.info("[v0] === SHUTDOWN COMPLETE ===")


# Create FastAPI app
app = FastAPI(
    title=Config.APP_NAME,
    description="Production-grade RAG system for research papers",
    version=Config.APP_VERSION,
    lifespan=lifespan,
    debug=Config.DEBUG
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint"""
    logger.debug("[v0] Root endpoint accessed")
    return {
        "message": f"Welcome to {Config.APP_NAME}",
        "version": Config.APP_VERSION,
        "docs": "/docs"
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"[v0] Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "details": str(exc) if Config.DEBUG else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"[v0] Starting server on {Config.HOST}:{Config.PORT}")
    
    uvicorn.run(
        "src.main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.RELOAD,
        log_level="debug" if Config.DEBUG else "info",
        timeout_keep_alive=300,  # Keep connection alive for 5 minutes
        timeout_notify=300  # Shutdown grace period
    )
