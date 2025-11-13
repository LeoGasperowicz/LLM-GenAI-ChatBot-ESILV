# LLM-GenAI-ChatBot-ESILV
ESILV Smart Assistant
This project aims to design and implement an intelligent chatbot dedicated to the ESILV
engineering school. The system should be capable of:

- Answering questions about programs, admissions, and courses using ESILV website and
internal documentation.
- Interacting with users to collect contact details for follow-up or registration.
- Coordinating multiple specialized agents (retrieval, form-filling, orchestration) to handle
complex user queries.

The chatbot must integrate both retrieval-augmented generation (RAG) for factual answers and
multi-agent coordination for structured interactions.
Students can deploy it locally with Ollama or on the Google AI platform (GCP).
A Streamlit front-end will serve as the user interface for chatting, document uploads, and admin
visualization.

# ⚙️ 1. Requirements
Please install the following:
### Ollama  
Download and install Ollama from:  
https://ollama.com/download

Ollama is required to run the **Mistral** LLM locally.

---

# 🤖 2. Install the Mistral model 
After installing Ollama, open a **terminal (CMD or Powershell)** and run:

```bash
ollama pull mistral
```bash
---

📦 3. Clone the project

```bash
git clone https://github.com/YOUR-REPO/LLM-GenAI-ChatBot-ESILV.git
cd LLM-GenAI-ChatBot-ESILV
```bash

---

📚 4. Install dependencies

At the root of the project:

```bash
python -m pip install -r requirements.txt
```bash

---

🚀 5. Start the backend (FastAPI)

In a new terminal:
```bash
uvicorn backend.main:app --reload
```bash

Backend is available at:
👉 http://127.0.0.1:8000

API docs:
👉 http://127.0.0.1:8000/docs

---

💬 6. Start the frontend (Streamlit)

In another terminal:
```bash
cd frontend
python -m streamlit run app.py
```bash

Frontend UI is available at:
👉 http://localhost:8501
