"""
RAG admin routes — ingest documents, query knowledge base.
Superuser-only except for the query endpoint.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.models.user import User
from app.rag.retriever import ingest_documents, ingest_travel_knowledge
from app.rag.vector_store import vector_store
from app.utils.dependencies import get_current_active_user, get_superuser
from app.utils.schemas import IngestDocumentRequest, RAGQueryRequest
from app.config.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/rag", tags=["RAG Knowledge Base"])


@router.post("/ingest", status_code=201)
async def ingest_document(
    body: IngestDocumentRequest,
    _: User = Depends(get_superuser),
):
    """
    Ingest a single document into the RAG knowledge base.
    Superuser access required.
    """
    doc_id = body.doc_id or str(uuid.uuid4())
    await ingest_documents(
        texts=[body.content],
        metadatas=[{"destination": body.destination.lower(), "source": body.source}],
        ids=[doc_id],
    )
    return {"status": "ingested", "id": doc_id}


@router.post("/ingest/seed", status_code=200)
async def seed_knowledge_base(_: User = Depends(get_superuser)):
    """Re-seed the knowledge base with built-in travel knowledge."""
    await ingest_travel_knowledge()
    return {"status": "seeded"}


@router.post("/query")
async def query_knowledge_base(
    body: RAGQueryRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Query the RAG knowledge base for relevant travel information.
    Available to all authenticated users.
    """
    where = {"destination": body.destination.lower()} if body.destination else None
    results = await vector_store.query(
        query_text=body.query,
        top_k=body.top_k,
        where=where,
    )
    return {"results": results, "count": len(results)}


@router.get("/stats")
async def knowledge_base_stats(_: User = Depends(get_superuser)):
    """Get RAG knowledge base document count."""
    count = await vector_store.count()
    return {"document_count": count}
