import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, DirectoryLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from streamlit.runtime import state


from dotenv import load_dotenv
load_dotenv()  # ensures .env is read even in standalone runs

# -------------------------------------------------------
# Configuration
# -------------------------------------------------------

# Embedding model used to convert text into numeric vectors
EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Path for storing FAISS index (vector database)
# Defaults to ~/.holos/faiss but can be overridden by VECTOR_PATH environment variable
VECTOR_PATH = os.getenv("VECTOR_PATH", str(Path.home() / ".holos" / "faiss"))
os.makedirs(VECTOR_PATH, exist_ok=True)  # Ensure directory exists

# Default path where documents (text, PDFs, etc.) are stored
DOCS_PATH = "data/docs/"

# -------------------------------------------------------
# Class: RAGRetriever
# -------------------------------------------------------
# Purpose:
# This class handles the core Retrieval-Augmented Generation (RAG) step.
# It builds or loads a FAISS vector database using text embeddings
# and retrieves the most relevant documents for a given query.
class RAGRetriever:
    # os.environ["CURRENT_CROP"] = state["context"].get("crop", "")
    # os.environ["CURRENT_REGION"] = state["context"].get("region", "")
    def __init__(self, docs_path: str = DOCS_PATH):
        # Use a single data root and scan it recursively so we don't rely on
        # a hard-coded, ordered list of folders. This ensures all data files
        # under the data tree are discovered and indexed.
        crop = (os.getenv("CURRENT_CROP") or "").lower()
        region = (os.getenv("CURRENT_REGION") or "").lower()


        if crop and region:
            crop_region_path = os.path.join(docs_path, crop, region)
        elif crop:
            crop_region_path = os.path.join(docs_path, crop)
        else:
            crop_region_path = docs_path

        self.docs_root = crop_region_path if os.path.exists(crop_region_path) else docs_path

        # Initialize OpenAI embedding model
        self.embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
        # Load an existing FAISS index or build a new one
        self.vs = self._load_or_build()

    # ---------------------------------------------------
    # Function: _load_or_build
    # ---------------------------------------------------
    # Purpose:
    # Checks if a FAISS index already exists. If yes, loads it.
    # Otherwise, scans document folders, splits them into chunks,
    # creates embeddings, and builds a new FAISS index.
    def _load_or_build(self):
        idx_file = os.path.join(VECTOR_PATH, "index.faiss")

        # If an index already exists, load it from disk
        if os.path.exists(idx_file):
            return FAISS.load_local(VECTOR_PATH, self.embeddings, allow_dangerous_deserialization=True)

        # If no index exists, create the folder
        os.makedirs(VECTOR_PATH, exist_ok=True)
        docs = []

        # Define supported file loaders (scan the docs_root recursively)
        loaders = [
            DirectoryLoader(self.docs_root, glob="**/*.txt", loader_cls=TextLoader, show_progress=True),
            DirectoryLoader(self.docs_root, glob="**/*.md", loader_cls=TextLoader, show_progress=True),
            #DirectoryLoader(self.docs_root, glob="**/*.pdf", loader_cls=PyPDFLoader, show_progress=True),
            DirectoryLoader(self.docs_root, glob="**/*.docx", loader_cls=TextLoader, show_progress=True),
        ]

        

        # Try loading files from each loader (they will walk subfolders)
        for ld in loaders:
            try:
                print(ld , " In load or build ..in rag...trying to load")
                docs.extend(ld.load())
            except Exception:
                # If a loader fails for some reason, skip it and continue
                print(ld, " In load or build ..in rag...loader failed")
                pass

        # If no documents found, return None (no retriever)
        if not docs:
            return None

        # Split large documents into smaller overlapping text chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,     # Each chunk up to 1200 characters
            chunk_overlap=150,   # Overlap between chunks for context continuity
            separators=["\n##", "\n#", "\n- ", "\n", " "]  # Split on headings and newlines
        )
        splits = splitter.split_documents(docs)

        # Build FAISS vector store (embedding index)
        vs = FAISS.from_documents(splits, self.embeddings)

        # Save the index locally for reuse
        vs.save_local(VECTOR_PATH)
        return vs

    # ---------------------------------------------------
    # Function: retrieve
    # ---------------------------------------------------
    # Purpose:
    # Retrieve the most relevant document chunks for a given query.
    # Returns a list of text snippets with metadata.
    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        vs = self.vs

        # If FAISS index is not loaded (maybe just created elsewhere), try loading it
        if vs is None:
            idx_file = os.path.join(VECTOR_PATH, "index.faiss")
            if os.path.exists(idx_file):
                vs = FAISS.load_local(VECTOR_PATH, self.embeddings, allow_dangerous_deserialization=True)
                self.vs = vs
            else:
                return []  # No index available → return empty list

        # Create a retriever object to search top-k similar chunks
        retriever = vs.as_retriever(search_kwargs={"k": k})
        docs = retriever.get_relevant_documents(query)

        # Convert LangChain Document objects into simple dicts
        results = []
        for d in docs:
            results.append({
                "content": d.page_content,  # Extracted text
                "metadata": {**(d.metadata or {}), "source": (d.metadata or {}).get("source", "")}
            })

        return results  # Return the top matching chunks
