from ..models.schemas import ChatMessage, ChatResponse
from .rag_agent import rag_agent
from .form_agent import form_agent


class OrchestratorAgent:
    name = "orchestrator"

    async def detect_intent(self, message: str) -> str:
        """
        Détection d'intent ultra simple basée sur des mots-clés.
        À remplacer par vraies règles / LLM plus tard.
        """
        text = message.lower()

        contact_keywords = ["contact", "rdv", "rendez-vous", "rendez vous",
                            "inscription", "m'inscrire", "m inscrire", "dossier",
                            "formulaire", "email", "mail", "téléphone"]
        faq_keywords = ["programme", "admission", "cursus", "cours", "spécialité",
                        "spécialisations", "diplôme", "alternance", "frais", "inscriptions"]

        if any(k in text for k in contact_keywords):
            return "contact"
        if any(k in text for k in faq_keywords):
            return "faq"
        return "unknown"

    async def route(self, message: ChatMessage) -> ChatResponse:
        """
        Route le message vers l'agent approprié.
        """
        intent = await self.detect_intent(message.message)

        if intent == "faq":
            res = await rag_agent.handle(message)
            res.intent = "faq"
            return res

        if intent == "contact":
            res = await form_agent.handle(message)
            res.intent = "contact"
            return res

        # Intent inconnu : par défaut, utilise le RAG
        res = await rag_agent.handle(message)
        res.intent = "unknown"
        res.metadata["note"] = "intent_unknown_used_rag"
        return res


orchestrator = OrchestratorAgent()
