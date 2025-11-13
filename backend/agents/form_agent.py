from ..models.schemas import ChatMessage, ChatResponse, ContactInfo
from ..services.contact_service import contact_service


class FormAgent:
    name = "form_agent"

    async def handle(self, message: ChatMessage) -> ChatResponse:
        """
        Version simple : détecte des infos basiques dans le texte (à améliorer avec un LLM ou un form-flow).
        Ici, on simule seulement.
        """
        # TODO : demander étape par étape (nom, email, téléphone) côté frontend ou via un flux multi-tours.

        fake_contact = ContactInfo(
            user_id=message.user_id,
            full_name="Nom Prénom (exemple)",
            email="exemple@esilv.fr",
            message=message.message,
        )
        contact_service.add_contact(fake_contact)

        reply = (
            "Merci pour vos informations. Un membre de l'équipe ESILV pourra "
            "vous recontacter. (NB : ici c'est un stockage simulé, à adapter)"
        )

        return ChatResponse(
            reply=reply,
            agent=self.name,
            intent="contact",
            context_documents=[],
            metadata={"contact_stored": True}
        )


form_agent = FormAgent()
