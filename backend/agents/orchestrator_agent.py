# backend/agents/orchestrator_agent.py

from ..models.schemas import ChatMessage, ChatResponse, Conversation
from .rag_agent import rag_agent
from .contact_agent import contact_agent, has_active_form


class OrchestratorAgent:
    """
    Agent orchestrateur.
    """

    name = "orchestrator"

    async def _detect_intent(self, text: str) -> str:
        """
        Renvoie 'faq' ou 'contact' selon règles simples.
        """
        lower = (text or "").lower()

        # 🔹 RÈGLES POUR CONTACT / FORMULAIRE
        contact_keywords = [
            "coordonné",
            "laisser mes coord",
            "laisser mes coordonnées",
            "laisser mes coordonnees",
            "contacter",
            "recontacter",
            "être recontacté",
            "etre recontacte",
            "prendre rendez-vous",
            "prendre rendez vous",
            "rdv",
            "rendez-vous",
            "rendez vous",
            "contactez-moi",
            "contacte moi",
            "parler à un conseiller",
            "parler a un conseiller",
            "appeler",
            "rappel téléphonique",
            "rappel telephonique",
            "inscription",
            "m'inscrire",
            "m inscrire",
            "dossier de candidature",
            "formulaire",
        ]
        if any(k in lower for k in contact_keywords):
            return "contact"

        # 👉 TOUT LE RESTE = FAQ (RAG)
        return "faq"

    async def handle(self, conversation: Conversation, message: ChatMessage) -> ChatResponse:

        # 0️⃣ FORMULAIRE EN COURS → priorité au contact agent
        if has_active_form(message.user_id):
            agent_response = await contact_agent.handle(message)
        else:
            # 1️⃣ Détection d'intent
            intent = await self._detect_intent(message.message)

            if intent == "contact":
                agent_response = await contact_agent.handle(message)
            else:
                agent_response = await rag_agent.handle(message)

        # Construction de la réponse
        return ChatResponse(
            reply=agent_response.reply,
            agent=agent_response.agent,
            intent=agent_response.intent,
            context_documents=agent_response.context_documents,
            metadata={"source": "orchestrator"},
        )


orchestrator = OrchestratorAgent()

