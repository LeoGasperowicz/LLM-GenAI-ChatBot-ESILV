from fastapi import APIRouter
from typing import Dict
from ..models.schemas import AdminStats
from .chat import CONVERSATIONS
from ..services.contact_service import contact_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStats)
async def get_stats():
    """
    Retourne quelques stats simples pour l'interface admin.
    """
    total_conversations = len(CONVERSATIONS)
    total_messages = sum(len(conv.turns) for conv in CONVERSATIONS.values())

    intent_counts: Dict[str, int] = {}
    for conv in CONVERSATIONS.values():
        for turn in conv.turns:
            if turn.role == "assistant" and turn.intent:
                intent_counts[turn.intent] = intent_counts.get(turn.intent, 0) + 1

    return AdminStats(
        total_conversations=total_conversations,
        total_messages=total_messages,
        top_intents=intent_counts,
    )


@router.get("/contacts")
async def list_contacts():
    """
    Liste des contacts collectés (simulé, pas de DB).
    """
    return contact_service.list_contacts()