"""
Embedding service with two modes:

  Mode A (RAG_EMBEDDING_MODEL=local):
      Uses ChromaDB's built-in sentence-transformers model.
      100% free, runs locally, no API key needed.
      Embeddings are created inside ChromaDB automatically.

  Mode B (RAG_EMBEDDING_MODEL=text-embedding-3-small or any OpenAI model):
      Uses LiteLLM / OpenAI embeddings API.
      Costs ~$0.0001 per full trip plan. Very cheap.

The vector_store.py and retriever.py detect the mode and behave accordingly.
"""
from typing import Union

from app.config.settings import settings
from app.config.logging_config import get_logger

logger = get_logger(__name__)

# Detect whether we are in local (free) mode
USE_LOCAL_EMBEDDINGS = settings.RAG_EMBEDDING_MODEL.lower() in (
    "local", "local-embeddings", "chromadb-local"
)


async def get_embedding(text: str) -> list[float] | None:
    """
    Get embedding vector for a single text string.
    Returns None when using local mode (ChromaDB embeds internally).
    """
    if USE_LOCAL_EMBEDDINGS:
        return None  # ChromaDB will embed automatically

    import litellm
    try:
        response = await litellm.aembedding(
            model=settings.RAG_EMBEDDING_MODEL,
            input=[text],
        )
        return response.data[0]["embedding"]
    except Exception as e:
        logger.error("embedding_error", model=settings.RAG_EMBEDDING_MODEL, error=str(e))
        logger.warning("falling_back_to_local_embeddings")
        return None  # fall back to ChromaDB local embeddings


async def get_embeddings(texts: list[str]) -> list[list[float]] | None:
    """
    Get embedding vectors for a list of texts.
    Returns None when using local mode (ChromaDB embeds internally).
    """
    if USE_LOCAL_EMBEDDINGS:
        return None  # ChromaDB will embed automatically

    import litellm
    try:
        response = await litellm.aembedding(
            model=settings.RAG_EMBEDDING_MODEL,
            input=texts,
        )
        return [item["embedding"] for item in response.data]
    except Exception as e:
        logger.error("batch_embedding_error", error=str(e), count=len(texts))
        logger.warning("falling_back_to_local_embeddings")
        return None  # fall back to ChromaDB local embeddings
