"""ChromaDB client wrapper for vector storage."""
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings
from loguru import logger


class ChromaClient:
    """ChromaDB client wrapper."""
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        collection_name: str = "knowledge_base"
    ):
        """Initialize ChromaDB client."""
        from app.core.config import settings
        self.host = host or settings.CHROMADB_HOST
        self.port = port or settings.CHROMADB_PORT
        self.client = chromadb.HttpClient(
            host=self.host,
            port=self.port,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        logger.info(f"ChromaDB client initialized: {self.host}:{self.port}")
    
    def get_or_create_collection(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Get or create a collection."""
        try:
            collection = self.client.get_or_create_collection(
                name=name,
                metadata=metadata or {}
            )
            logger.info(f"Collection '{name}' ready")
            return collection
        except Exception as e:
            logger.error(f"Failed to get/create collection: {e}")
            raise
    
    def delete_collection(self, name: str):
        """Delete a collection."""
        try:
            self.client.delete_collection(name)
            logger.info(f"Collection '{name}' deleted")
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            raise
    
    def add_vectors(
        self,
        collection_name: str,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ):
        """Add vectors to a collection."""
        collection = self.client.get_collection(collection_name)
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Added {len(ids)} vectors to collection '{collection_name}'")
    
    def query(
        self,
        collection_name: str,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query a collection."""
        collection = self.client.get_collection(collection_name)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            where_document=where_document
        )
        return results
    
    def delete_vectors(
        self,
        collection_name: str,
        ids: List[str]
    ):
        """Delete vectors from a collection."""
        collection = self.client.get_collection(collection_name)
        collection.delete(ids=ids)
        logger.info(f"Deleted {len(ids)} vectors from collection '{collection_name}'")
    
    def count(self, collection_name: str) -> int:
        """Count vectors in a collection."""
        collection = self.client.get_collection(collection_name)
        return collection.count()
    
    def reset(self):
        """Reset the database (dangerous!)."""
        self.client.reset()
        logger.warning("ChromaDB database reset")


# Global ChromaDB client instance
_chroma_client: Optional[ChromaClient] = None


def get_chroma_client(
    host: str = "localhost",
    port: int = 8001
) -> ChromaClient:
    """Get or create ChromaDB client instance."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = ChromaClient(host=host, port=port)
    return _chroma_client


def init_chroma_collection(
    knowledge_base_id: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Any:
    """Initialize a collection for a knowledge base."""
    client = get_chroma_client()
    collection_name = f"kb_{knowledge_base_id}"
    return client.get_or_create_collection(
        name=collection_name,
        metadata=metadata or {"knowledge_base_id": knowledge_base_id}
    )
