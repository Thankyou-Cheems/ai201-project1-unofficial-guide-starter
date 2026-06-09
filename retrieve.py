import os
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DIR = os.path.join("data", "chroma")

TEST_QUERIES = [
    "What are the graduate meal plans and how much do they cost?",
    "Where can I use graduate meal plan swipes on campus?",
    "Can I eat at John Jay, Ferris Booth Commons, or JJ's Place with a graduate plan?",
    "What happens if I run out of meals before the end of the term? Can I add more?",
    "What are the best dining options near Mudd for engineering students?"
]

def test_retrieval():
    print(f"Loading persistent Chroma vector store from {CHROMA_DIR}...")
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    try:
        collection = client.get_collection(name="columbia_dining")
        print("Successfully loaded collection 'columbia_dining'.")
    except Exception as e:
        print(f"Error: Collection 'columbia_dining' not found. Please run 'python index.py' first. Details: {e}")
        return

    print("Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    for i, query in enumerate(TEST_QUERIES):
        print("\n" + "="*80)
        print(f"QUERY {i+1}: '{query}'")
        print("="*80)

        # Generate query embedding
        query_embedding = model.encode(query).tolist()

        # Query vector database
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3, # Retrieve top 3
            include=["documents", "metadatas", "distances"]
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        print(f"Retrieved {len(documents)} matching chunks:")
        for idx, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
            print(f"\n  [{idx+1}] Chunk ID: {results['ids'][0][idx]}  |  Distance (Cosine): {dist:.4f}")
            print(f"      Source: {meta['title']} ({meta['source_id']})")
            print(f"      URL: {meta['url']}")
            print(f"      Audience: {meta['audience']}  |  Doc Type: {meta['doc_type']}")
            # Truncate text for cleaner display
            snippet = doc.replace("\n", " ")
            if len(snippet) > 250:
                snippet = snippet[:250] + "..."
            print(f"      Text: \"{snippet}\"")

if __name__ == "__main__":
    test_retrieval()
