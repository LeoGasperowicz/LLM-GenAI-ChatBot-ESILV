from fastapi import APIRouter, Depends
from ..models.schemas import ChatMessage, ChatResponse, Conversation, ConversationTurn
from ..agents.orchestrator_agent import orchestrator
from datetime import datetime
from typing import Dict, List

router = APIRouter(prefix="/chat", tags=["chat"])

# Stockage en mémoire des conversations (à remplacer par DB si besoin)
CONVERSATIONS: Dict[str, Conversation] = {}


def get_or_create_conversation(user_id: str | None) -> Conversation:
    conv_id = user_id or "anonymous"
    if conv_id not in CONVERSATIONS:
        CONVERSATIONS[conv_id] = Conversation(
            id=conv_id,
            user_id=user_id,
            turns=[]
        )
    return CONVERSATIONS[conv_id]


@router.post("/", response_model=ChatResponse)
async def chat(message: ChatMessage) -> ChatResponse:
    """
    Endpoint principal de chat.
    Le frontend Streamlit enverra les messages ici.
    """
    conversation = get_or_create_conversation(message.user_id or "anonymous")

    # Ajouter le message utilisateur à la conversation
    conversation.turns.append(
        ConversationTurn(
            timestamp=datetime.utcnow(),
            user_id=message.user_id,
            role="user",
            content=message.message,
        )
    )

    # Passer par l'orchestrateur
    response = await orchestrator.route(message)

    # Ajouter la réponse de l'assistant à la conversation
    conversation.turns.append(
        ConversationTurn(
            timestamp=datetime.utcnow(),
            user_id=message.user_id,
            role="assistant",
            content=response.reply,
            agent=response.agent,
            intent=response.intent,
        )
    )

    return response


@router.get("/conversation/{user_id}", response_model=Conversation)
async def get_conversation(user_id: str):
    """
    Récupérer l'historique de conversation pour un user_id donné.
    Utile pour l'interface admin ou pour un affichage persistant côté frontend.
    """
    return get_or_create_conversation(user_id)