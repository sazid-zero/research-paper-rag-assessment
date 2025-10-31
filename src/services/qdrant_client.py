"""
Qdrant vector database client
Handle vector storage and retrieval
"""
import logging
import uuid
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from src.config import Config, logger


class QdrantVectorClient:
    """Manage vectors in Qdrant"""
    
    def __init__(self):
        self.logger = logger
        self.host = Config.QDRANT_HOST
        self.port = Config.QDRANT_PORT
        self.collection_name = Config.QDRANT_COLLECTION
        self.embedding_dim = Config.EMBEDDING_DIMENSION
        
        self.logger.info(f"Connecting to Qdrant at {self.host}:{self.port}")
        
        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            self.logger.info("Successfully connected to Qdrant")
            self._ensure_collection_exists()
        except Exception as e:
            self.logger.error(f"Failed to connect to Qdrant: {str(e)}", exc_info=True)
            raise
    
    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist"""
        self.logger.debug(f"Checking if collection '{self.collection_name}' exists")
        
        try:
            collections = self.client.get_collections()
            existing_collections = [col.name for col in collections.collections]
            
            if self.collection_name not in existing_collections:
                self.logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                self.logger.info(f"Collection created successfully")
            else:
                self.logger.debug(f"Collection already exists")
        except Exception as e:
            self.logger.error(f"Error ensuring collection: {str(e)}", exc_info=True)
            raise
    
    def add_vectors(self, texts: List[str], embeddings: List, metadata: List[Dict]) -> List[str]:
        """
        Add vectors to collection
        
        Args:
            texts: List of text chunks
            embeddings: List of embedding vectors
            metadata: List of metadata dictionaries
            
        Returns:
            List of point IDs
        """
        self.logger.info(f"Adding {len(texts)} vectors to Qdrant")
        self.logger.info(f"Embedding type: {type(embeddings)}, shape info available: {hasattr(embeddings, 'shape')}")
        
        try:
            points = []
            point_ids = []
            
            for i, (text, embedding, meta) in enumerate(zip(texts, embeddings, metadata)):
                self.logger.debug(f"Processing chunk {i}: type={type(embedding)}, len/shape={len(embedding) if hasattr(embedding, '__len__') else 'N/A'}")
                
                point_id = str(uuid.uuid4())
                point_ids.append(point_id)
                
                # Create point with vector and metadata
                point = PointStruct(
                    id=point_id,
                    vector=embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding),
                    payload={
                        "text": text,
                        "paper_id": meta.get("paper_id", "unknown"),
                        "paper_title": meta.get("paper_title", "unknown"),
                        "section": meta.get("section", "unknown"),
                        "page_number": meta.get("page_number", 1),
                        "chunk_index": meta.get("chunk_index", 0)
                    }
                )
                points.append(point)
            
            self.logger.info(f"Created {len(points)} point objects, uploading to Qdrant...")
            
            # Upload to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            stats = self.client.get_collection(self.collection_name)
            self.logger.info(f"Successfully added {len(point_ids)} vectors. Collection now has {stats.points_count} total points")
            return point_ids
            
        except Exception as e:
            self.logger.error(f"Error adding vectors: {str(e)}", exc_info=True)
            raise
    
    def search(self, query_embedding: List, top_k: int = 5, paper_ids: Optional[List[str]] = None) -> List[Dict]:
        """
        Search for similar vectors
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            paper_ids: Optional filter by paper IDs
            
        Returns:
            List of search results with scores
        """
        self.logger.info(f"Searching for top {top_k} similar vectors")
        self.logger.debug(f"Query embedding type: {type(query_embedding)}, has tolist: {hasattr(query_embedding, 'tolist')}")
        
        try:
            # Convert to list if needed
            query_vec = query_embedding.tolist() if hasattr(query_embedding, 'tolist') else list(query_embedding)
            self.logger.debug(f"Query vector converted to list, length: {len(query_vec)}")
            
            # Check collection stats before search
            stats = self.client.get_collection(self.collection_name)
            self.logger.info(f"Collection has {stats.points_count} points before search")
            
            # Build filter if paper_ids provided
            query_filter = None
            if paper_ids:
                self.logger.debug(f"Filtering by paper IDs: {paper_ids}")
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="paper_id",
                            match=MatchValue(value=paper_id)
                        ) for paper_id in paper_ids
                    ]
                )
            
            # Search
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vec,
                query_filter=query_filter,
                limit=top_k
            )
            
            results = []
            for hit in search_result:
                results.append({
                    "point_id": hit.id,
                    "score": hit.score,
                    "text": hit.payload.get("text", ""),
                    "paper_id": hit.payload.get("paper_id", ""),
                    "paper_title": hit.payload.get("paper_title", ""),
                    "section": hit.payload.get("section", ""),
                    "page_number": hit.payload.get("page_number", 1)
                })
            
            self.logger.info(f"Search complete: found {len(results)} results")
            return results
            
        except Exception as e:
            self.logger.error(f"Search error: {str(e)}", exc_info=True)
            raise
    
    def delete_by_paper_id(self, paper_id: str) -> bool:
        """
        Delete all vectors for a paper
        
        Args:
            paper_id: Paper ID to delete
            
        Returns:
            Success status
        """
        self.logger.info(f"Deleting vectors for paper: {paper_id}")
        
        try:
            # Delete using filter
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="paper_id",
                            match=MatchValue(value=paper_id)
                        )
                    ]
                )
            )
            
            self.logger.info(f"Successfully deleted vectors for paper {paper_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting vectors: {str(e)}", exc_info=True)
            return False
    
    def get_collection_stats(self) -> Dict:
        """Get collection statistics"""
        self.logger.debug("Fetching collection statistics")
        
        try:
            stats = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "points_count": stats.points_count,
                "vectors_count": stats.vectors_count if hasattr(stats, 'vectors_count') else stats.points_count
            }
        except Exception as e:
            self.logger.error(f"Error getting stats: {str(e)}", exc_info=True)
            return {}
