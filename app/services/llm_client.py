# app/services/llm_client.py

import os
from typing import List

from openai import OpenAI
from chromadb import PersistentClient
from chromadb.errors import NotFoundError
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
)
import pymupdf
from app.core.settings import Settings

RETRIEVAL_TOP_K = 5
EMBEDDING_PROVIDERS = ["CPUExecutionProvider"]

def send_to_llm(
    messages: List[dict[str, str]], collection_name
) -> str:
    if not messages or messages[-1]["role"] != "user":
        raise ValueError("Last message must be a user message")


    history       = messages[:-1]
    original_user = messages[-1]["content"]

    try:
        contexts = query_vector_db(original_user, collection_name)
        augmented_user = build_rag_prompt(original_user, contexts)
        rag_messages = history + [{"role": "user", "content": augmented_user}]
    except NotFoundError:
        rag_messages = messages

    # return 'sample text'

    return call_llm(rag_messages)


def get_embedding_function() -> ONNXMiniLM_L6_V2:
    return ONNXMiniLM_L6_V2(preferred_providers=EMBEDDING_PROVIDERS)

def query_vector_db(query: str, collection_name: str, top_k: int = RETRIEVAL_TOP_K) -> List[str]:
    # 1. Embed
    ef = get_embedding_function()
    query_embedding = ef([query])[0]

    # 2. Retrieve
    client     = PersistentClient(path=str(Settings.db_path))
    collection = client.get_collection(name=collection_name)
    results    = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    # 3. Return just the text chunks
    return results["documents"][0]


# ─── Prompt Construction ──────────────────────────────────────────────────────

def build_rag_prompt(user_message: str, contexts: List[str]) -> str:
    prompt_lines = [
        "Here is the context that can help you. If it's not useful, ignore it.",
        "\n--- CONTEXT ---"
    ]
    for i, ctx in enumerate(contexts, start=1):
        prompt_lines.append(f"\n[{i}]\n{ctx}")
    prompt_lines.append("\n--- QUERY ---")
    prompt_lines.append(user_message)
    return "\n\n".join(prompt_lines)


# ─── LLM Interaction ──────────────────────────────────────────────────────────

def call_llm(
    messages: List[dict[str, str]],
    # model: str = "fusechat-gemma-2-9b-instruct",
    model:str = "gpt-4.1-mini",
    temperature: float = 0.0,
    max_tokens: int = 512
) -> str:
    client = OpenAI(
        # base_url="http://localhost:1234/v1",
        # api_key="lm-studio"
        api_key="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"
    )
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()


def extract_text_from_pdf(pdf_path: str) -> str:
    doc = pymupdf.open(pdf_path)
    return "\n".join(page.get_text("text") or "" for page in doc)


def split_text_into_chunks(
    text: str, chunk_size: int = 1000, overlap: int = 200
) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=overlap
    )
    return splitter.split_text(text)


def compute_onnx_embeddings(
    texts: List[str],
    providers: List[str] = None,
) -> List[List[float]]:
    """
    Compute embeddings for a list of texts using ONNX MiniLM-L6-v2.
    """
    providers = providers or ["CPUExecutionProvider"]
    ef = ONNXMiniLM_L6_V2(preferred_providers=providers)
    return ef(texts)


def store_chunks_with_precomputed_embeddings(
    chunks: List[str],
    embeddings: List[List[float]],
    file_name: str,
    collection_name: str,
    db_path: str,
):
    """
    Store chunks plus their precomputed embeddings into ChromaDB.
    """
    client = PersistentClient(path=db_path)
    # No embedding_function here—just grab or create the collection
    collection = client.get_or_create_collection(name=collection_name)

    ids = [f"{file_name}_chunk_{i}" for i in range(len(chunks))]
    collection.add(documents=chunks, ids=ids, embeddings=embeddings)
    print(f"✔ Stored {len(chunks)} chunks + embeddings into '{collection_name}'")


def save_pdf_to_db(pdf_path, file_name, collection_name):

    # 1. Extract
    text = extract_text_from_pdf(pdf_path)
    print(f"Extracted {len(text)} characters")

    # 2. Chunk
    chunks = split_text_into_chunks(text, chunk_size=1000, overlap=200)
    print(f"Split into {len(chunks)} chunks")

    # 3. Compute embeddings
    embeddings = compute_onnx_embeddings(chunks)
    print(f"Computed {len(embeddings)} embeddings")

    # 4. Store
    store_chunks_with_precomputed_embeddings(
        chunks, embeddings, file_name=file_name, collection_name=collection_name, db_path=str(Settings.db_path)
    )

