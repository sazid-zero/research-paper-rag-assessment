"""
Configuration management for RAG system
Centralized configuration with logging setup
"""
import os
import logging
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Application
    APP_NAME = "Research Paper RAG Assistant"
    APP_VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "True") == "True"
    
    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    RELOAD = os.getenv("RELOAD", "True") == "True"
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    UPLOADS_DIR = BASE_DIR / "uploads"
    LOGS_DIR = BASE_DIR / "logs"
    
    # Create directories if they don't exist
    UPLOADS_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Vector Database (Qdrant)
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "research_papers")
    
    # Embeddings
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", 384))
    
    # Chunking
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 512))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 100))
    MIN_CHUNK_LENGTH = int(os.getenv("MIN_CHUNK_LENGTH", 50))
    
    # RAG
    TOP_K = int(os.getenv("TOP_K", 5))
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.5))
    
    # LLM Configuration
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # ollama, deepseek, openai, openrouter
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")
    
    # Database (optional: for storing metadata)
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./papers.db")
    
    # PDF Processing
    MAX_PDF_SIZE_MB = int(os.getenv("MAX_PDF_SIZE_MB", 50))
    ALLOWED_EXTENSIONS = {"pdf"}
    
    # Search
    SEARCH_LIMIT = int(os.getenv("SEARCH_LIMIT", 1000))
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 0.3))


def setup_logging() -> logging.Logger:
    """
    Configure logging with both file and console handlers
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(__name__)
    
    # Set log level based on DEBUG setting
    log_level = logging.DEBUG if Config.DEBUG else logging.INFO
    logger.setLevel(log_level)
    
    # Formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [v0] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    log_file = Config.LOGS_DIR / "rag_system.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"[v0] Logging configured. Level: {logging.getLevelName(log_level)}")
    logger.debug(f"[v0] Log file: {log_file}")
    
    return logger


# Initialize logger
logger = setup_logging()

if __name__ == "__main__":
    logger.info("[v0] Config module loaded successfully")
