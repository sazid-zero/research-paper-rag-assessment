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

# Simple in-memory storage for paper metadata (in production use database)
papers_db: dict = {}


@router.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info("[v0] API routes loaded")


@router.post("/papers/upload", response_model=UploadResponse)
async def upload_paper(file: UploadFile = File(...)):
    """
    Upload and process a research paper
    
    Args:
        file: PDF file to upload
        
    Returns:
        Upload response with paper metadata
    """
    logger.info(f"[v0] Received paper upload: {file.filename}")
    
    start_time = time.time()
    
    try:
        # Validate file
        if not file.filename.lower().endswith('.pdf'):
            logger.warning(f"[v0] Invalid file type: {file.filename}")
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Check file size
        contents = await file.read()
        file_size_bytes = len(contents)  # Store size in bytes as integer
        file_size_mb = file_size_bytes / (1024 * 1024)
        if file_size_mb > Config.MAX_PDF_SIZE_MB:
            logger.warning(f"[v0] File too large: {file_size_mb}MB")
            raise HTTPException(status_code=413, detail=f"File too large (max {Config.MAX_PDF_SIZE_MB}MB)")
        
        # Save file
        paper_id = str(uuid.uuid4())
        file_path = Config.UPLOADS_DIR / f"{paper_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            f.write(contents)
        logger.debug(f"[v0] File saved to: {file_path}")
        
        # Process PDF
        chunks, metadata = pdf_processor.process_pdf(str(file_path))
        logger.info(f"[v0] PDF processed: {len(chunks)} chunks created")
        
        # Generate embeddings
        texts = [chunk.text for chunk in chunks]
        embeddings = embedding_service.embed_texts(texts)
        logger.info(f"[v0] Generated {len(embeddings)} embeddings")
        
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
        logger.info(f"[v0] Stored {len(point_ids)} vectors in Qdrant")
        
        # Store paper metadata
        paper_metadata = PaperMetadata(
            title=metadata.get("title", file.filename),
            authors=metadata.get("authors", []),
            year=metadata.get("year"),
            file_name=file.filename,
            file_size=int(file_size_bytes),  # Convert to int (bytes)
            num_pages=metadata.get("num_pages", 0),
            total_chunks=len(chunks),
            abstract=metadata.get("abstract")
        )
        
        papers_db[paper_id] = {
            "metadata": paper_metadata,
            "file_path": str(file_path),
            "point_ids": point_ids
        }
        
        logger.info(f"[v0] Paper {paper_id} registered successfully")
        
        elapsed_time = time.time() - start_time
        logger.info(f"[v0] Upload completed in {elapsed_time:.2f}s")
        
        return UploadResponse(
            paper_id=paper_id,
            message=f"Successfully uploaded and processed {file.filename}",
            metadata=paper_metadata,
            chunks_created=len(chunks)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[v0] Upload error: {str(e)}", exc_info=True)
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
    logger.info(f"[v0] Received query: {request.question[:100]}")
    
    start_time = time.time()
    
    try:
        # Validate paper IDs if provided
        if request.paper_ids:
            invalid_ids = [pid for pid in request.paper_ids if pid not in papers_db]
            if invalid_ids:
                logger.warning(f"[v0] Invalid paper IDs: {invalid_ids}")
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
        logger.info(f"[v0] Query completed in {elapsed_time:.2f}s")
        
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
        logger.error(f"[v0] Query error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/papers", response_model=dict)
async def list_papers():
    """List all uploaded papers"""
    logger.debug(f"[v0] Listing papers ({len(papers_db)} total)")
    
    try:
        papers = [
            {
                "paper_id": pid,
                "metadata": {
                    "title": p["metadata"].title,
                    "authors": p["metadata"].authors,
                    "year": p["metadata"].year,
                    "file_name": p["metadata"].file_name,
                    "chunks": p["metadata"].total_chunks
                }
            }
            for pid, p in papers_db.items()
        ]
        
        return {
            "total_papers": len(papers_db),
            "papers": papers
        }
        
    except Exception as e:
        logger.error(f"[v0] Error listing papers: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/papers/{paper_id}", response_model=PaperInfo)
async def get_paper(paper_id: str):
    """Get paper details"""
    logger.debug(f"[v0] Getting paper: {paper_id}")
    
    if paper_id not in papers_db:
        logger.warning(f"[v0] Paper not found: {paper_id}")
        raise HTTPException(status_code=404, detail="Paper not found")
    
    paper = papers_db[paper_id]
    return PaperInfo(
        paper_id=paper_id,
        metadata=paper["metadata"]
    )


@router.delete("/papers/{paper_id}")
async def delete_paper(paper_id: str):
    """Delete a paper and its vectors"""
    logger.info(f"[v0] Deleting paper: {paper_id}")
    
    try:
        if paper_id not in papers_db:
            logger.warning(f"[v0] Paper not found: {paper_id}")
            raise HTTPException(status_code=404, detail="Paper not found")
        
        # Delete from vector database
        vector_client.delete_by_paper_id(paper_id)
        
        # Delete file
        paper = papers_db[paper_id]
        file_path = Path(paper["file_path"])
        if file_path.exists():
            file_path.unlink()
            logger.debug(f"[v0] Deleted file: {file_path}")
        
        # Remove from metadata
        del papers_db[paper_id]
        
        logger.info(f"[v0] Paper {paper_id} deleted successfully")
        
        return {"message": f"Paper {paper_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[v0] Delete error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/papers/{paper_id}/stats")
async def get_paper_stats(paper_id: str):
    """Get paper statistics"""
    logger.debug(f"[v0] Getting stats for paper: {paper_id}")
    
    try:
        if paper_id not in papers_db:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        paper = papers_db[paper_id]
        metadata = paper["metadata"]
        
        return {
            "paper_id": paper_id,
            "title": metadata.title,
            "file_name": metadata.file_name,
            "total_pages": metadata.num_pages,
            "total_chunks": metadata.total_chunks,
            "vector_points": len(paper["point_ids"]),
            "upload_date": metadata.upload_date.isoformat(),
            "file_size_mb": metadata.file_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[v0] Stats error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
async def get_analytics():
    """Get system analytics"""
    logger.debug("[v0] Fetching system analytics")
    
    try:
        stats = vector_client.get_collection_stats()
        
        return {
            "total_papers": len(papers_db),
            "total_chunks": sum(p["metadata"].total_chunks for p in papers_db.values()),
            "vector_store_stats": stats,
            "embedding_model": Config.EMBEDDING_MODEL,
            "llm_provider": Config.LLM_PROVIDER
        }
        
    except Exception as e:
        logger.error(f"[v0] Analytics error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("[v0] Health check called")
    
    return {
        "status": "healthy",
        "app_name": Config.APP_NAME,
        "version": Config.APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }
