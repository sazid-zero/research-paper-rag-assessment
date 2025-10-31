"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChunkData(BaseModel):
    """Represents a text chunk from a paper"""
    text: str
    section: str = Field(default="Unknown", description="Section name (Abstract, Methods, etc)")
    page_number: int = Field(default=1, description="Page number in PDF")
    chunk_index: int = Field(default=0, description="Index of chunk in document")


class PaperMetadata(BaseModel):
    """Paper metadata"""
    title: str = Field(description="Paper title")
    authors: List[str] = Field(default_factory=list, description="List of authors")
    year: Optional[int] = Field(default=None, description="Publication year")
    file_name: str = Field(description="Original PDF filename")
    file_size: int = Field(description="File size in bytes")
    upload_date: datetime = Field(default_factory=datetime.now)
    num_pages: int = Field(default=0, description="Total pages in PDF")
    total_chunks: int = Field(default=0, description="Total chunks created")
    abstract: Optional[str] = Field(default=None, description="Paper abstract")


class Citation(BaseModel):
    """Citation information for query response"""
    paper_id: str = Field(description="Unique paper identifier")
    paper_title: str = Field(description="Title of source paper")
    section: str = Field(description="Section where information came from")
    page_number: int = Field(description="Page number")
    relevance_score: float = Field(ge=0, le=1, description="Relevance score 0-1")
    text_snippet: str = Field(description="Relevant text excerpt")


class QueryRequest(BaseModel):
    """Request body for query endpoint"""
    question: str = Field(description="User's question about papers")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results")
    paper_ids: Optional[List[str]] = Field(default=None, description="Optional: limit to specific papers")
    use_summary: bool = Field(default=True, description="Use LLM to summarize results")


class QueryResponse(BaseModel):
    """Response body for query endpoint"""
    answer: str = Field(description="Generated answer to question")
    citations: List[Citation] = Field(description="List of citations/sources")
    sources_used: List[str] = Field(description="List of paper titles used")
    confidence: float = Field(ge=0, le=1, description="Confidence score 0-1")
    response_time_ms: float = Field(description="Response time in milliseconds")
    model_used: str = Field(description="Which LLM model was used")


class UploadResponse(BaseModel):
    """Response after paper upload"""
    paper_id: str = Field(description="Unique paper identifier")
    message: str = Field(description="Success message")
    metadata: PaperMetadata = Field(description="Paper metadata")
    chunks_created: int = Field(description="Number of chunks created")


class PaperInfo(BaseModel):
    """Information about a stored paper"""
    paper_id: str = Field(description="Unique paper identifier")
    metadata: PaperMetadata = Field(description="Paper metadata")


class QueryHistory(BaseModel):
    """Query history record"""
    query_id: str = Field(description="Unique query identifier")
    question: str = Field(description="Query question")
    papers_used: List[str] = Field(description="Papers that were searched")
    answer: str = Field(description="Generated answer")
    confidence: float = Field(description="Confidence score")
    timestamp: datetime = Field(description="When query was made")
    response_time_ms: float = Field(description="Response time")


class AnalyticsData(BaseModel):
    """Analytics data"""
    total_papers: int = Field(description="Total papers in system")
    total_chunks: int = Field(description="Total chunks indexed")
    total_queries: int = Field(description="Total queries processed")
    avg_response_time_ms: float = Field(description="Average response time")
    popular_topics: List[Dict[str, Any]] = Field(description="Most queried topics")


class ErrorResponse(BaseModel):
    """Error response"""
    error: str = Field(description="Error message")
    details: Optional[str] = Field(default=None, description="Additional error details")
    request_id: Optional[str] = Field(default=None, description="Request tracking ID")
