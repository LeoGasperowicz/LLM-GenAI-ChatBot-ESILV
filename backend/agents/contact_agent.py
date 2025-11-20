# backend/agents/contact_agent.py

import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

from ..models.schemas import ChatMessage, ChatResponse
from ..core.llm_client import llm_client  # ✅ LLM utilisé pour formuler les messages


# ================================
# 📌 Gestion du stockage contacts
# ================================

CONTACTS_FILE = Path(__file__).resolve().parent.parent / "data" / "contacts.json"


def _ensure_contacts_file():
    CONTACTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not CONTACTS_FILE.exists():
        CONTACTS_FILE.write_text("[]", encoding="utf-8")


def save_contact(contact: dict):
    """
    Sauvegarde un contact dans backend/data/contacts.json
    """
    _ensure_contacts_file()

    try:
        existing = json.loads(CONTACTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        existing = []

    existing.append(contact)

    CONTACTS_FILE.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


# ==============================================
# 📌 État du formulaire en mémoire (par user_id)
# ==============================================

_FORM_STATES: Dict[str, Dict[str, Any]] = {}


def _user_key(user_id: Optional[str]) -> str:
    return user_id or "anonymous"


def has_active_form(user_id: Optional[str]) -> bool:
    """
    Indique si ce user est en plein remplissage de formulaire.
    Utilisé par orchestrator_agent.
    """
    return _user_key(user_id) in _FORM_STATES


# ===========================
# 📌 Extraction automatique
# ===========================

def _extract_email(text: str) -> Optional[str]:
    m = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    return m.group(0) if m else None


def _extract_phone(text: str) -> Optional[str]:
    m = re.search(r"(\+?\d[\d \-]{7,}\d)", text)
    return m.group(0) if m else None


def _extract_name(text: str, email: Optional[str], phone: Optional[str]) -> Optional[str]:
    clean = text
    if email:
        clean = clean.replace(email, "")
    if phone:
        clean = clean.replace(phone, "")
    clean = clean.replace(",", " ").strip()
    clean = re.sub(r"\s+", " ", clean)

    if not clean:
        return None

    parts = clean.split(" ")
    if len(parts) > 5:
        parts = parts[:5]
    name = " ".join(p for p in parts if p)
    return name or None


# =======================
# 📌 Contact Agent
# =======================

class ContactAgent:
    """
    Agent responsable de la collecte des coordonnées (formulaire contact).
    1) Il demande nom + email + téléphone dans un seul message (réponse générée par LLM).
    2) L'utilisateur répond → extraction + sauvegarde JSON.
    3) Le LLM génère un message de confirmation personnalisé.
    """

    name = "form_agent"

    async def handle(self, message: ChatMessage) -> ChatResponse:
        user_key = _user_key(message.user_id)
        user_text = (message.message or "").strip()

        state = _FORM_STATES.get(user_key)

        # ---------------------------------------
        # 1️⃣ PAS D'ÉTAT -> démarrage formulaire
        #    → on demande les infos via le LLM
        # ---------------------------------------
        if state is None:
            _FORM_STATES[user_key] = {"step": "awaiting_details"}

            system_prompt = (
                "Tu es un assistant d'admission pour l'école d'ingénieurs **ESILV**.\n"
                "INFORMATIONS IMPORTANTES SUR L'ÉCOLE :\n"
                "- ESILV signifie « École Supérieure d'Ingénieurs Léonard de Vinci ».\n"
                "- C'est une école d'ingénieurs située à Paris-La Défense, au sein du Pôle Léonard de Vinci.\n"
                "- Tu NE DOIS JAMAIS réinventer ou redéfinir l'acronyme ESILV.\n"
                "- Si tu dois expliquer l'acronyme, utilise exactement : "
                "« l’ESILV, École Supérieure d'Ingénieurs Léonard de Vinci à Paris-La Défense ».\n\n"
                "CONTEXTE DE TA MISSION :\n"
                "L'utilisateur souhaite être recontacté par l'école ou laisser ses coordonnées.\n"
                "Ta tâche : rédiger une **réponse en français**, polie et professionnelle, qui :\n"
                "- remercie l'utilisateur pour son intérêt pour l'ESILV,\n"
                "- explique que pour être recontacté, il doit envoyer **dans un seul message** :\n"
                "    - son nom complet,\n"
                "    - son adresse e-mail,\n"
                "    - son numéro de téléphone (optionnel),\n"
                "- propose éventuellement d'indiquer le programme ou le niveau qui l'intéresse,\n"
                "- reste courte (4–6 phrases) et utilise le vouvoiement.\n"
                "Ne donne aucune information inventée (pas de délais précis, pas de noms de personnes)."
            )

            user_prompt = (
                f"Message utilisateur : {user_text}\n\n"
                "Rédige cette réponse de demande de coordonnées."
            )

            try:
                llm_reply = await llm_client.generate(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                )
                reply = llm_reply.strip()
            except Exception:
                # Fallback template si le LLM plante
                reply = (
                    "Merci pour votre intérêt pour l'ESILV 👏\n\n"
                    "Pour que nous puissions vous recontacter, pouvez-vous me donner **dans un seul message** :\n"
                    "- votre **nom complet**,\n"
                    "- votre **adresse e-mail**, \n"
                    "- votre **numéro de téléphone** (optionnel),\n"
                    "- et éventuellement le programme ou le niveau qui vous intéresse.\n\n"
                    "Exemple : Jean Dupont, jean.dupont@mail.com, 06 12 34 56 78, intéressé par le cycle ingénieur."
                )

            return ChatResponse(
                reply=reply,
                agent=self.name,
                intent="contact",
                context_documents=[],
                metadata={
                    "form_step": "awaiting_details",
                    "provider": llm_client.provider,
                    "model": llm_client.model,
                },
            )

        # --------------------------------------------------------
        # 2️⃣ ÉTAT EN COURS -> tentative extraction des informations
        # --------------------------------------------------------
        if state.get("step") == "awaiting_details":
            email = _extract_email(user_text)
            phone = _extract_phone(user_text)
            name = _extract_name(user_text, email, phone)

            # ❌ informations insuffisantes
            if not email or not name:
                reply = (
                    "Merci pour ces informations 🙏\n"
                    "Je n'ai pas réussi à trouver **clairement** votre nom et votre e-mail dans ce message.\n\n"
                    "Pouvez-vous renvoyer un message du type :\n"
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
                        "provider": llm_client.provider,
                        "model": llm_client.model,
                    },
                )

            # ---------------------------------------
            # ✅ extraction ok → on enregistre
            # ---------------------------------------
            contact_data = {
                "full_name": name,
                "email": email,
                "phone": phone,
                "raw_message": user_text,
                "user_id": message.user_id,
                "created_at": datetime.utcnow().isoformat(),
            }

            save_contact(contact_data)

            # On efface l'état du formulaire
            _FORM_STATES.pop(user_key, None)

            # ---------------------------------------
            # 🧠 Appel LLM pour un message de confirmation naturel
            # ---------------------------------------
            system_prompt = (
                "Tu es un assistant d'admission pour l'école d'ingénieurs **ESILV**.\n"
                "INFORMATIONS IMPORTANTES SUR L'ÉCOLE :\n"
                "- ESILV signifie « École Supérieure d'Ingénieurs Léonard de Vinci ».\n"
                "- C'est une école d'ingénieurs située à Paris-La Défense, au sein du Pôle Léonard de Vinci.\n"
                "- Tu NE DOIS JAMAIS réinventer ou redéfinir l'acronyme ESILV.\n"
                "- Si tu dois rappeler ce que c'est, utilise exactement : "
                "« l’ESILV, École Supérieure d'Ingénieurs Léonard de Vinci à Paris-La Défense ».\n\n"
                "CONTEXTE DE TA MISSION :\n"
                "On t'envoie les coordonnées qu'un candidat vient de fournir pour être recontacté.\n"
                "Tu dois répondre par un message de **confirmation poli en français**, qui :\n"
                "- remercie la personne pour son intérêt pour l'ESILV,\n"
                "- récapitule les infos reçues (nom, email, téléphone s'il existe),\n"
                "- explique qu'elle pourra être recontactée par l'équipe ESILV,\n"
                "- reste concise (5–7 phrases max).\n"
                "Ne rajoute pas d'informations inventées (pas de délais précis, pas de noms de personnes).\n"
            )

            user_prompt = (
                f"Nom : {name}\n"
                f"Email : {email}\n"
                f"Téléphone : {phone or 'non renseigné'}\n"
                f"Message initial : {user_text}\n\n"
                "Rédige le message de confirmation."
            )

            try:
                llm_reply = await llm_client.generate(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                )
                reply = llm_reply.strip()
            except Exception:
                # Fallback en cas de problème LLM
                reply = (
                    f"Merci **{name}** ! 🙌\n\n"
                    "J'ai bien enregistré vos coordonnées :\n"
                    f"- Email : **{email}**\n"
                    f"- Téléphone : **{phone or 'non renseigné'}**\n\n"
                    "Un membre de l'équipe ESILV pourra vous recontacter prochainement."
                )

            return ChatResponse(
                reply=reply,
                agent=self.name,
                intent="contact",
                context_documents=[],
                metadata={
                    "form_step": "completed",
                    "saved_contact": contact_data,
                    "provider": llm_client.provider,
                    "model": llm_client.model,
                },
            )

        # ---------------------------------------
        # 3️⃣ fallback / reset
        # ---------------------------------------
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
            metadata={
                "form_step": "reset",
                "provider": llm_client.provider,
                "model": llm_client.model,
            },
        )


contact_agent = ContactAgent()
