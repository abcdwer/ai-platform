"""Embedding service for text vectorization."""
from typing import List, Optional
from app.services.model_dispatcher import get_model_dispatcher


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self):
        self.dispatcher = get_model_dispatcher()
    
    async def embed_text(
        self,
        text: str,
        model: str = "text-embedding-ada-002",
        provider: str = "openai"
    ) -> List[float]:
        """Generate embedding for a single text."""
        try:
            embedding = await self.dispatcher.embed(
                text=text,
                model=model,
                provider=provider
            )
            return embedding
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding: {e}")
    
    async def embed_batch(
        self,
        texts: List[str],
        model: str = "text-embedding-ada-002",
        provider: str = "openai"
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            try:
                embedding = await self.embed_text(text, model, provider)
                embeddings.append(embedding)
            except Exception as e:
                # Return zero vector for failed embeddings
                embedding_size = 1536  # Default for ada-002
                embeddings.append([0.0] * embedding_size)
        
        return embeddings
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have the same dimension")
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
