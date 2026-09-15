"""
ChromaDB vector store client for RAG.

Supports two embedding modes:
  - LOCAL mode  (RAG_EMBEDDING_MODEL=local):
      ChromaDB uses its built-in sentence-transformers. 100% free, no API key.
  - REMOTE mode (RAG_EMBEDDING_MODEL=text-embedding-3-small etc):
      Uses OpenAI / LiteLLM embeddings API.

Client priority:
  1. Persistent local client (stores data in ./chroma_data/ folder) — default for dev
  2. HTTP client (if CHROMA_HOST != localhost or CHROMA_PORT reachable) — for Docker
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import chromadb

from app.config.settings import settings
from app.config.logging_config import get_logger
from app.rag.embedder import USE_LOCAL_EMBEDDINGS

logger = get_logger(__name__)

_chroma_client: Any = None   # chromadb.Client | AsyncHttpClient


async def _get_client():
    """Return (or create) the ChromaDB client."""
    global _chroma_client
    if _chroma_client is not None:
        return _chroma_client

    # Try HTTP client first (for Docker / remote Chroma)
    port_open = False
    try:
        import socket
        s = socket.create_connection((settings.CHROMA_HOST, settings.CHROMA_PORT), timeout=1)
        s.close()
        port_open = True
    except OSError:
        pass

    if port_open:
        try:
            client = await chromadb.AsyncHttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT,
            )
            await client.heartbeat()
            _chroma_client = client
            logger.info("chromadb_http_connected",
                        host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
            return _chroma_client
        except Exception as e:
            logger.warning("chromadb_http_failed", error=str(e))

    # Fallback: persistent local client (data stored on disk, survives restarts)
    chroma_dir = Path(__file__).parent.parent.parent / "chroma_data"
    chroma_dir.mkdir(exist_ok=True)
    _chroma_client = chromadb.PersistentClient(path=str(chroma_dir))
    logger.info("chromadb_persistent_local", path=str(chroma_dir))
    return _chroma_client


async def _get_collection():
    """Return (or create) the TripMate knowledge collection."""
    client = await _get_client()

    if USE_LOCAL_EMBEDDINGS:
        # Use ChromaDB's default embedding function (sentence-transformers, free, local)
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        ef = DefaultEmbeddingFunction()
        # PersistentClient uses sync API; AsyncHttpClient uses async
        if hasattr(client, 'get_or_create_collection'):
            try:
                collection = client.get_or_create_collection(
                    name=settings.CHROMA_COLLECTION_NAME,
                    metadata={"hnsw:space": "cosine"},
                    embedding_function=ef,
                )
            except TypeError:
                # async client
                collection = await client.get_or_create_collection(
                    name=settings.CHROMA_COLLECTION_NAME,
                    metadata={"hnsw:space": "cosine"},
                    embedding_function=ef,
                )
        return collection
    else:
        if hasattr(client, 'get_or_create_collection'):
            try:
                collection = client.get_or_create_collection(
                    name=settings.CHROMA_COLLECTION_NAME,
                    metadata={"hnsw:space": "cosine"},
                )
            except TypeError:
                collection = await client.get_or_create_collection(
                    name=settings.CHROMA_COLLECTION_NAME,
                    metadata={"hnsw:space": "cosine"},
                )
        return collection


def _is_async_client(client) -> bool:
    return hasattr(client, '__class__') and 'Async' in client.__class__.__name__


class VectorStore:
    """Wrapper around ChromaDB. Handles both sync (PersistentClient) and async (HttpClient)."""

    async def _call(self, collection, method: str, **kwargs):
        """Call a collection method — handles both sync and async collections."""
        fn = getattr(collection, method)
        import asyncio
        if asyncio.iscoroutinefunction(fn):
            return await fn(**kwargs)
        else:
            # Run sync method in executor to avoid blocking event loop
            loop = asyncio.get_event_loop()
            import functools
            return await loop.run_in_executor(None, functools.partial(fn, **kwargs))

    async def add_documents(
        self,
        documents: list[str],
        metadatas: list[dict[str, Any]],
        ids: list[str],
    ) -> None:
        """Embed and store documents in ChromaDB."""
        try:
            collection = await _get_collection()
            await self._call(
                collection, "add",
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )
            logger.info("rag_documents_added", count=len(documents))
        except Exception as e:
            logger.error("rag_add_error", error=str(e))

    async def query(
        self,
        query_text: str,
        top_k: int | None = None,
        where: Optional[dict] = None,
    ) -> list[dict[str, Any]]:
        """Semantic search — returns top_k most relevant documents."""
        k = top_k or settings.RAG_TOP_K
        try:
            collection = await _get_collection()

            query_kwargs: dict[str, Any] = {
                "query_texts": [query_text],
                "n_results": k,
                "include": ["documents", "metadatas", "distances"],
            }
            if where:
                query_kwargs["where"] = where

            results = await self._call(collection, "query", **query_kwargs)

            docs  = results.get("documents",  [[]])[0]
            metas = results.get("metadatas",  [[]])[0]
            dists = results.get("distances",  [[]])[0]

            return [
                {
                    "content": doc,
                    "metadata": meta,
                    "relevance_score": round(1 - dist, 4),
                }
                for doc, meta, dist in zip(docs, metas, dists)
            ]
        except Exception as e:
            logger.error("rag_query_error", error=str(e))
            return []

    async def delete_by_ids(self, ids: list[str]) -> None:
        try:
            collection = await _get_collection()
            await self._call(collection, "delete", ids=ids)
        except Exception as e:
            logger.error("rag_delete_error", error=str(e))

    async def count(self) -> int:
        try:
            collection = await _get_collection()
            result = await self._call(collection, "count")
            return result if isinstance(result, int) else 0
        except Exception:
            return 0


# Singleton
vector_store = VectorStore()
