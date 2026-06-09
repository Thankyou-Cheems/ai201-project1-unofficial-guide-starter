import os
import json
import re
import chromadb
from sentence_transformers import SentenceTransformer

PROCESSED_DIR = os.path.join("data", "processed")
CHROMA_DIR = os.path.join("data", "chroma")

def chunk_reddit(text):
    # Split Reddit threads by posts/comments
    # Split on lines starting with OP or Comment
    pattern = r'(?=\bOP \([^)]+\):|\bComment \d+ \([^)]+\):)'
    parts = re.split(pattern, text)
    chunks = []
    current_chunk = ""
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # If it's a header comment, add it
        chunks.append(part)
    return chunks

def chunk_engineering_dining(text):
    # Split on lines starting with a number like "1. ", "2. "
    pattern = r'(?=\n\d+\.\s+|\b\d+\.\s+)'
    parts = re.split(pattern, text)
    chunks = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        chunks.append(part)
    return chunks

def chunk_wikicu_services(text):
    # Split on list items starting with "- "
    pattern = r'(?=\n-\s+|\b-\s+)'
    parts = re.split(pattern, text)
    chunks = []
    header = ""
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if part.startswith("Dining Halls:") or part.startswith("Retail:"):
            # This is a header, prepend it or store it
            header = part.split("\n")[0]
            # Get rest of text
            subparts = part.split("\n")[1:]
            for sub in subparts:
                sub = sub.strip()
                if sub.startswith("-"):
                    chunks.append(f"{header}\n{sub}")
        elif part.startswith("-"):
            chunks.append(f"{header}\n{part}" if header else part)
        else:
            chunks.append(part)
    return chunks

def chunk_paragraphs(text, max_chars=1200, overlap=150):
    # Standard paragraph chunker
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # If paragraph itself is too large, split it mechanically
        if len(para) > max_chars:
            # Save any accumulated chunk first
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            
            # Split paragraph into overlapping blocks
            start = 0
            while start < len(para):
                end = start + max_chars
                block = para[start:end]
                chunks.append(block)
                start += max_chars - overlap
        else:
            # Accumulate paragraphs until they reach a good size
            if len(current_chunk) + len(para) + 2 > max_chars:
                chunks.append(current_chunk)
                current_chunk = para
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
                    
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks

def chunk_document(doc):
    source_id = doc["source_id"]
    text = doc["text"]
    
    if source_id in ["S10_reddit_grad_policy", "S11_reddit_extra_meals", "S12_reddit_dining_halls"]:
        return chunk_reddit(text)
    elif source_id == "S4_engineering_dining":
        return chunk_engineering_dining(text)
    elif source_id == "S7_wikicu_dining_services":
        return chunk_wikicu_services(text)
    else:
        return chunk_paragraphs(text)

def index_all():
    print("Initializing embedding model (all-MiniLM-L6-v2)...")
    # Load model locally
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Setup Chroma client
    print(f"Initializing persistent Chroma client at {CHROMA_DIR}...")
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    # Get or create collection
    # Chroma default uses L2 distance; we can configure it if needed
    collection = client.get_or_create_collection(
        name="columbia_dining",
        metadata={"hnsw:space": "cosine"} # Use cosine distance for semantic search
    )
    
    # Clear existing documents in collection to avoid duplicates
    print("Clearing existing collection entries...")
    existing = collection.get()
    if existing and existing["ids"]:
        collection.delete(ids=existing["ids"])
        print(f"Deleted {len(existing['ids'])} existing chunks.")

    # Get list of processed files
    files = [f for f in os.listdir(PROCESSED_DIR) if f.endswith(".json")]
    print(f"Found {len(files)} processed JSON documents.")

    all_ids = []
    all_embeddings = []
    all_documents = []
    all_metadatas = []
    chunk_counter = 0

    for filename in files:
        filepath = os.path.join(PROCESSED_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            doc = json.load(f)
            
        chunks = chunk_document(doc)
        print(f"Document {doc['doc_id']} split into {len(chunks)} chunks.")
        
        for idx, chunk in enumerate(chunks):
            # Check length to avoid empty chunks
            chunk = chunk.strip()
            if not chunk:
                continue
                
            chunk_id = f"{doc['doc_id']}_c{idx}"
            
            # Format metadata
            metadata = {
                "source_id": doc["source_id"],
                "doc_id": doc["doc_id"],
                "url": doc["url"],
                "title": doc["title"],
                "type": doc["metadata"].get("type", "unknown"),
                "doc_type": doc["metadata"].get("doc_type", "unknown"),
                "audience": doc["metadata"].get("audience", "unknown"),
                "priority": doc["metadata"].get("priority", 3),
                "school": doc["metadata"].get("school", ""),
                "campus": doc["metadata"].get("campus", ""),
                "chunk_index": idx
            }
            
            all_ids.append(chunk_id)
            all_documents.append(chunk)
            all_metadatas.append(metadata)
            chunk_counter += 1

    print(f"\nGenerating embeddings for {chunk_counter} chunks...")
    # Generate embeddings in batch
    embeddings = model.encode(all_documents, show_progress_bar=True)
    all_embeddings = [emb.tolist() for emb in embeddings]

    # Batch add to Chroma (max batch size in Chroma is typically 5000, we have ~100-200 chunks)
    print("Adding chunks and embeddings to Chroma database...")
    collection.add(
        ids=all_ids,
        embeddings=all_embeddings,
        documents=all_documents,
        metadatas=all_metadatas
    )

    print(f"\nSuccessfully indexed {chunk_counter} chunks in Chroma vector store.")
    print("Vector database is persisted in: data/chroma/")

if __name__ == "__main__":
    index_all()
