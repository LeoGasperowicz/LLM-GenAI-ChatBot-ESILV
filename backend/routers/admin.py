# backend/routers/admin.py

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from fastapi import APIRouter

from ..models.schemas import AdminStats
from .chat import CONVERSATIONS  # on réutilise les conversations en mémoire

router = APIRouter(prefix="/admin", tags=["admin"])

# Fichier JSON où ContactAgent enregistre les contacts
CONTACTS_FILE = Path(__file__).resolve().parent.parent / "data" / "contacts.json"


# ============================
#  /admin/stats
# ============================

@router.get("/stats", response_model=AdminStats)
def get_stats() -> AdminStats:
    """
    Statistiques globales simples :
    - nombre de conversations
    - nombre total de messages
    - répartition des intents (faq / contact / unknown)
    """
    total_conversations = len(CONVERSATIONS)
    total_messages = 0
    intents_counter: Counter[str] = Counter()

    for conv in CONVERSATIONS.values():
        total_messages += len(conv.turns)
        for turn in conv.turns:
            if getattr(turn, "intent", None):
                intents_counter[turn.intent] += 1

    top_intents: Dict[str, int] = dict(intents_counter)

    return AdminStats(
        total_conversations=total_conversations,
        total_messages=total_messages,
        top_intents=top_intents,
    )


# ============================
#  /admin/contacts
# ============================

@router.get("/contacts")
def get_contacts() -> List[Dict[str, Any]]:
    """
    Retourne la liste des personnes à recontacter.

    Les données sont lues dans backend/data/contacts.json,
    fichier alimenté par ContactAgent.save_contact().
    """
    CONTACTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not CONTACTS_FILE.exists():
        # Pas encore de contacts
        return []

    try:
        raw = CONTACTS_FILE.read_text(encoding="utf-8")
        data = json.loads(raw)

        # On s'assure que c'est bien une liste de dicts
        if isinstance(data, list):
            return data
        else:
            return []
    except Exception:
        # En cas de JSON cassé, on renvoie liste vide
        return []
