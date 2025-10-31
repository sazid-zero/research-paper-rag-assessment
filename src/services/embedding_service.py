"""
Embedding service
Generate embeddings using sentence-transformers
"""
import logging
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from src.config import Config, logger


class EmbeddingService:
    """Generate embeddings for texts"""
    
    def __init__(self):
        self.logger = logger
        self.model_name = Config.EMBEDDING_MODEL
        self.logger.info(f"[v0] Loading embedding model: {self.model_name}")
        
        try:
            self.model = SentenceTransformer(self.model_name)
            self.logger.info(f"[v0] Embedding model loaded successfully")
        except Exception as e:
            self.logger.error(f"[v0] Failed to load embedding model: {str(e)}", exc_info=True)
            raise
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for single text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        self.logger.debug(f"[v0] Embedding single text (length: {len(text)})")
        
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            self.logger.debug(f"[v0] Successfully generated embedding (dim: {len(embedding)})")
            return embedding
        except Exception as e:
            self.logger.error(f"[v0] Error generating embedding: {str(e)}", exc_info=True)
            raise
    
    def embed_texts(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        self.logger.info(f"[v0] Embedding {len(texts)} texts")
        
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            self.logger.info(f"[v0] Successfully embedded {len(embeddings)} texts")
            self.logger.debug(f"[v0] Embeddings shape: {embeddings.shape if hasattr(embeddings, 'shape') else 'N/A'}")
            self.logger.debug(f"[v0] First embedding type: {type(embeddings[0])}, first 5 values: {embeddings[0][:5] if len(embeddings) > 0 else 'N/A'}")
            return embeddings
        except Exception as e:
            self.logger.error(f"[v0] Error embedding multiple texts: {str(e)}", exc_info=True)
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get embedding vector dimension"""
        test_embedding = self.embed_text("test")
        return len(test_embedding)
