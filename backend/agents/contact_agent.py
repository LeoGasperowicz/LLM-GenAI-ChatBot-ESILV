# backend/agents/contact_agent.py

import re
from typing import Dict, Optional, Any

from ..models.schemas import ChatMessage, ChatResponse

# État en mémoire des formulaires de contact en cours
# Clé = user_id (ou "anonymous"), valeur = dict (état du formulaire)
_FORM_STATES: Dict[str, Dict[str, Any]] = {}


def _user_key(user_id: Optional[str]) -> str:
    return user_id or "anonymous"


def has_active_form(user_id: Optional[str]) -> bool:
    """
    Indique si ce user est en plein remplissage de formulaire.
    Utilisé par l'orchestrateur pour forcer la route vers ContactAgent.
    """
    return _user_key(user_id) in _FORM_STATES


def _extract_email(text: str) -> Optional[str]:
    m = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    return m.group(0) if m else None


def _extract_phone(text: str) -> Optional[str]:
    m = re.search(r"(\+?\d[\d \-]{7,}\d)", text)
    return m.group(0) if m else None


def _extract_name(text: str, email: Optional[str], phone: Optional[str]) -> Optional[str]:
    # On enlève email et téléphone du texte pour deviner le nom
    clean = text
    if email:
        clean = clean.replace(email, "")
    if phone:
        clean = clean.replace(phone, "")
    clean = clean.replace(",", " ").strip()
    clean = re.sub(r"\s+", " ", clean)

    if not clean:
        return None

    # Heuristique simple : on garde max 5 mots
    parts = clean.split(" ")
    if len(parts) > 5:
        parts = parts[:5]
    name = " ".join(p for p in parts if p)
    return name or None


class ContactAgent:
    """
    Agent responsable de la collecte des coordonnées (formulaire contact).
    Fonctionne en 2 temps :
      1) On demande tout dans un message
      2) L'utilisateur envoie nom + email (+ téléphone)
    """

    name = "form_agent"

    async def handle(self, message: ChatMessage) -> ChatResponse:
        user_key = _user_key(message.user_id)
        user_text = (message.message or "").strip()

        state = _FORM_STATES.get(user_key)

        # 1️⃣ PAS D'ÉTAT ENCORE -> ON DÉMARRE LE FORMULAIRE
        if state is None:
            _FORM_STATES[user_key] = {"step": "awaiting_details"}

            reply = (
                "Merci pour votre intérêt pour l'ESILV 👏\n\n"
                "Pour que nous puissions vous recontacter, pouvez-vous me donner **dans un seul message** :\n"
                "- votre **nom complet**,\n"
                "- votre **adresse e-mail**, \n"
                "- votre **numéro de téléphone** (optionnel).\n\n"
                "Exemple :\n"
                "_Jean Dupont, jean.dupont@mail.com, 06 12 34 56 78_"
            )

            return ChatResponse(
                reply=reply,
                agent=self.name,
                intent="contact",
                context_documents=[],
                metadata={"form_step": "awaiting_details"},
            )

        # 2️⃣ ON ATTEND LES DÉTAILS -> ON ESSAIE D'EXTRAIRE NOM / EMAIL / TÉL
        if state.get("step") == "awaiting_details":
            email = _extract_email(user_text)
            phone = _extract_phone(user_text)
            name = _extract_name(user_text, email, phone)

            if not email or not name:
                # Infos insuffisantes -> on redemande proprement
                reply = (
                    "Merci pour ces informations 🙏\n"
                    "Je n'ai pas réussi à trouver **clairement** votre nom et votre e-mail dans ce message.\n\n"
                    "Pouvez-vous les renvoyer dans un format du type :\n"
                    "_Prénom Nom, email@domaine.com, 06 12 34 56 78_ ?"
                )
                return ChatResponse(
                    reply=reply,
                    agent=self.name,
                    intent="contact",
                    context_documents=[],
                    metadata={
                        "form_step": "awaiting_details",
                        "warning": "missing_name_or_email",
                    },
                )

            # ✅ On a suffisamment d'infos -> on "sauvegarde" et on clôt le formulaire
            contact_data = {
                "full_name": name,
                "email": email,
                "phone": phone,
                "raw_message": user_text,
            }

            # Si tu veux, tu peux à terme stocker ça dans une vraie DB ici

            # On efface l'état du formulaire
            _FORM_STATES.pop(user_key, None)

            reply = (
                f"Merci **{name}** ! 🙌\n\n"
                "J'ai bien enregistré vos coordonnées :\n"
                f"- Email : **{email}**\n"
                f"- Téléphone : **{phone or 'non renseigné'}**\n\n"
                "Un membre de l'équipe ESILV pourra vous recontacter à partir de ces informations."
            )

            return ChatResponse(
                reply=reply,
                agent=self.name,
                intent="contact",
                context_documents=[],
                metadata={
                    "form_step": "completed",
                    "saved_contact": contact_data,
                },
            )

        # 3️⃣ Cas de sécurité : on reset
        _FORM_STATES.pop(user_key, None)
        return ChatResponse(
            reply=(
                "Je vais vous aider à laisser vos coordonnées 😊\n"
                "Pouvez-vous me donner votre nom complet, votre e-mail et éventuellement votre téléphone "
                "dans un seul message ?"
            ),
            agent=self.name,
            intent="contact",
            context_documents=[],
            metadata={"form_step": "reset"},
        )


contact_agent = ContactAgent()
