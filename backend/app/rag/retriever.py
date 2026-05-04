"""Document retriever for knowledge base search."""
from typing import List, Dict, Any, Optional
from loguru import logger

from app.rag.chroma_client import get_chroma_client, init_chroma_collection


class Retriever:
    """Document retriever using ChromaDB."""
    
    def __init__(
        self,
        knowledge_base_id: str,
        embedding_service: Any = None
    ):
        """Initialize retriever."""
        self.knowledge_base_id = knowledge_base_id
        self.collection_name = f"kb_{knowledge_base_id}"
        self.chroma = get_chroma_client()
        self.embedding_service = embedding_service
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Ensure collection exists."""
        try:
            self.chroma.get_or_create_collection(
                name=self.collection_name,
                metadata={"knowledge_base_id": self.knowledge_base_id}
            )
        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents for query."""
        try:
            # Generate query embedding
            if self.embedding_service is None:
                raise ValueError("Embedding service not configured")
            
            query_embedding = self.embedding_service.embed([query])[0]
            
            # Query ChromaDB
            results = self.chroma.query(
                collection_name=self.collection_name,
                query_embedding=query_embedding,
                n_results=top_k * 2,  # Get more to filter by threshold
                where=filters
            )
            
            # Process and filter results
            retrieved = []
            if results and results.get("documents"):
                ids = results.get("ids", [[]])[0]
                documents = results.get("documents", [[]])[0]
                distances = results.get("distances", [[]])[0]
                metadatas = results.get("metadatas", [[{}]])[0]
                
                for i, doc in enumerate(documents):
                    # Convert distance to similarity (ChromaDB uses L2 distance)
                    distance = distances[i] if i < len(distances) else 1.0
                    similarity = 1.0 / (1.0 + distance)
                    
                    if similarity >= similarity_threshold:
                        retrieved.append({
                            "content": doc,
                            "document_id": metadatas[i].get("document_id") if i < len(metadatas) else None,
                            "document_title": metadatas[i].get("document_title", "Unknown") if i < len(metadatas) else "Unknown",
                            "chunk_index": metadatas[i].get("chunk_index", 0) if i < len(metadatas) else 0,
                            "score": similarity,
                            "metadata": metadatas[i] if i < len(metadatas) else {}
                        })
                        
                        if len(retrieved) >= top_k:
                            break
            
            logger.info(f"Retrieved {len(retrieved)} documents for query")
            return retrieved
            
        except Exception as e:
            logger.error(f"Failed to retrieve documents: {e}")
            return []
    
    def add_documents(
        self,
        document_id: str,
        document_title: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ):
        """Add document chunks to the collection."""
        try:
            ids = [f"{document_id}_chunk_{c['chunk_index']}" for c in chunks]
            documents = [c["content"] for c in chunks]
            metadatas = [
                {
                    "document_id": document_id,
                    "document_title": document_title,
                    "chunk_index": c["chunk_index"],
                    "char_count": c["char_count"]
                }
                for c in chunks
            ]
            
            self.chroma.add_vectors(
                collection_name=self.collection_name,
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(chunks)} chunks for document {document_id}")
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    def delete_document(self, document_id: str):
        """Delete all chunks for a document."""
        try:
            # Query to get chunk IDs
            collection = self.chroma.client.get_collection(self.collection_name)
            
            # Get all items with this document_id
            results = collection.get(
                where={"document_id": document_id}
            )
            
            if results and results.get("ids"):
                self.chroma.delete_vectors(
                    collection_name=self.collection_name,
                    ids=results["ids"]
                )
                logger.info(f"Deleted chunks for document {document_id}")
                
        except Exception as e:
            logger.error(f"Failed to delete document chunks: {e}")
            raise
    
    def get_vector_count(self) -> int:
        """Get total number of vectors in collection."""
        try:
            return self.chroma.count(self.collection_name)
        except Exception as e:
            logger.error(f"Failed to count vectors: {e}")
            return 0
