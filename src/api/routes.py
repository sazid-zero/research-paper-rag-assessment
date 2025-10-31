"""
FastAPI routes
API endpoints for paper management and querying
"""
import logging
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
import time
from src.services.pdf_processor import PDFProcessor
from src.services.embedding_service import EmbeddingService
from src.services.qdrant_client import QdrantVectorClient
from src.services.rag_pipeline import RAGPipeline
from src.services.database_service import DatabaseService
from src.models.schemas import (
    QueryRequest, QueryResponse, Citation, UploadResponse,
    PaperMetadata, PaperInfo, ErrorResponse
)
from src.config import Config, logger
from datetime import datetime
from pathlib import Path


router = APIRouter(prefix="/api", tags=["API"])

# Initialize services
pdf_processor = PDFProcessor()
embedding_service = EmbeddingService()
vector_client = QdrantVectorClient()
rag_pipeline = RAGPipeline()
db_service = DatabaseService()


@router.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info("API routes loaded")
    from src.services.database_service import init_db
    init_db()


@router.post("/papers/upload", response_model=UploadResponse)
async def upload_paper(file: UploadFile = File(...)):
    """
    Upload and process a research paper
    
    Args:
        file: PDF file to upload
        
    Returns:
        Upload response with paper metadata
    """
    logger.info(f"Received paper upload: {file.filename}")
    
    start_time = time.time()
    
    try:
        # Validate file
        if not file.filename.lower().endswith('.pdf'):
            logger.warning(f"Invalid file type: {file.filename}")
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Check file size
        contents = await file.read()
        file_size_bytes = len(contents)
        file_size_mb = file_size_bytes / (1024 * 1024)
        if file_size_mb > Config.MAX_PDF_SIZE_MB:
            logger.warning(f"File too large: {file_size_mb}MB")
            raise HTTPException(status_code=413, detail=f"File too large (max {Config.MAX_PDF_SIZE_MB}MB)")
        
        # Save file
        paper_id = str(uuid.uuid4())
        file_path = Config.UPLOADS_DIR / f"{paper_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            f.write(contents)
        logger.debug(f"File saved to: {file_path}")
        
        # Process PDF
        chunks, metadata = pdf_processor.process_pdf(str(file_path))
        logger.info(f"PDF processed: {len(chunks)} chunks created")
        
        # Generate embeddings
        texts = [chunk.text for chunk in chunks]
        embeddings = embedding_service.embed_texts(texts)
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Prepare metadata for storage
        chunk_metadata = []
        for i, chunk in enumerate(chunks):
            chunk_metadata.append({
                "paper_id": paper_id,
                "paper_title": metadata.get("title", file.filename),
                "section": chunk.section,
                "page_number": chunk.page_number,
                "chunk_index": i
            })
        
        # Store in vector database
        point_ids = vector_client.add_vectors(texts, embeddings, chunk_metadata)
        logger.info(f"Stored {len(point_ids)} vectors in Qdrant")
        
        # Store paper metadata in database
        paper_metadata = PaperMetadata(
            title=metadata.get("title", file.filename),
            authors=metadata.get("authors", []),
            year=metadata.get("year"),
            file_name=file.filename,
            file_size=int(file_size_bytes),
            num_pages=metadata.get("num_pages", 0),
            total_chunks=len(chunks),
            abstract=metadata.get("abstract")
        )
        
        db_service.create_paper(
            paper_id=paper_id,
            title=paper_metadata.title,
            authors=paper_metadata.authors,
            year=paper_metadata.year,
            file_name=paper_metadata.file_name,
            file_size=paper_metadata.file_size,
            num_pages=paper_metadata.num_pages,
            total_chunks=paper_metadata.total_chunks,
            abstract=paper_metadata.abstract,
            file_path=str(file_path),
            point_ids=point_ids
        )
        
        logger.info(f"Paper {paper_id} registered successfully")
        
        elapsed_time = time.time() - start_time
        logger.info(f"Upload completed in {elapsed_time:.2f}s")
        
        return UploadResponse(
            paper_id=paper_id,
            message=f"Successfully uploaded and processed {file.filename}",
            metadata=paper_metadata,
            chunks_created=len(chunks)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/query", response_model=QueryResponse)
async def query_papers(request: QueryRequest):
    """
    Query papers using RAG
    
    Args:
        request: Query request with question and options
        
    Returns:
        Query response with answer and citations
    """
    logger.info(f"Received query: {request.question[:100]}")
    
    start_time = time.time()
    
    try:
        # Validate paper IDs if provided
        if request.paper_ids:
            invalid_ids = []
            for pid in request.paper_ids:
                if not db_service.get_paper(pid):
                    invalid_ids.append(pid)
            if invalid_ids:
                logger.warning(f"Invalid paper IDs: {invalid_ids}")
                raise HTTPException(status_code=404, detail=f"Paper not found: {invalid_ids}")
        
        # Process query through RAG pipeline
        result = rag_pipeline.process_query(
            query=request.question,
            top_k=request.top_k,
            paper_ids=request.paper_ids
        )
        
        # Build citations
        citations = [
            Citation(
                paper_id=c["paper_id"],
                paper_title=c["paper_title"],
                section=c["section"],
                page_number=c["page_number"],
                relevance_score=c["relevance_score"],
                text_snippet=c["text_snippet"]
            )
            for c in result["citations"]
        ]
        
        elapsed_time = time.time() - start_time
        
        query_id = str(uuid.uuid4())
        db_service.create_query(
            query_id=query_id,
            question=request.question,
            answer=result["answer"],
            sources_used=result["sources_used"],
            confidence=result["confidence"],
            response_time_ms=elapsed_time * 1000,
            model_used=Config.LLM_PROVIDER
        )
        
        logger.info(f"Query completed in {elapsed_time:.2f}s")
        
        return QueryResponse(
            answer=result["answer"],
            citations=citations,
            sources_used=result["sources_used"],
            confidence=result["confidence"],
            response_time_ms=elapsed_time * 1000,
            model_used=Config.LLM_PROVIDER
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/papers", response_model=dict)
async def list_papers():
    """List all uploaded papers"""
    logger.debug("Listing papers")
    
    try:
        papers_list = db_service.get_all_papers()
        
        papers = [
            {
                "paper_id": p.paper_id,
                "metadata": {
                    "title": p.title,
                    "authors": p.authors,
                    "year": p.year,
                    "file_name": p.file_name,
                    "chunks": p.total_chunks,
                    "upload_date": p.upload_date.isoformat()
                }
            }
            for p in papers_list
        ]
        
        return {
            "total_papers": len(papers_list),
            "papers": papers
        }
        
    except Exception as e:
        logger.error(f"Error listing papers: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/papers/{paper_id}", response_model=PaperInfo)
async def get_paper(paper_id: str):
    """Get paper details"""
    logger.debug(f"Getting paper: {paper_id}")
    
    try:
        paper = db_service.get_paper(paper_id)
        
        if not paper:
            logger.warning(f"Paper not found: {paper_id}")
            raise HTTPException(status_code=404, detail="Paper not found")
        
        return PaperInfo(
            paper_id=paper_id,
            metadata=PaperMetadata(
                title=paper.title,
                authors=paper.authors,
                year=paper.year,
                file_name=paper.file_name,
                file_size=paper.file_size,
                num_pages=paper.num_pages,
                total_chunks=paper.total_chunks,
                abstract=paper.abstract
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting paper: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/papers/{paper_id}")
async def delete_paper(paper_id: str):
    """Delete a paper and its vectors"""
    logger.info(f"Deleting paper: {paper_id}")
    
    try:
        paper = db_service.get_paper(paper_id)
        
        if not paper:
            logger.warning(f"Paper not found: {paper_id}")
            raise HTTPException(status_code=404, detail="Paper not found")
        
        # Delete from vector database
        vector_client.delete_by_paper_id(paper_id)
        
        # Delete file
        file_path = Path(paper.file_path)
        if file_path.exists():
            file_path.unlink()
            logger.debug(f"Deleted file: {file_path}")
        
        db_service.delete_paper(paper_id)
        
        logger.info(f"Paper {paper_id} deleted successfully")
        
        return {"message": f"Paper {paper_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/papers/{paper_id}/stats")
async def get_paper_stats(paper_id: str):
    """Get paper statistics"""
    logger.debug(f"Getting stats for paper: {paper_id}")
    
    try:
        paper = db_service.get_paper(paper_id)
        
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        return {
            "paper_id": paper_id,
            "title": paper.title,
            "file_name": paper.file_name,
            "total_pages": paper.num_pages,
            "total_chunks": paper.total_chunks,
            "vector_points": len(paper.point_ids),
            "upload_date": paper.upload_date.isoformat(),
            "file_size_bytes": paper.file_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stats error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
async def get_analytics():
    """Get system analytics"""
    logger.debug("Fetching system analytics")
    
    try:
        papers_list = db_service.get_all_papers()
        stats = vector_client.get_collection_stats()
        
        return {
            "total_papers": len(papers_list),
            "total_chunks": sum(p.total_chunks for p in papers_list),
            "vector_store_stats": stats,
            "embedding_model": Config.EMBEDDING_MODEL,
            "llm_provider": Config.LLM_PROVIDER
        }
        
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check called")
    
    return {
        "status": "healthy",
        "app_name": Config.APP_NAME,
        "version": Config.APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }
