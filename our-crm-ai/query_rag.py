import os
import json
import faiss
import numpy as np
import argparse
import anthropic
from sentence_transformers import SentenceTransformer

# --- Configuration ---
DOCS_DIR = os.path.join(os.path.dirname(__file__), "rag")
INDEX_PATH = os.path.join(DOCS_DIR, "index.faiss")
CHUNKS_PATH = os.path.join(DOCS_DIR, "chunks.json")
MODEL_NAME = 'all-MiniLM-L6-v2'
TOP_K = 5  # Number of relevant chunks to retrieve

def load_rag_data():
    """Loads the FAISS index and the text chunks."""
    print("Loading RAG data...")
    if not os.path.exists(INDEX_PATH) or not os.path.exists(CHUNKS_PATH):
        print("Error: Index or chunks file not found.")
        print(f"Please run 'python3 our-crm-ai/rag/prepare_rag.py' first.")
        return None, None

    index = faiss.read_index(INDEX_PATH)
    with open(CHUNKS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return index, data['chunks']

def retrieve_chunks(query, model, index, chunks, k):
    """Retrieves the top-k most relevant chunks for a query."""
    print(f"Embedding query: '{query}'")
    query_embedding = model.encode([query])
    query_embedding = np.array(query_embedding, dtype='float32')

    print(f"Searching for top {k} relevant chunks...")
    distances, indices = index.search(query_embedding, k)

    retrieved_chunks = [chunks[i] for i in indices[0]]
    return retrieved_chunks

def generate_answer(query, retrieved_chunks):
    """
    Generates an answer using the Anthropic Claude model.
    """
    print("Generating answer with Claude...")

    # Get API key from environment
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "Error: ANTHROPIC_API_KEY environment variable not set."

    try:
        client = anthropic.Anthropic(api_key=api_key)

        context = "\n\n".join(retrieved_chunks)

        prompt = f"""You are a helpful AI assistant for the 'our-crm-ai' project. Your task is to answer questions about the project based on the provided context.

Here is the user's question:
{query}

Here is the relevant context from the project's documentation and code:
{context}

Please provide a clear and concise answer to the question based only on the provided context.
"""

        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        ).content[0].text

        return message
    except Exception as e:
        return f"Error calling Anthropic API: {e}"

def main():
    """
    Main function for the query engine CLI.
    """
    parser = argparse.ArgumentParser(description="Query the RAG system to get information about the project.")
    parser.add_argument("query", type=str, help="The question you want to ask about the project.")
    args = parser.parse_args()

    # Load RAG data
    index, chunks = load_rag_data()
    if index is None:
        return

    # Load the sentence transformer model
    print(f"Loading sentence transformer model '{MODEL_NAME}'...")
    model = SentenceTransformer(MODEL_NAME)

    # Retrieve relevant chunks
    retrieved_chunks = retrieve_chunks(args.query, model, index, chunks, TOP_K)

    # Generate an answer
    final_answer = generate_answer(args.query, retrieved_chunks)

    # Print the result
    print("\n--- Generated Answer ---")
    print(final_answer)


if __name__ == "__main__":
    main()
