import uuid
from datetime import datetime

import streamlit as st

from config import APP_TITLE
from api_client import (
    chat as api_chat,
    get_admin_stats,
    get_contacts,
    APIClientError,
)


# ---------- Utils ----------


def get_user_id() -> str:
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = str(uuid.uuid4())
    return st.session_state["user_id"]


def init_chat_state():
    if "messages" not in st.session_state:
        # Liste de dicts {role: "user"/"assistant", content: str, meta: dict}
        st.session_state["messages"] = []


# ---------- UI ----------


def render_chat_page():
    st.header("💬 Assistant ESILV")

    st.markdown(
        """
L'assistant peut répondre à des questions sur :
- les **programmes ESILV**  
- les **admissions**  
- les **cours / spécialisations**  
- et peut vous aider à laisser vos **coordonnées** pour être recontacté.
"""
    )

    init_chat_state()
    user_id = get_user_id()

    # Affichage de l'historique
    for msg in st.session_state["messages"]:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.write(msg["content"])
                meta = msg.get("meta") or {}

                # 🔍 Afficher les sources RAG pour les anciens messages
                ctx_docs = meta.get("context_documents") or []
                if ctx_docs:
                    st.markdown("**📚 Sources utilisées :**")
                    for i, doc in enumerate(ctx_docs, start=1):
                        source = doc.get("source") or f"Document {i}"
                        page = doc.get("page")
                        url = doc.get("url")
                        snippet = doc.get("snippet") or ""

                        # Lien cliquable si une URL est fournie
                        if url:
                            label = f"{source}"
                            if page not in (None, "N/A"):
                                label += f" — page {page}"
                            st.markdown(f"- 📄 [{label}]({url})")
                        else:
                            if page not in (None, "N/A"):
                                st.markdown(f"- 📄 {source} — page {page}")
                            else:
                                st.markdown(f"- 📄 {source}")

                        # Petit extrait
                        if snippet:
                            st.caption(snippet[:300] + ("…" if len(snippet) > 300 else ""))

                # Détails techniques (debug)
                if "agent" in meta or "intent" in meta:
                    with st.expander("Détails techniques (debug)", expanded=False):
                        st.json(meta)

    # Zone de saisie
    prompt = st.chat_input("Posez votre question sur l'ESILV...")

    if prompt:
        # Afficher immédiatement le message utilisateur
        st.session_state["messages"].append(
            {"role": "user", "content": prompt, "meta": {}}
        )
        with st.chat_message("user"):
            st.write(prompt)

        # Appel backend
        try:
            with st.spinner("Réflexion de l'assistant..."):
                resp = api_chat(user_id=user_id, message=prompt)
        except APIClientError as e:
            with st.chat_message("assistant"):
                st.error(f"Erreur côté serveur : {e}")
            return
        except Exception as e:
            with st.chat_message("assistant"):
                st.error(f"Erreur inattendue : {e}")
            return

        reply_text = resp.get("reply", "(Pas de réponse)")
        meta = {
            "agent": resp.get("agent"),
            "intent": resp.get("intent"),
            "metadata": resp.get("metadata"),
            "context_documents": resp.get("context_documents"),
        }

        # Enregistrer la réponse
        st.session_state["messages"].append(
            {"role": "assistant", "content": reply_text, "meta": meta}
        )

        # Afficher la réponse
        with st.chat_message("assistant"):
            st.write(reply_text)

            # 🔍 Afficher les documents de contexte (RAG) renvoyés par le backend
            ctx_docs = meta.get("context_documents") or []
            if ctx_docs:
                st.markdown("**📚 Sources utilisées :**")
                for i, doc in enumerate(ctx_docs, start=1):
                    source = doc.get("source") or f"Document {i}"
                    page = doc.get("page")
                    url = doc.get("url")
                    snippet = doc.get("snippet") or ""

                    if url:
                        label = f"{source}"
                        if page not in (None, "N/A"):
                            label += f" — page {page}"
                        st.markdown(f"- 📄 [{label}]({url})")
                    else:
                        if page not in (None, "N/A"):
                            st.markdown(f"- 📄 {source} — page {page}")
                        else:
                            st.markdown(f"- 📄 {source}")

                    if snippet:
                        st.caption(snippet[:300] + ("…" if len(snippet) > 300 else ""))

            # Bloc debug
            if meta:
                with st.expander("Détails techniques (debug)", expanded=False):
                    st.json(meta)


def render_admin_page():
    st.header("🛠️ Dashboard Admin ESILV Assistant")

    col1, col2 = st.columns(2)

    # --- Stats globales ---
    with col1:
        st.subheader("Statistiques globales")
        try:
            stats = get_admin_stats()
        except APIClientError as e:
            st.error(f"Erreur API : {e}")
            stats = None
        except Exception as e:
            st.error(f"Erreur inattendue : {e}")
            stats = None

        if stats:
            st.metric("Nombre de conversations", stats.get("total_conversations", 0))
            st.metric("Nombre total de messages", stats.get("total_messages", 0))

            st.markdown("**Intents les plus fréquents :**")
            intents = stats.get("top_intents", {})
            if intents:
                for intent, count in intents.items():
                    st.write(f"- `{intent}` : {count}")
            else:
                st.write("_Aucun intent pour l'instant._")

    # --- Contacts collectés / personnes à recontacter ---
    with col2:
        st.subheader("📇 Personnes à recontacter")

        try:
            contacts = get_contacts()
        except APIClientError as e:
            st.error(f"Erreur API : {e}")
            contacts = []
        except Exception as e:
            st.error(f"Erreur inattendue : {e}")
            contacts = []

        if contacts:
            for c in contacts:
                st.markdown("---")

                name = c.get("full_name") or "Nom inconnu"
                email = c.get("email") or "Email inconnu"
                phone = c.get("phone") or "Téléphone non renseigné"
                raw_message = c.get("raw_message") or ""
                created_str = c.get("created_at")

                st.markdown(f"**👤 {name}**")
                st.write(f"📧 {email}")
                st.write(f"📱 {phone}")

                if created_str:
                    try:
                        dt = datetime.fromisoformat(created_str)
                        st.write(f"🕒 {dt.strftime('%d/%m/%Y %H:%M')}")
                    except Exception:
                        st.write(f"🕒 {created_str}")

                if raw_message:
                    st.write("📝 Message initial :")
                    st.info(raw_message)
        else:
            st.info("Aucune personne à recontacter pour le moment.")

    st.markdown("---")
    st.caption(
        "Ce dashboard utilise les endpoints `/api/admin/stats` et `/api/admin/contacts` "
        "du backend FastAPI."
    )


def render_sidebar():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Choisissez une vue",
        ["Chat étudiant", "Admin"],
        index=0,
    )
    st.sidebar.markdown("---")
    st.sidebar.caption("Projet ESILV Smart Assistant")

    return page


# ---------- Main ----------


def main():
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🤖",
        layout="wide",
    )

    page = render_sidebar()

    st.title(APP_TITLE)

    if page == "Chat étudiant":
        render_chat_page()
    elif page == "Admin":
        render_admin_page()


if __name__ == "__main__":
    main()
