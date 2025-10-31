"""
PDF processing service
Handles PDF extraction, text processing, and intelligent chunking
"""
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import PyPDF2
from src.models.schemas import ChunkData
from src.config import Config, logger


class PDFProcessor:
    """Process and chunk PDF documents"""
    
    def __init__(self):
        self.logger = logger
        self.chunk_size = Config.CHUNK_SIZE
        self.chunk_overlap = Config.CHUNK_OVERLAP
        self.min_chunk_length = Config.MIN_CHUNK_LENGTH
        self.logger.info("[v0] PDFProcessor initialized")
    
    def extract_text_from_pdf(self, pdf_path: str) -> Tuple[str, Dict]:
        """
        Extract text from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (full_text, metadata)
        """
        self.logger.debug(f"[v0] Extracting text from: {pdf_path}")
        
        try:
            full_text = ""
            metadata = {
                "num_pages": 0,
                "authors": [],
                "title": "Unknown",
                "year": None
            }
            
            with open(pdf_path, 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                metadata["num_pages"] = len(reader.pages)
                
                self.logger.debug(f"[v0] PDF has {metadata['num_pages']} pages")
                
                # Extract text from each page
                for page_num, page in enumerate(reader.pages):
                    try:
                        text = page.extract_text()
                        full_text += f"\n[PAGE {page_num + 1}]\n{text}"
                    except Exception as e:
                        self.logger.warning(f"[v0] Error extracting page {page_num + 1}: {str(e)}")
                
                # Try to extract metadata
                if reader.metadata:
                    self.logger.debug(f"[v0] PDF metadata found: {reader.metadata}")
                    if reader.metadata.title:
                        metadata["title"] = reader.metadata.title
                    if reader.metadata.author:
                        metadata["authors"] = [reader.metadata.author]
            
            self.logger.info(f"[v0] Successfully extracted {len(full_text)} characters from PDF")
            return full_text, metadata
            
        except Exception as e:
            self.logger.error(f"[v0] Error extracting PDF text: {str(e)}", exc_info=True)
            raise
    
    def identify_sections(self, text: str) -> Dict[str, str]:
        """
        Identify major sections in paper (Abstract, Methods, Results, etc)
        
        Args:
            text: Full paper text
            
        Returns:
            Dictionary mapping section names to text
        """
        self.logger.debug("[v0] Identifying paper sections")
        
        sections = {}
        section_keywords = {
            "abstract": ["abstract", "summary"],
            "introduction": ["introduction", "intro", "background"],
            "methodology": ["methodology", "methods", "approach", "system design"],
            "results": ["results", "findings", "evaluation", "experiments"],
            "discussion": ["discussion", "analysis", "limitations"],
            "conclusion": ["conclusion", "conclusions", "future work"],
            "references": ["references", "citations", "bibliography"]
        }
        
        lines = text.split('\n')
        current_section = "other"
        section_text = {key: "" for key in section_keywords.keys()}
        section_text["other"] = ""
        
        for line in lines:
            # Check if line starts a new section
            line_lower = line.lower().strip()
            found_section = False
            
            for section_name, keywords in section_keywords.items():
                if any(keyword in line_lower for keyword in keywords):
                    if len(line_lower) < 100:  # Likely a section header
                        current_section = section_name
                        found_section = True
                        break
            
            section_text[current_section] += line + "\n"
        
        # Only keep non-empty sections
        sections = {k: v for k, v in section_text.items() if v.strip()}
        self.logger.info(f"[v0] Identified {len(sections)} sections: {list(sections.keys())}")
        
        return sections
    
    def chunk_text(self, text: str, section_name: str = "Unknown") -> List[ChunkData]:
        """
        Split text into chunks with overlap
        
        Args:
            text: Text to chunk
            section_name: Section name for metadata
            
        Returns:
            List of ChunkData objects
        """
        self.logger.debug(f"[v0] Chunking text (section: {section_name}, length: {len(text)})")
        
        chunks = []
        words = text.split()
        
        if len(words) < self.min_chunk_length:
            self.logger.debug(f"[v0] Text too short ({len(words)} words), creating single chunk")
            if text.strip():
                chunks.append(ChunkData(
                    text=text.strip(),
                    section=section_name,
                    page_number=1,
                    chunk_index=0
                ))
            return chunks
        
        # Create overlapping chunks
        chunk_index = 0
        i = 0
        
        while i < len(words):
            # Get chunk_size words
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            if len(chunk_text.strip()) >= self.min_chunk_length:
                chunks.append(ChunkData(
                    text=chunk_text.strip(),
                    section=section_name,
                    page_number=1,
                    chunk_index=chunk_index
                ))
                chunk_index += 1
            
            # Move forward by (chunk_size - overlap) words
            i += self.chunk_size - self.chunk_overlap
        
        self.logger.info(f"[v0] Created {len(chunks)} chunks from {len(words)} words")
        return chunks
    
    def process_pdf(self, pdf_path: str) -> Tuple[List[ChunkData], Dict]:
        """
        Complete PDF processing pipeline
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (chunks, metadata)
        """
        self.logger.info(f"[v0] Starting PDF processing for: {pdf_path}")
        
        try:
            # Extract text
            full_text, metadata = self.extract_text_from_pdf(pdf_path)
            
            # Identify sections
            sections = self.identify_sections(full_text)
            
            # Chunk each section
            all_chunks = []
            for section_name, section_text in sections.items():
                chunks = self.chunk_text(section_text, section_name)
                all_chunks.extend(chunks)
            
            metadata["total_chunks"] = len(all_chunks)
            self.logger.info(f"[v0] PDF processing complete: {len(all_chunks)} total chunks")
            
            return all_chunks, metadata
            
        except Exception as e:
            self.logger.error(f"[v0] PDF processing failed: {str(e)}", exc_info=True)
            raise
