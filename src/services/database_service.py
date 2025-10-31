"""
Database service for persistent storage of paper metadata
Uses SQLite with SQLAlchemy ORM
"""
import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Float, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from src.config import Config, logger

# Create SQLAlchemy base
Base = declarative_base()

engine = create_engine(
    Config.NEON_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in Config.NEON_DATABASE_URL else {},
    echo=Config.DEBUG
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class PaperRecord(Base):
    """SQLAlchemy model for paper metadata"""
    __tablename__ = "papers"
    
    paper_id = Column(String(36), primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    authors = Column(JSON, default=[])  # Store as JSON array
    year = Column(Integer, nullable=True)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    num_pages = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    abstract = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=False)
    point_ids = Column(JSON, default=[])  # Vector IDs in Qdrant
    upload_date = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class QueryRecord(Base):
    """SQLAlchemy model for query history"""
    __tablename__ = "queries"
    
    query_id = Column(String(36), primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources_used = Column(JSON, default=[])  # List of paper IDs used
    confidence = Column(Float, default=0.0)
    response_time_ms = Column(Float, default=0.0)
    model_used = Column(String(50), default="")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}", exc_info=True)
        raise


class DatabaseService:
    """Service for database operations"""
    
    @staticmethod
    def get_session() -> Session:
        """Get database session"""
        return SessionLocal()
    
    @staticmethod
    def create_paper(
        paper_id: str,
        title: str,
        authors: List[str],
        year: Optional[int],
        file_name: str,
        file_size: int,
        num_pages: int,
        total_chunks: int,
        abstract: Optional[str],
        file_path: str,
        point_ids: List[str]
    ) -> PaperRecord:
        """Create a new paper record"""
        db = DatabaseService.get_session()
        try:
            paper = PaperRecord(
                paper_id=paper_id,
                title=title,
                authors=authors,
                year=year,
                file_name=file_name,
                file_size=file_size,
                num_pages=num_pages,
                total_chunks=total_chunks,
                abstract=abstract,
                file_path=file_path,
                point_ids=point_ids
            )
            db.add(paper)
            db.commit()
            db.refresh(paper)
            logger.info(f"Paper {paper_id} created in database")
            return paper
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating paper: {str(e)}", exc_info=True)
            raise
        finally:
            db.close()
    
    @staticmethod
    def get_paper(paper_id: str) -> Optional[PaperRecord]:
        """Get paper by ID"""
        db = DatabaseService.get_session()
        try:
            paper = db.query(PaperRecord).filter(PaperRecord.paper_id == paper_id).first()
            return paper
        finally:
            db.close()
    
    @staticmethod
    def get_all_papers() -> List[PaperRecord]:
        """Get all papers"""
        db = DatabaseService.get_session()
        try:
            papers = db.query(PaperRecord).order_by(PaperRecord.upload_date.desc()).all()
            return papers
        finally:
            db.close()
    
    @staticmethod
    def delete_paper(paper_id: str) -> bool:
        """Delete paper by ID"""
        db = DatabaseService.get_session()
        try:
            paper = db.query(PaperRecord).filter(PaperRecord.paper_id == paper_id).first()
            if paper:
                db.delete(paper)
                db.commit()
                logger.info(f"Paper {paper_id} deleted from database")
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting paper: {str(e)}", exc_info=True)
            raise
        finally:
            db.close()
    
    @staticmethod
    def create_query(
        query_id: str,
        question: str,
        answer: str,
        sources_used: List[str],
        confidence: float,
        response_time_ms: float,
        model_used: str
    ) -> QueryRecord:
        """Create a new query record"""
        db = DatabaseService.get_session()
        try:
            query = QueryRecord(
                query_id=query_id,
                question=question,
                answer=answer,
                sources_used=sources_used,
                confidence=confidence,
                response_time_ms=response_time_ms,
                model_used=model_used
            )
            db.add(query)
            db.commit()
            db.refresh(query)
            return query
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating query record: {str(e)}", exc_info=True)
            raise
        finally:
            db.close()
    
    @staticmethod
    def get_recent_queries(limit: int = 10) -> List[QueryRecord]:
        """Get recent queries"""
        db = DatabaseService.get_session()
        try:
            queries = db.query(QueryRecord).order_by(QueryRecord.created_at.desc()).limit(limit).all()
            return queries
        finally:
            db.close()
