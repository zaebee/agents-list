import os
import json
import faiss
import numpy as np
import argparse
import anthropic
from sentence_transformers import SentenceTransformer

# --- Configuration ---
# Correct the path to be relative to this file's location
RAG_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(RAG_DIR, "index.faiss")
CHUNKS_PATH = os.path.join(RAG_DIR, "chunks.json")
MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 5


def load_rag_data():
    """Loads the FAISS index and the text chunks."""
    if not os.path.exists(INDEX_PATH) or not os.path.exists(CHUNKS_PATH):
        return None, None
    index = faiss.read_index(INDEX_PATH)
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return index, data["chunks"]


def retrieve_chunks(query, model, index, chunks, k):
    """Retrieves the top-k most relevant chunks for a query."""
    query_embedding = model.encode([query])
    query_embedding = np.array(query_embedding, dtype="float32")
    _, indices = index.search(query_embedding, k)
    return [chunks[i] for i in indices[0]]


def generate_answer(query, retrieved_chunks):
    """
    Generates an answer using the Anthropic Claude model.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "Error: ANTHROPIC_API_KEY environment variable not set."
    try:
        client = anthropic.Anthropic(api_key=api_key)
        context = "\n\n".join(retrieved_chunks)
        prompt = (
            "You are a helpful AI assistant for the 'our-crm-ai' project. "
            "Your task is to answer questions about the project based on the "
            "provided context.\n\n"
            f"Here is the user's question:\n{query}\n\n"
            "Here is the relevant context from the project's documentation and code:\n"
            f"{context}\n\n"
            "Please provide a clear and concise answer to the question based "
            "only on the provided context.\n"
        )
        message = (
            client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            .content[0]
            .text
        )
        return message
    except Exception as e:
        return f"Error calling Anthropic API: {e}"


def query_rag(query_string):
    """
    Main entry point for the RAG system as a library.
    """
    print("Loading RAG data...")
    index, chunks = load_rag_data()
    if index is None:
        return "Error: RAG data not found. Please run prepare_rag.py first."

    print(f"Loading sentence transformer model '{MODEL_NAME}'...")
    model = SentenceTransformer(MODEL_NAME)

    print(f"Retrieving chunks for query: '{query_string}'")
    retrieved_chunks = retrieve_chunks(query_string, model, index, chunks, TOP_K)

    print("Generating answer...")
    final_answer = generate_answer(query_string, retrieved_chunks)

    return final_answer


def main():
    """Main function for the query engine CLI."""
    parser = argparse.ArgumentParser(
        description="Query the RAG system to get information about the project."
    )
    parser.add_argument(
        "query", type=str, help="The question you want to ask about the project."
    )
    args = parser.parse_args()

    result = query_rag(args.query)

    print("\n--- Generated Answer ---")
    print(result)


if __name__ == "__main__":
    main()
