"""Text chunking strategies."""
from typing import List, Tuple
import re
from loguru import logger


class BaseChunker:
    """Base text chunker."""
    
    def chunk(self, text: str, **kwargs) -> List[Tuple[str, int]]:
        """Chunk text and return list of (chunk_text, start_index) tuples."""
        raise NotImplementedError


class ParagraphChunker(BaseChunker):
    """Split text by paragraphs."""
    
    def chunk(self, text: str, **kwargs) -> List[Tuple[str, int]]:
        """Split text by paragraph boundaries."""
        # Split by double newlines or single newlines with whitespace
        paragraphs = re.split(r'\n\s*\n|\n(?=\s*[A-Z0-9]|\s*[-*])', text)
        
        chunks = []
        for para in paragraphs:
            para = para.strip()
            if para and len(para) > 10:  # Skip very short paragraphs
                chunks.append((para, text.find(para)))
        
        return chunks


class FixedSizeChunker(BaseChunker):
    """Split text into fixed-size chunks with overlap."""
    
    def chunk(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50,
        **kwargs
    ) -> List[Tuple[str, int]]:
        """Split text into fixed-size overlapping chunks."""
        chunks = []
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + chunk_size
            
            # Try to break at word boundary
            if end < text_len:
                # Look for word boundary near chunk_size
                chunk = text[start:end]
                last_space = chunk.rfind(' ')
                if last_space > chunk_size // 2:
                    chunk = chunk[:last_space]
                    end = start + last_space
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append((chunk, start))
            
            # Move start with overlap
            start = end - overlap
            if start <= chunks[-1][1] if chunks else start:
                start = (chunks[-1][1] + len(chunks[-1][0])) if chunks else start
                break
        
        return chunks


class SemanticChunker(BaseChunker):
    """Split text by semantic units (sentences)."""
    
    def chunk(
        self,
        text: str,
        max_chunk_size: int = 500,
        overlap: int = 50,
        **kwargs
    ) -> List[Tuple[str, int]]:
        """Split text by semantic units (sentences/paragraphs)."""
        # First split by paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_chunk = ""
        current_start = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If adding this paragraph exceeds max size, save current and start new
            if current_chunk and len(current_chunk) + len(para) > max_chunk_size:
                if current_chunk:
                    chunks.append((current_chunk.strip(), current_start))
                # Start new chunk with overlap
                if chunks and overlap > 0:
                    # Find overlap text
                    prev_chunk = chunks[-1][0]
                    words = prev_chunk.split()
                    overlap_words = []
                    word_count = 0
                    for w in reversed(words):
                        overlap_words.insert(0, w)
                        word_count += len(w) + 1
                        if word_count > overlap:
                            break
                    current_chunk = " ".join(overlap_words) + " " + para
                    current_start = text.find(para, chunks[-1][1])
                else:
                    current_chunk = para
                    current_start = text.find(para)
            else:
                if not current_chunk:
                    current_start = text.find(para)
                current_chunk = (current_chunk + "\n\n" + para).strip()
        
        # Add final chunk
        if current_chunk:
            chunks.append((current_chunk, current_start))
        
        return chunks


def get_chunker(strategy: str) -> BaseChunker:
    """Get chunker by strategy name."""
    chunkers = {
        "paragraph": ParagraphChunker(),
        "fixed": FixedSizeChunker(),
        "semantic": SemanticChunker(),
    }
    chunker = chunkers.get(strategy)
    if chunker is None:
        logger.warning(f"Unknown chunking strategy: {strategy}, using paragraph")
        return ParagraphChunker()
    return chunker


def chunk_text(
    text: str,
    strategy: str = "paragraph",
    chunk_size: int = 500,
    overlap: int = 50
) -> List[dict]:
    """Chunk text and return list of chunk dicts."""
    chunker = get_chunker(strategy)
    
    chunks = chunker.chunk(
        text,
        chunk_size=chunk_size,
        overlap=overlap
    )
    
    return [
        {
            "content": chunk_text,
            "start_index": start_idx,
            "chunk_index": idx,
            "char_count": len(chunk_text)
        }
        for idx, (chunk_text, start_idx) in enumerate(chunks)
    ]
