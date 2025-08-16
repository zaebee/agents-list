import json
import os

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# --- Configuration ---
ROOT_DIR = "/app"  # Start from the absolute root of the repository
DOCS_DIR = os.path.join(ROOT_DIR, "our-crm-ai", "rag")
INDEX_PATH = os.path.join(DOCS_DIR, "index.faiss")
CHUNKS_PATH = os.path.join(DOCS_DIR, "chunks.json")
MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE = 1000  # characters
CHUNK_OVERLAP = 200


def find_files(start_path, extensions):
    """Finds all files with given extensions in a directory tree."""
    file_paths = []
    for root, _, files in os.walk(start_path):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                # Exclude the RAG directory itself
                if os.path.join(root, file).startswith(DOCS_DIR):
                    continue
                file_paths.append(os.path.join(root, file))
    return file_paths


def chunk_text(text, size, overlap):
    """Splits text into overlapping chunks."""
    chunks = []
    for i in range(0, len(text), size - overlap):
        chunks.append(text[i : i + size])
    return chunks


def main():
    """
    Main function to prepare the RAG data:
    1. Find and load documents.
    2. Chunk the documents.
    3. Generate embeddings.
    4. Build and save a FAISS index.
    5. Save the chunks.
    """
    print("Starting RAG data preparation...")

    # Ensure the output directory exists
    os.makedirs(DOCS_DIR, exist_ok=True)

    # 1. Find and load documents
    print(f"Searching for .md and .py files in {ROOT_DIR}...")
    files_to_index = find_files(ROOT_DIR, [".md", ".py"])

    if not files_to_index:
        print("No documents found to index. Exiting.")
        return

    print(f"Found {len(files_to_index)} files to index.")

    all_chunks = []
    chunk_metadata = []

    # 2. Chunk the documents
    print("Chunking documents...")
    for file_path in files_to_index:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            chunks = chunk_text(content, CHUNK_SIZE, CHUNK_OVERLAP)
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                chunk_metadata.append({"source": file_path, "chunk_index": i})
        except Exception as e:
            print(f"Could not read or chunk file {file_path}: {e}")

    if not all_chunks:
        print("No text chunks were generated. Exiting.")
        return

    print(f"Generated {len(all_chunks)} chunks.")

    # 3. Generate embeddings
    print(f"Loading sentence transformer model '{MODEL_NAME}'...")
    model = SentenceTransformer(MODEL_NAME)

    print("Generating embeddings for all chunks...")
    embeddings = model.encode(all_chunks, show_progress_bar=True)
    embeddings = np.array(embeddings, dtype="float32")

    # 4. Build and save FAISS index
    print("Building FAISS index...")
    embedding_dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(embedding_dim)
    index.add(embeddings)

    print(f"Saving FAISS index to {INDEX_PATH}...")
    faiss.write_index(index, INDEX_PATH)

    # 5. Save the chunks and their metadata
    print(f"Saving text chunks and metadata to {CHUNKS_PATH}...")
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump({"chunks": all_chunks, "metadata": chunk_metadata}, f, indent=4)

    print("\nData preparation complete!")
    print(f"FAISS index saved at: {INDEX_PATH}")
    print(f"Text chunks saved at: {CHUNKS_PATH}")


if __name__ == "__main__":
    main()
