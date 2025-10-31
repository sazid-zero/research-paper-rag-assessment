"""
RAG Pipeline
Orchestrate document retrieval and answer generation
"""
import logging
from typing import List, Dict, Optional
import requests
from src.services.embedding_service import EmbeddingService
from src.services.qdrant_client import QdrantVectorClient
from src.config import Config, logger


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline"""
    
    def __init__(self):
        self.logger = logger
        self.embedding_service = EmbeddingService()
        self.vector_client = QdrantVectorClient()
        self.llm_provider = Config.LLM_PROVIDER
        self.logger.info(f"[v0] RAG Pipeline initialized with LLM provider: {self.llm_provider}")
    
    def retrieve_context(self, query: str, top_k: int = 5, paper_ids: Optional[List[str]] = None) -> List[Dict]:
        """
        Retrieve relevant documents for query
        
        Args:
            query: User query
            top_k: Number of results
            paper_ids: Optional paper filters
            
        Returns:
            List of relevant chunks
        """
        self.logger.info(f"[v0] Retrieving context for query: {query[:100]}")
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.embed_text(query)
            self.logger.debug("[v0] Query embedding generated")
            
            # Search vector database
            results = self.vector_client.search(query_embedding, top_k, paper_ids)
            self.logger.info(f"[v0] Retrieved {len(results)} relevant chunks")
            
            return results
            
        except Exception as e:
            self.logger.error(f"[v0] Error retrieving context: {str(e)}", exc_info=True)
            raise
    
    def _call_ollama_llm(self, prompt: str) -> str:
        """Call local Ollama LLM with better timeout handling"""
        self.logger.debug(f"[v0] Calling Ollama LLM (model: {Config.OLLAMA_MODEL})")
        self.logger.info(f"[v0] LLM prompt length: {len(prompt)} characters")
        
        try:
            url = f"{Config.OLLAMA_BASE_URL}/api/generate"
            payload = {
                "model": Config.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7,  # added temperature for better responses
                "top_p": 0.9
            }
            
            self.logger.debug(f"[v0] Sending request to {url}")
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            answer = result.get("response", "").strip()
            self.logger.debug(f"[v0] Ollama response received ({len(answer)} chars)")
            
            if not answer:
                self.logger.warning("[v0] Ollama returned empty response")
                return "Sorry, I could not generate a response. Please try again."
            
            return answer
            
        except requests.exceptions.Timeout:
            self.logger.error("[v0] Ollama request timed out after 300 seconds")
            return "The LLM took too long to respond. Please try a simpler question."
        except requests.exceptions.ConnectionError:
            self.logger.error(f"[v0] Cannot connect to Ollama at {Config.OLLAMA_BASE_URL}")
            return "Error: Cannot connect to LLM service. Make sure Ollama is running."
        except Exception as e:
            self.logger.error(f"[v0] Ollama LLM error: {str(e)}", exc_info=True)
            raise
    
    def _call_deepseek_llm(self, prompt: str) -> str:
        """Call DeepSeek API"""
        self.logger.debug("[v0] Calling DeepSeek LLM")
        
        try:
            url = f"{Config.DEEPSEEK_API_URL}/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {Config.DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            answer = result["choices"][0]["message"]["content"].strip()
            self.logger.debug(f"[v0] DeepSeek response received ({len(answer)} chars)")
            
            return answer
            
        except requests.exceptions.Timeout:
            self.logger.error("[v0] DeepSeek request timed out")
            return "The LLM took too long to respond. Please try again."
        except requests.exceptions.ConnectionError:
            self.logger.error("[v0] Cannot connect to DeepSeek API")
            return "Error: Cannot connect to DeepSeek service."
        except Exception as e:
            self.logger.error(f"[v0] DeepSeek LLM error: {str(e)}", exc_info=True)
            raise
    
    def _call_openai_llm(self, prompt: str) -> str:
        """Call OpenAI API"""
        self.logger.debug("[v0] Calling OpenAI LLM")
        
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {Config.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            answer = result["choices"][0]["message"]["content"].strip()
            self.logger.debug(f"[v0] OpenAI response received ({len(answer)} chars)")
            
            return answer
            
        except requests.exceptions.Timeout:
            self.logger.error("[v0] OpenAI request timed out")
            return "The LLM took too long to respond. Please try again."
        except requests.exceptions.ConnectionError:
            self.logger.error("[v0] Cannot connect to OpenAI API")
            return "Error: Cannot connect to OpenAI service."
        except Exception as e:
            self.logger.error(f"[v0] OpenAI LLM error: {str(e)}", exc_info=True)
            raise
    
    def _call_openrouter_llm(self, prompt: str) -> str:
        """Call OpenRouter API (free DeepSeek or other models)"""
        self.logger.debug("[v0] Calling OpenRouter LLM")
        
        try:
            url = f"{Config.OPENROUTER_API_URL}/chat/completions"
            headers = {
                "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/UpscaleBD/research-paper-rag-assessment"
            }
            payload = {
                "model": Config.OPENROUTER_MODEL,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            
            self.logger.debug(f"[v0] Sending request to OpenRouter with model: {Config.OPENROUTER_MODEL}")
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            self.logger.debug(f"[v0] OpenRouter response status: {response.status_code}")
            response.raise_for_status()
            
            result = response.json()
            answer = result["choices"][0]["message"]["content"].strip()
            self.logger.debug(f"[v0] OpenRouter response received ({len(answer)} chars)")
            
            return answer
            
        except requests.exceptions.Timeout:
            self.logger.error("[v0] OpenRouter request timed out")
            return "The LLM took too long to respond. Please try again."
        except requests.exceptions.ConnectionError:
            self.logger.error("[v0] Cannot connect to OpenRouter API")
            return "Error: Cannot connect to OpenRouter service."
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"[v0] OpenRouter HTTP error: {response.status_code} - {response.text}")
            return f"Error: OpenRouter API error - {response.status_code}"
        except Exception as e:
            self.logger.error(f"[v0] OpenRouter LLM error: {str(e)}", exc_info=True)
            raise
    
    def generate_answer(self, query: str, context: List[Dict]) -> tuple[str, float]:
        """
        Generate answer using context and LLM
        
        Args:
            query: User query
            context: Retrieved context chunks
            
        Returns:
            Tuple of (answer, confidence_score)
        """
        self.logger.info(f"[v0] Generating answer from {len(context)} context chunks")
        
        try:
            # Build context string
            context_text = "\n\n".join([
                f"From '{chunk['paper_title']}' ({chunk['section']}, p.{chunk['page_number']}):\n{chunk['text']}"
                for chunk in context
            ])
            
            # Build prompt - optimized for llama3
            prompt = f"""Based on the following research paper excerpts, answer the question:

Question: {query}

Context:
{context_text}

Answer: Please provide a clear and comprehensive answer based on the context above. If the information is not in the context, say "This information is not available in the provided papers."
"""
            
            self.logger.debug("[v0] Prompt prepared, calling LLM")
            self.logger.debug(f"[v0] Context chunks used: {len(context)}")
            
            # Call appropriate LLM
            if self.llm_provider == "ollama":
                answer = self._call_ollama_llm(prompt)
            elif self.llm_provider == "deepseek":
                answer = self._call_deepseek_llm(prompt)
            elif self.llm_provider == "openai":
                answer = self._call_openai_llm(prompt)
            elif self.llm_provider == "openrouter":
                answer = self._call_openrouter_llm(prompt)
            else:
                self.logger.warning(f"[v0] Unknown LLM provider: {self.llm_provider}, using ollama")
                answer = self._call_ollama_llm(prompt)
            
            # Calculate confidence based on context relevance scores
            avg_score = sum(c["score"] for c in context) / len(context) if context else 0
            confidence = min(avg_score, 1.0)
            
            self.logger.info(f"[v0] Answer generated (length: {len(answer)}, confidence: {confidence:.2f})")
            return answer, confidence
            
        except Exception as e:
            self.logger.error(f"[v0] Answer generation failed: {str(e)}", exc_info=True)
            raise
    
    def process_query(self, query: str, top_k: int = 5, paper_ids: Optional[List[str]] = None) -> Dict:
        """
        Full RAG processing
        
        Args:
            query: User query
            top_k: Number of contexts
            paper_ids: Optional paper filters
            
        Returns:
            Query result with answer and citations
        """
        self.logger.info(f"[v0] Processing query through RAG pipeline")
        
        try:
            # Retrieve context
            context = self.retrieve_context(query, top_k, paper_ids)
            
            if not context:
                self.logger.warning("[v0] No relevant context found")
                return {
                    "answer": "No relevant information found in the papers.",
                    "citations": [],
                    "sources_used": [],
                    "confidence": 0.0
                }
            
            # Generate answer
            answer, confidence = self.generate_answer(query, context)
            
            # Extract citations
            citations = [
                {
                    "paper_id": c["paper_id"],
                    "paper_title": c["paper_title"],
                    "section": c["section"],
                    "page_number": c["page_number"],
                    "relevance_score": c["score"],
                    "text_snippet": c["text"][:200] + "..." if len(c["text"]) > 200 else c["text"]
                }
                for c in context
            ]
            
            # Unique sources
            sources = list(set(c["paper_title"] for c in context))
            
            self.logger.info(f"[v0] Query processing complete with {len(sources)} unique sources")
            
            return {
                "answer": answer,
                "citations": citations,
                "sources_used": sources,
                "confidence": confidence
            }
            
        except Exception as e:
            self.logger.error(f"[v0] Query processing failed: {str(e)}", exc_info=True)
            raise
