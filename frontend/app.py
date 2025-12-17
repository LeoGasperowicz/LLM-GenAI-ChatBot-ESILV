import uuid
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
import requests

from config import APP_TITLE, BACKEND_BASE_URL
from api_client import (
    chat as api_chat,
    get_admin_stats,
    get_contacts,
    APIClientError,
)

# =========================
# THEME / STYLE
# =========================

ESILV_RED = "#CF1053"


def inject_sidebar_style():
    st.markdown(
        f"""
        <style>
        section[data-testid="stSidebar"] {{
            background-color: {ESILV_RED} !important;
        }}

        section[data-testid="stSidebar"] * {{
            color: #ffffff !important;
        }}

        section[data-testid="stSidebar"] hr {{
            border-color: rgba(255,255,255,0.25) !important;
        }}

        section[data-testid="stSidebar"] button {{
            background-color: rgba(255,255,255,0.16) !important;
            color: #ffffff !important;
            border-radius: 10px !important;
            border: 1px solid rgba(255,255,255,0.35) !important;
            width: 100% !important;
            text-align: left !important;
            font-weight: 600 !important;
        }}
        section[data-testid="stSidebar"] button:hover {{
            background-color: rgba(255,255,255,0.28) !important;
            border: 1px solid rgba(255,255,255,0.55) !important;
        }}

        button[kind="header"] {{
            color: #ffffff !important;
        }}

        /* Highlight de la question ciblée */
        .esilv-highlight {{
            border: 2px solid rgba(207,16,83,0.55);
            border-radius: 14px;
            padding: 6px 10px;
            background: rgba(207,16,83,0.06);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================
# STATE / UTILS
# =========================

def get_user_id() -> str:
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = str(uuid.uuid4())
    return st.session_state["user_id"]


def init_state():
    if "messages" not in st.session_state:
        st.session_state["messages"] = []  # [{role, content, meta}]
    if "show_uploader" not in st.session_state:
        st.session_state["show_uploader"] = False
    if "jump_to_idx" not in st.session_state:
        st.session_state["jump_to_idx"] = None  # index du message user cliqué
    if "upload_status" not in st.session_state:
        st.session_state["upload_status"] = []  # feedback upload (liste de strings)


def upload_files_to_backend(uploaded_files, location: str = "main"):
    placeholder = st.sidebar if location == "sidebar" else st
    if not uploaded_files:
        return

    placeholder.info("Envoi des documents...")

    ok_msgs = []
    err_msgs = []

    for f in uploaded_files:
        files = {"file": (f.name, f.getvalue())}
        try:
            resp = requests.post(
                f"{BACKEND_BASE_URL}/upload-document",
                files=files,
                timeout=120,
            )
            if resp.status_code == 200:
                data = resp.json()
                ok_msgs.append(f"✔ {data.get('filename', f.name)} ajouté")
            else:
                err_msgs.append(f"❌ {f.name} : {resp.text}")
        except Exception as e:
            err_msgs.append(f"❌ {f.name} : {e}")

    st.session_state["upload_status"] = ok_msgs + err_msgs

    for m in ok_msgs:
        placeholder.success(m)
    for m in err_msgs:
        placeholder.error(m)


def render_sources(ctx_docs):
    if not ctx_docs:
        return

    with st.expander("📚 Voir les sources utilisées", expanded=False):
        for d in ctx_docs:
            src = d.get("source") or "Document"
            page = d.get("page", "N/A")
            url = d.get("url") or d.get("source_url")

            label = src
            if page not in (None, "N/A"):
                label += f" — page {page}"

            if url:
                st.markdown(f"- 📄 [{label}]({url})")
            else:
                st.markdown(f"- 📄 {label}")


def scroll_to_message(target_idx: int):
    """
    Scroll vers l'ancre HTML #msg-{target_idx}
    (JS exécuté dans un iframe -> parent.document)
    """
    if target_idx is None:
        return

    anchor_id = f"msg-{target_idx}"
    components.html(
        f"""
        <script>
        (function() {{
          const id = "{anchor_id}";
          const tryScroll = () => {{
            const el = parent.document.getElementById(id);
            if (el) {{
              el.scrollIntoView({{ behavior: "smooth", block: "start" }});
            }}
          }};
          setTimeout(tryScroll, 60);
          setTimeout(tryScroll, 250);
          setTimeout(tryScroll, 600);
        }})();
        </script>
        """,
        height=0,
    )


# =========================
# CHAT PAGE
# =========================

def render_chat_page():
    st.header("💬 Assistant ESILV")

    st.markdown(
        """
L'assistant peut répondre à des questions sur :
- Les **programmes ESILV**
- Les **admissions**
- Les **cours / spécialisations**
- L’**international**
"""
    )

    user_id = get_user_id()

    # Feedback upload (affiché une fois)
    if st.session_state.get("upload_status"):
        for msg in st.session_state["upload_status"]:
            if msg.startswith("✔"):
                st.success(msg)
            else:
                st.error(msg)
        st.session_state["upload_status"] = []

    # Scroll si clic historique
    jump_idx = st.session_state.get("jump_to_idx")
    if jump_idx is not None:
        scroll_to_message(jump_idx)

    # Historique complet du chat + ancres
    for idx, msg in enumerate(st.session_state["messages"]):
        if msg["role"] == "user":
            # ancre HTML (pour scroll)
            st.markdown(f"<div id='msg-{idx}'></div>", unsafe_allow_html=True)

            # highlight si c'est la question ciblée
            if idx == jump_idx:
                st.markdown("<div class='esilv-highlight'>", unsafe_allow_html=True)

            with st.chat_message("user"):
                st.write(msg["content"])

            if idx == jump_idx:
                st.markdown("</div>", unsafe_allow_html=True)

        else:
            with st.chat_message("assistant"):
                st.write(msg["content"])
                ctx_docs = (msg.get("meta") or {}).get("context_documents") or []
                render_sources(ctx_docs)

    # Barre du bas : + upload + chat_input
    with st.container():
        col_plus, col_input = st.columns([1, 10], vertical_alignment="bottom")

        with col_plus:
            if st.button("➕", key="toggle_upload_plus", help="Uploader un document"):
                st.session_state["show_uploader"] = not st.session_state["show_uploader"]

            if st.session_state["show_uploader"]:
                files = st.file_uploader(
                    "Docs",
                    type=["pdf", "txt", "docx"],
                    accept_multiple_files=True,
                    key="uploader_plus",
                    label_visibility="collapsed",
                )
                if files and st.button("📤 Envoyer", key="send_upload_plus"):
                    upload_files_to_backend(files, location="main")
                    st.session_state["show_uploader"] = False
                    st.rerun()

        with col_input:
            prompt = st.chat_input("Posez votre question sur l'ESILV…")

    # Envoi ENTER
    if prompt:
        # on sort du mode "ciblage"
        st.session_state["jump_to_idx"] = None

        # afficher la question immédiatement
        st.session_state["messages"].append({"role": "user", "content": prompt, "meta": {}})
        with st.chat_message("user"):
            st.write(prompt)

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
            "context_documents": resp.get("context_documents") or [],
        }

        st.session_state["messages"].append({"role": "assistant", "content": reply_text, "meta": meta})
        with st.chat_message("assistant"):
            st.write(reply_text)
            render_sources(meta["context_documents"])

        # refresh pour que l'historique soit clean
        st.rerun()


# =========================
# ADMIN PAGE
# =========================

def render_admin_page():
    st.header("🛠️ Dashboard Admin ESILV Assistant")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Statistiques globales")
        try:
            stats = get_admin_stats()
        except Exception as e:
            st.error(f"Erreur : {e}")
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

    with col2:
        st.subheader("📇 Personnes à recontacter")
        try:
            contacts = get_contacts()
        except Exception as e:
            st.error(f"Erreur : {e}")
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
    st.caption("Ce dashboard utilise les endpoints `/api/admin/stats` et `/api/admin/contacts` du backend FastAPI.")


# =========================
# SIDEBAR
# =========================

def render_sidebar():
    inject_sidebar_style()

    st.sidebar.image("Logo-ESILV.jpg", use_container_width=True)
    st.sidebar.markdown("---")

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Choisissez une vue", ["Chat étudiant", "Admin"], index=0)

    st.sidebar.markdown("---")
    st.sidebar.subheader("🕓 Historique")

    msgs = st.session_state.get("messages", [])
    user_msgs = [(i, m.get("content", "")) for i, m in enumerate(msgs) if m.get("role") == "user"]

    if user_msgs:
        st.sidebar.caption("Clique sur une question :")
        for idx, txt in reversed(user_msgs[-10:]):
            short = txt.replace("\n", " ").strip()
            if len(short) > 60:
                short = short[:60] + "…"

            if st.sidebar.button(short, key=f"history_btn_{idx}"):
                st.session_state["jump_to_idx"] = idx
                st.rerun()
    else:
        st.sidebar.caption("Aucune question pour le moment.")

    st.sidebar.markdown("---")

    if st.sidebar.button("🗑️ Nouvelle conversation", key="new_convo"):
        st.session_state["messages"] = []
        st.session_state["jump_to_idx"] = None
        st.session_state["show_uploader"] = False
        st.session_state["upload_status"] = []
        st.rerun()

    st.sidebar.caption("Projet ESILV Smart Assistant")
    return page


# =========================
# MAIN
# =========================

def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="🤖", layout="wide")

    init_state()
    page = render_sidebar()

    st.title(APP_TITLE)

    if page == "Chat étudiant":
        render_chat_page()
    else:
        render_admin_page()


if __name__ == "__main__":
    main()
