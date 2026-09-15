"""
RAG Retriever — queries the vector store and injects context into TravelState.
Also handles document ingestion and the knowledge base seeding.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from app.config.settings import settings
from app.config.logging_config import get_logger
from app.rag.vector_store import vector_store

if TYPE_CHECKING:
    from app.agents.state import TravelState

logger = get_logger(__name__)


async def inject_rag_context(state: "TravelState") -> "TravelState":
    """
    Query the vector store for destination-specific knowledge and inject
    it into the TravelState before the itinerary agent runs.
    """
    tc = state.trip_constraints
    destination = tc.destination or ""
    interests = tc.interests or []

    if not destination:
        return state

    query = (
        f"Travel tips, attractions, culture, food, and transport in {destination}. "
        f"Interests: {', '.join(interests) if interests else 'general tourism'}"
    )

    try:
        results = await vector_store.query(
            query_text=query,
            top_k=settings.RAG_TOP_K,
            where={"destination": destination.lower()} if destination else None,
        )

        if results:
            context_parts = []
            for i, r in enumerate(results, 1):
                meta = r.get("metadata", {})
                source = meta.get("source", "Knowledge Base")
                content = r.get("content", "")
                score = r.get("relevance_score", 0)
                context_parts.append(
                    f"[{i}] (relevance: {score:.2f}, source: {source})\n{content}"
                )

            state.rag_context = "\n\n".join(context_parts)
            logger.info(
                "rag_context_injected",
                destination=destination,
                chunks=len(results),
            )
        else:
            logger.info("rag_no_results", destination=destination)

    except Exception as e:
        logger.error("rag_retrieval_error", destination=destination, error=str(e))
        # RAG failure is non-fatal — itinerary proceeds without it

    return state


async def ingest_documents(
    texts: list[str],
    metadatas: list[dict],
    ids: list[str],
) -> None:
    """Ingest a batch of documents into the vector store."""
    await vector_store.add_documents(
        documents=texts,
        metadatas=metadatas,
        ids=ids,
    )


async def ingest_travel_knowledge() -> None:
    """
    Seed the knowledge base with built-in travel knowledge.
    Call once at startup or via admin endpoint.
    """
    knowledge = [
        {
            "id": "dubai_001",
            "destination": "dubai",
            "content": (
                "Dubai is best visited October–April. Must-see: Burj Khalifa (book tickets in advance), "
                "Dubai Mall, Gold Souk, Deira Old Town, Dubai Frame, Desert Safari. "
                "Best food areas: Deira, JBR Walk, Downtown Dubai. Metro covers most tourist spots. "
                "Tap water is safe. Dress modestly in malls and heritage areas."
            ),
            "source": "TripMate Knowledge Base",
        },
        {
            "id": "dubai_002",
            "destination": "dubai",
            "content": (
                "Dubai transport: Metro Red and Green lines connect airport to city. "
                "NOL card works on metro, bus, and water taxis. "
                "Careem and Uber are reliable and affordable. Taxis are metered and safe. "
                "Water taxis (Abra) cross Dubai Creek for AED 1."
            ),
            "source": "TripMate Knowledge Base",
        },
        {
            "id": "tokyo_001",
            "destination": "tokyo",
            "content": (
                "Tokyo highlights: Shinjuku, Shibuya Crossing, Asakusa Temple, Akihabara, "
                "Harajuku, Odaiba, teamLab Borderless. Day trips: Nikko, Kamakura, Mt Fuji (Hakone). "
                "IC card (Suica/Pasmo) works on all rail and subway. 7-Eleven and Lawson meals are excellent. "
                "Tipping is not customary in Japan."
            ),
            "source": "TripMate Knowledge Base",
        },
        {
            "id": "london_001",
            "destination": "london",
            "content": (
                "London essentials: Oyster card for tube. Free museums: British Museum, V&A, Natural History, Tate Modern. "
                "Best neighbourhoods: Shoreditch, Notting Hill, Covent Garden, South Bank. "
                "Afternoon tea at Fortnum & Mason. Borough Market for food. "
                "Avoid Oxford Street for shopping — try Carnaby Street instead."
            ),
            "source": "TripMate Knowledge Base",
        },
        {
            "id": "paris_001",
            "destination": "paris",
            "content": (
                "Paris must-do: Eiffel Tower (book online), Louvre (book in advance), Musée d'Orsay, Montmartre, "
                "Seine river cruise, Sainte-Chapelle. Best food: Marais neighbourhood, Le Comptoir du Relais, "
                "boulangeries for croissants. Metro is excellent and affordable. "
                "Paris Museum Pass saves money. Many shops closed Sunday."
            ),
            "source": "TripMate Knowledge Base",
        },
        {
            "id": "bangkok_001",
            "destination": "bangkok",
            "content": (
                "Bangkok attractions: Grand Palace & Wat Pho (cover up), Chatuchak Weekend Market, "
                "Khao San Road, Wat Arun, Floating Markets. "
                "BTS Skytrain and MRT cover tourist areas. Grab app for taxis. "
                "Street food is safe and excellent — Pad Thai, Som Tum, Mango sticky rice. "
                "Best time: Nov–Feb. Avoid Songkran if you dislike water fights."
            ),
            "source": "TripMate Knowledge Base",
        },
        {
            "id": "bali_001",
            "destination": "bali",
            "content": (
                "Bali highlights: Ubud (rice terraces, Monkey Forest, arts), Seminyak (beach, nightlife), "
                "Canggu (surf, cafes), Uluwatu Temple, Mount Batur sunrise hike. "
                "Rent a scooter or hire a driver for the day (~$40). "
                "Warung food is cheap and excellent. Avoid tap water. "
                "Best time: April–October (dry season)."
            ),
            "source": "TripMate Knowledge Base",
        },
    ]

    existing_count = await vector_store.count()
    if existing_count >= len(knowledge):
        logger.info("rag_knowledge_already_seeded", count=existing_count)
        return

    texts = [k["content"] for k in knowledge]
    ids = [k["id"] for k in knowledge]
    metadatas = [
        {"destination": k["destination"], "source": k["source"]} for k in knowledge
    ]

    await vector_store.add_documents(texts, metadatas, ids)
    logger.info("rag_knowledge_seeded", count=len(knowledge))
