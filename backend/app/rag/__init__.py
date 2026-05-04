"""RAG engine package."""
from app.rag.chroma_client import ChromaClient, get_chroma_client, init_chroma_collection
from app.rag.parser import (
    parse_document,
    get_parser,
    TextParser,
    MarkdownParser,
    PDFParser,
    DocxParser,
    CSVParser,
    HTMLParser,
    URLParser,
)
from app.rag.chunker import chunk_text, get_chunker, BaseChunker
from app.rag.retriever import Retriever

__all__ = [
    "ChromaClient",
    "get_chroma_client",
    "init_chroma_collection",
    "parse_document",
    "get_parser",
    "TextParser",
    "MarkdownParser",
    "PDFParser",
    "DocxParser",
    "CSVParser",
    "HTMLParser",
    "URLParser",
    "chunk_text",
    "get_chunker",
    "BaseChunker",
    "Retriever",
]
