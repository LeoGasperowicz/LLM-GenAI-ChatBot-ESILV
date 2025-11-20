# backend/agents/orchestrator_agent.py

from ..models.schemas import ChatMessage, ChatResponse, Conversation
from ..core.llm_client import llm_client
from .rag_agent import rag_agent
from .contact_agent import contact_agent, has_active_form


class OrchestratorAgent:
    """
    Agent orchestrateur.
    - Décide si on est sur une question FAQ / info -> RAG
    - Ou sur une demande de contact / inscription -> ContactAgent (formulaire)
    """

    name = "orchestrator"

    async def _detect_intent(self, text: str) -> str:
        """
        Renvoie 'faq', 'contact' ou 'unknown'.

        Règles simples + fallback LLM.
        """
        lower = (text or "").lower()

        # 🔹 RÈGLES POUR CONTACT / FORMULAIRE
        contact_keywords = [
            "coordonné",       # coordonnées, coordonnees
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

        # 🔹 RÈGLES SIMPLES POUR FAQ
        faq_keywords = [
            "programme",
            "spécialisation",
            "specialisation",
            "majeure",
            "admission",
            "concours",
            "parcoursup",
            "frais de scolarité",
            "frais de scolarite",
            "tarif",
            "alternance",
            "stage",
            "cours",
            "matière",
            "matiere",
            "logement",
            "résidence",
            "residence",
        ]
        if any(k in lower for k in faq_keywords):
            return "faq"

        # 🔹 Fallback LLM pour les cas ambigus
        system_prompt = (
            "Tu es un classificateur d'intentions pour un chatbot de l'école d'ingénieurs ESILV.\n"
            "Tu dois décider si le message de l'utilisateur est :\n"
            "- 'contact' : il veut être recontacté, laisser ses coordonnées, prendre rendez-vous,\n"
            "             obtenir un suivi personnalisé, etc.\n"
            "- 'faq' : il pose une question d'information (programmes, cours, admissions,\n"
            "          vie étudiante, etc.).\n"
            "- 'unknown' : si ce n'est pas clair.\n\n"
            "IMPORTANT : Réponds UNIQUEMENT par : contact, faq, unknown."
        )

        raw = (await llm_client.generate(prompt=text, system_prompt=system_prompt)).lower()

        if "contact" in raw:
            return "contact"
        if "faq" in raw:
            return "faq"
        return "faq"

    async def handle(self, conversation: Conversation, message: ChatMessage) -> ChatResponse:
        """
        Choisit le bon agent, appelle cet agent et renvoie un ChatResponse.
        🔑 Si un formulaire est déjà en cours pour ce user, on continue avec ContactAgent.
        """

        # 0️⃣ SI FORMULAIRE DÉJÀ EN COURS -> ON CONTINUE LE FORMULAIRE
        if has_active_form(message.user_id):
            agent_response = await contact_agent.handle(message)
            meta = dict(agent_response.metadata or {})
            meta["orchestrator_intent"] = "contact"
            meta["orchestrator_agent"] = self.name

            return ChatResponse(
                reply=agent_response.reply,
                agent=agent_response.agent,
                intent=agent_response.intent,
                context_documents=agent_response.context_documents,
                metadata=meta,
            )

        # 1️⃣ PAS DE FORMULAIRE EN COURS -> ON DÉTECTE L'INTENT
        intent = await self._detect_intent(message.message)

        if intent == "contact":
            agent_response = await contact_agent.handle(message)
        else:
            agent_response = await rag_agent.handle(message)

        meta = dict(agent_response.metadata or {})
        meta["orchestrator_intent"] = intent
        meta["orchestrator_agent"] = self.name

        return ChatResponse(
            reply=agent_response.reply,
            agent=agent_response.agent,
            intent=agent_response.intent,
            context_documents=agent_response.context_documents,
            metadata=meta,
        )


orchestrator = OrchestratorAgent()
