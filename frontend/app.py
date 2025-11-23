import uuid
from datetime import datetime

import streamlit as st
import requests

from config import APP_TITLE, BACKEND_BASE_URL
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


def upload_files_to_backend(uploaded_files, location: str = "main"):
    """
    Envoie les fichiers au backend et affiche les messages de retour.
    location : "main" (zone centrale) ou "sidebar".
    """
    placeholder = st.sidebar if location == "sidebar" else st

    if not uploaded_files:
        return

    placeholder.info("Envoi des documents...")

    for f in uploaded_files:
        files = {"file": (f.name, f.getvalue())}
        try:
            resp = requests.post(
                f"{BACKEND_BASE_URL}/upload-document",
                files=files,
            )
            if resp.status_code == 200:
                data = resp.json()
                placeholder.success(f"✔ {data.get('filename', f.name)} ajouté")
            else:
                placeholder.error(f"Erreur pour {f.name} : {resp.text}")
        except Exception as e:
            placeholder.error(f"Erreur de connexion : {e}")


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

    # état pour afficher / cacher l'uploader à gauche de la barre
    if "show_bottom_uploader" not in st.session_state:
        st.session_state["show_bottom_uploader"] = False

    # Affichage de l'historique des messages
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
                            st.caption(
                                snippet[:300] + ("…" if len(snippet) > 300 else "")
                            )

                # Détails techniques (debug)
                if "agent" in meta or "intent" in meta:
                    with st.expander("Détails techniques (debug)", expanded=False):
                        st.json(meta)

    # ---- Zone de saisie custom : onglet upload à gauche + barre de recherche + bouton envoyer ----
    with st.container():
        col_plus, col_input, col_send = st.columns([1, 7, 1])

        # Colonne gauche : onglet +
        with col_plus:
            if st.button("➕", key="toggle_bottom_uploader", help="Uploader des documents"):
                st.session_state["show_bottom_uploader"] = not st.session_state.get(
                    "show_bottom_uploader", False
                )

            if st.session_state.get("show_bottom_uploader", False):
                uploaded_files_bottom = st.file_uploader(
                    "Docs",
                    type=["pdf", "txt", "docx"],
                    accept_multiple_files=True,
                    key="bottom_uploader",
                    label_visibility="collapsed",
                )
                if uploaded_files_bottom and st.button("📤", key="bottom_upload_btn"):
                    upload_files_to_backend(uploaded_files_bottom, location="main")

        # Colonne centrale : barre de recherche / saisie
        with col_input:
            user_input = st.text_input(
                "Posez votre question sur l'ESILV...",
                key="chat_input",
                label_visibility="collapsed",
            )

        # Colonne droite : bouton envoyer
        with col_send:
            send = st.button("➤", key="send_message")

    # Si on clique sur Envoyer, on traite le message
    if send and user_input.strip():
        prompt = user_input.strip()

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
                        st.caption(
                            snippet[:300] + ("…" if len(snippet) > 300 else "")
                        )

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

    st.sidebar.image("Logo-ESILV.jpg", use_container_width=True)
    st.sidebar.markdown("---")

    st.sidebar.title("Navigation")

    # -------------------------------------------------

    page = st.sidebar.radio(
        "Choisissez une vue",
        ["Chat étudiant", "Admin"],
        index=0,
    )
    st.sidebar.markdown("---")
    st.sidebar.subheader("🕓 Historique de vos questions")

    messages = st.session_state.get("messages", [])
    user_messages = [m["content"] for m in messages if m.get("role") == "user"]

    if user_messages:
        # On affiche les 10 dernières questions (de la plus récente à la plus ancienne)
        for i, text in enumerate(reversed(user_messages[-10:]), start=1):
            short = text.strip().replace("\n", " ")
            if len(short) > 60:
                short = short[:60] + "…"
            st.sidebar.markdown(f"{i}. {short}")
    else:
        st.sidebar.caption("Aucune question pour le moment.")

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
