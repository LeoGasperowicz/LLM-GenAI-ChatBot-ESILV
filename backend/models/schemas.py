from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional, Any, Dict

from pydantic import BaseModel, EmailStr


class ChatMessage(BaseModel):
    user_id: Optional[str] = None
    message: str

class AdminStats(BaseModel):
    total_conversations: int
    total_messages: int
    top_intents: Dict[str, int]

class ChatResponse(BaseModel):
    reply: str

    # Quel agent a répondu ?
    agent: Literal["orchestrator", "rag_agent", "form_agent"]

    # Intention principale
    intent: Literal["faq", "contact", "unknown"] = "unknown"

    # Contexte utilisé pour répondre (RAG)
    # On stocke une liste de dicts : {source, page, snippet, is_pdf, url?}
    context_documents: Optional[List[Dict[str, Any]]] = None

    # Extra (pour debug, routing, etc.)
    metadata: Optional[Dict[str, Any]] = None


class ConversationTurn(BaseModel):
    timestamp: datetime
    user_id: Optional[str] = None
    role: Literal["user", "assistant"]
    content: str
    agent: Optional[str] = None
    intent: Optional[str] = None


class Conversation(BaseModel):
    id: str
    user_id: Optional[str] = None
    turns: List[ConversationTurn]


class Contact(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    message: Optional[str] = None
    created_at: datetime
