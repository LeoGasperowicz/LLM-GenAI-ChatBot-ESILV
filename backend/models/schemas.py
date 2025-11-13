from typing import Optional, Literal, List
from pydantic import BaseModel, Field
from datetime import datetime


class ChatMessage(BaseModel):
    user_id: Optional[str] = Field(
        default=None,
        description="Identifiant utilisateur (ou session) fourni par le frontend."
    )
    message: str = Field(..., description="Message utilisateur.")


class ChatResponse(BaseModel):
    reply: str
    agent: Literal["rag_agent", "form_agent", "orchestrator"]
    intent: Literal["faq", "contact", "unknown"]
    context_documents: list[str] = []
    metadata: dict = {}


class ContactInfo(BaseModel):
    user_id: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ConversationTurn(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    role: Literal["user", "assistant"]
    content: str
    agent: Optional[str] = None
    intent: Optional[str] = None


class Conversation(BaseModel):
    id: str
    user_id: Optional[str] = None
    turns: List[ConversationTurn]


class AdminStats(BaseModel):
    total_conversations: int
    total_messages: int
    top_intents: dict[str, int]
