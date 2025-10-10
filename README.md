# Holos Chatbot

This repository contains a local copy of the Holos Chatbot — a small FastAPI + Streamlit application that demonstrates a RAG (retrieval-augmented generation) pipeline using FAISS and LangChain-related components.

## What is included
- `holos/` — application modules (API, RAG wiring, conversation/heuristics, data loaders)
- `streamlit_app.py` — Streamlit frontend that talks to the FastAPI backend
- `requirements.txt` — Python dependencies (pinned ranges)
- `data/` — sample data files used by the RAG index

## Quick setup (Windows PowerShell)

Open PowerShell in the project root and run:

```powershell
# create and activate a virtual environment
python -m venv .venv
. .\.venv\Scripts\Activate.ps1

# upgrade packaging tools
python -m pip install --upgrade pip setuptools wheel

# install dependencies
pip install -r requirements.txt
```

Notes:
- The project was developed on Python 3.12. Use that or a compatible Python version.
- The `.venv/` directory is excluded from the repo (do not push it to GitHub).

## Environment variables
- `OPENAI_API_KEY` — (optional) if you use OpenAI embeddings or models.
- `EMBED_MODEL` — embedding model name (default: `text-embedding-3-small`).

Create a `.env` file in the project root with lines like:

```env
OPENAI_API_KEY=sk-...
EMBED_MODEL=text-embedding-3-small
```

## Run the backend (FastAPI)

From the activated virtual environment:

```powershell
# development server (no extra process manager)
uvicorn holos.api:app --host 127.0.0.1 --port 8001 --reload
```

The backend provides a `/chat` endpoint used by the Streamlit frontend.

## Run the frontend (Streamlit)

In a separate PowerShell window (activated `.venv`):

```powershell
# point the UI to the API
$env:API_URL = 'http://127.0.0.1:8001/chat'
streamlit run streamlit_app.py
```

## Vector index location and rebuild

The FAISS vector store is stored under a user-writable path by default (e.g., `%USERPROFILE%\.holos\faiss`). If you need to force a rebuild of the index, stop the backend, remove the vector directory, and restart the API. Example (PowerShell):

```powershell
# WARNING: deletes your local index — only do it if you want a fresh rebuild
Remove-Item -Recurse -Force $env:USERPROFILE\.holos\faiss
# then restart uvicorn
```

## Dependency notes

- There was an observed dependency mismatch during development between `langgraph-prebuilt` and `langchain-core`. If you encounter installation problems, check `requirements.txt` and consider adjusting package versions or using a locked environment. I can help reconcile these versions if you want.

## Troubleshooting
- If Streamlit cannot reach the API, make sure uvicorn is running and listening on the same host/port the UI expects (`127.0.0.1:8001` by default).
- If you see permission or locked-file errors when creating `.venv`, delete and recreate the venv and re-install dependencies.

## Pushing changes

This repo is already pushed to: https://github.com/shraddhac0206/Holos-Chatbot

If you want me to add CI, tags, or a more detailed README (with architecture diagram or tests), tell me what you'd like and I will add it and push another commit.

---
_Generated and updated locally on your request._
# Holos-Chatbot

Local copy of the Holos Chatbot project.
