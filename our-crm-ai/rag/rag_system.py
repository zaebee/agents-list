import os
import json
import numpy as np
import faiss
import re
import argparse
from sentence_transformers import SentenceTransformer
import sys

# Add project root to path to allow sibling imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import download_file

# --- Configuration ---
ROOT_DIR = "/app"
RAG_DIR = os.path.dirname(os.path.abspath(__file__))
ATTACHMENTS_DIR = os.path.join(RAG_DIR, "attachments")
INDEX_PATH = os.path.join(RAG_DIR, "index.faiss")
CHUNKS_PATH = os.path.join(RAG_DIR, "chunks.json")
MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TEXT_EXTENSIONS = [".md", ".py", ".txt", ".json"]
TOP_K = 5

# --- Data Preparation Functions ---


def find_local_files(start_path, extensions):
    """Finds all local files with given extensions in a directory tree."""
    file_paths = []
    for root, _, files in os.walk(start_path):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                if RAG_DIR in os.path.join(root, file):
                    continue
                file_paths.append(os.path.join(root, file))
    return file_paths


def find_attached_files(client):
    """Finds and downloads text file attachments from all tasks."""
    print("Searching for attached text files in CRM tasks...")
    attached_files = []
    tasks = client.list_tasks()
    attachment_regex = re.compile(r"\[(.*?)\]\((https?://.*?)\)")
    for task_summary in tasks:
        task_details = client.view_task(task_summary["id"])
        if not task_details or not task_details.get("comments"):
            continue
        for comment in task_details["comments"]:
            text = comment.get("text", "")
            matches = attachment_regex.findall(text)
            for filename, url in matches:
                if any(filename.endswith(ext) for ext in TEXT_EXTENSIONS):
                    downloaded_path = download_file(
                        url, ATTACHMENTS_DIR, client.api_key
                    )
                    if downloaded_path:
                        attached_files.append(downloaded_path)
    return attached_files


def chunk_text(text, size, overlap):
    """Splits text into overlapping chunks."""
    chunks = []
    for i in range(0, len(text), size - overlap):
        chunks.append(text[i : i + size])
    return chunks


def prepare_data():
    """Main function to prepare the RAG data."""
    print("Starting RAG data preparation...")
    os.makedirs(RAG_DIR, exist_ok=True)
    os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

    print(f"Searching for local files in {ROOT_DIR}...")
    files_to_index = find_local_files(ROOT_DIR, TEXT_EXTENSIONS)
    print(f"Found {len(files_to_index)} local files.")

    # NOTE: Skipping attachment download due to 404 issue.
    # try:
    #     client = CRMClient()
    #     attached_files = find_attached_files(client)
    #     files_to_index.extend(attached_files)
    #     print(f"Found and downloaded {len(attached_files)} attached files.")
    # except Exception as e:
    #     print(f"Could not connect to CRM to fetch attachments: {e}")

    if not files_to_index:
        print("No documents found to index. Exiting.")
        return

    all_chunks, chunk_metadata = [], []
    for file_path in files_to_index:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            chunks = chunk_text(content, CHUNK_SIZE, CHUNK_OVERLAP)
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                chunk_metadata.append({"source": file_path, "chunk_index": i})
        except Exception as e:
            print(f"Could not read or chunk file {file_path}: {e}")

    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(all_chunks, show_progress_bar=True)
    embeddings = np.array(embeddings, dtype="float32")

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    faiss.write_index(index, INDEX_PATH)
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump({"chunks": all_chunks, "metadata": chunk_metadata}, f, indent=4)
    print("\nData preparation complete!")


# --- Query Functions ---


def load_rag_data():
    """Loads the FAISS index and the text chunks."""
    if not os.path.exists(INDEX_PATH) or not os.path.exists(CHUNKS_PATH):
        return None, None
    index = faiss.read_index(INDEX_PATH)
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return index, data["chunks"]


def query_rag(query_string):
    """Main entry point for querying the RAG system."""
    index, chunks = load_rag_data()
    if index is None:
        return "Error: RAG data not found. Please run `prepare` command first."

    model = SentenceTransformer(MODEL_NAME)
    query_embedding = model.encode([query_string])
    query_embedding = np.array(query_embedding, dtype="float32")
    _, indices = index.search(query_embedding, TOP_K)
    retrieved_chunks = [chunks[i] for i in indices[0]]

    # For now, just return the retrieved chunks without LLM call
    response = f"--- Top {TOP_K} relevant chunks for '{query_string}' ---\n\n"
    for i, chunk in enumerate(retrieved_chunks):
        response += f"--- Chunk {i + 1} ---\n{chunk}\n\n"
    return response


# --- Main CLI Handler ---


def main():
    parser = argparse.ArgumentParser(description="RAG System for our-crm-ai.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("prepare", help="Build the RAG index.")
    query_parser = subparsers.add_parser("query", help="Query the RAG system.")
    query_parser.add_argument("query_string", type=str, help="The question to ask.")

    args = parser.parse_args()

    if args.command == "prepare":
        prepare_data()
    elif args.command == "query":
        result = query_rag(args.query_string)
        print(result)


if __name__ == "__main__":
    main()
