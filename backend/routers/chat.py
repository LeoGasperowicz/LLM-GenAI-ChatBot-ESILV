from datetime import datetime
from typing import Dict

from fastapi import APIRouter

from ..models.schemas import ChatMessage, ChatResponse, Conversation, ConversationTurn
from ..core.llm_client import llm_client  # 🔗 on importe le client LLM

router = APIRouter(prefix="/chat", tags=["chat"])

# Stockage en mémoire des conversations (à remplacer par DB si besoin)
CONVERSATIONS: Dict[str, Conversation] = {}


def get_or_create_conversation(user_id: str | None) -> Conversation:
    conv_id = user_id or "anonymous"
    if conv_id not in CONVERSATIONS:
        CONVERSATIONS[conv_id] = Conversation(
            id=conv_id,
            user_id=user_id,
            turns=[],
        )
    return CONVERSATIONS[conv_id]


@router.post("/", response_model=ChatResponse)
async def chat(message: ChatMessage) -> ChatResponse:
    """
    Endpoint principal de chat.
    Le frontend Streamlit enverra les messages ici.
    """
    conversation = get_or_create_conversation(message.user_id or "anonymous")

    # 1) Ajouter le message utilisateur à la conversation
    conversation.turns.append(
        ConversationTurn(
            timestamp=datetime.utcnow(),
            user_id=message.user_id,
            role="user",
            content=message.message,
        )
    )

    # 2) Appeler le LLM **avec RAG**
    #    generate_with_rag retourne un dict :
    #    { "answer": str, "sources": [ ... ] }
    result = await llm_client.generate_with_rag(message.message)

    reply_text = result.get("answer", "(Pas de réponse)")
    context_docs = result.get("sources", [])

    # Tu peux mettre ce que tu veux ici comme "agent" et "intent"
    agent_name = "rag_esilv"
    intent_name = "information_esilv"

    # 3) Ajouter la réponse de l'assistant à la conversation
    conversation.turns.append(
        ConversationTurn(
            timestamp=datetime.utcnow(),
            user_id=message.user_id,
            role="assistant",
            content=reply_text,
            agent=agent_name,
            intent=intent_name,
        )
    )

    # 4) Construire la réponse pour le frontend
    response = ChatResponse(
        reply=reply_text,
        agent=agent_name,
        intent=intent_name,
        metadata={
            "provider": llm_client.provider,
            "model": llm_client.model,
        },
        context_documents=context_docs,  # utilisé par le front pour afficher les sources
    )

    return response


@router.get("/conversation/{user_id}", response_model=Conversation)
async def get_conversation(user_id: str):
    """
    Récupérer l'historique de conversation pour un user_id donné.
    Utile pour l'interface admin ou pour un affichage persistant côté frontend.
    """
    return get_or_create_conversation(user_id)
