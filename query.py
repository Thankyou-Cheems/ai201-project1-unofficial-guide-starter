import os
import chromadb
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer

# Load environment variables (.env)
load_dotenv()

CHROMA_DIR = os.path.join("data", "chroma")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set. Please check your .env file.")

# Initialize embedding model and persistent Chroma client
print("Loading sentence-transformers model (all-MiniLM-L6-v2)...")
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

print(f"Connecting to Chroma database at {CHROMA_DIR}...")
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = chroma_client.get_collection(name="columbia_dining")

# Initialize Groq client
print("Initializing Groq API client...")
groq_client = Groq(api_key=GROQ_API_KEY)

def ask(question, top_k=5):
    # 1. Embed the query
    query_embedding = embed_model.encode(question).tolist()
    
    # 2. Retrieve top-k chunks from ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas"]
    )
    
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    
    # 3. Format the context for the LLM
    context_blocks = []
    for doc, meta in zip(documents, metadatas):
        context_blocks.append(f"[Source ID: {meta['source_id']} | Title: {meta['title']}]\n{doc}")
    context = "\n\n".join(context_blocks)
    
    # 4. Formulate the system prompt instructing strict grounding
    system_prompt = (
        "You are an assistant for Columbia University Graduate Dining and Meal Plans.\n"
        "Your goal is to answer the user's question using ONLY the provided document context below.\n\n"
        "RULES:\n"
        "1. Base your answer strictly and only on the provided context. Do NOT use any general external knowledge.\n"
        "2. If the context does not contain enough information to fully answer the question, or if the question is "
        "completely out-of-scope, you MUST respond exactly with: 'I don't have enough information on that.'\n"
        "3. Cite the Source ID (e.g., [S6_grad_plans]) for each major claim you make. Do not create fake citations.\n"
        "4. Be objective, concise, and helpful to graduate students."
    )
    
    user_prompt = f"Context:\n{context}\n\nQuestion: {question}"
    
    # 5. Call Llama 3.3 70B model on Groq
    completion = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0, # Greedy decoding for maximum factual accuracy / grounding
        max_tokens=1024
    )
    
    answer = completion.choices[0].message.content
    
    # Extract list of unique source titles cited or retrieved
    retrieved_sources = []
    for meta in metadatas:
        source_info = f"{meta['title']} ({meta['source_id']})"
        if source_info not in retrieved_sources:
            retrieved_sources.append(source_info)
            
    return {
        "answer": answer,
        "sources": retrieved_sources
    }

if __name__ == "__main__":
    # Test execution
    test_q = "What are the graduate meal plans and how much do they cost?"
    print(f"\nTesting RAG query: '{test_q}'")
    res = ask(test_q)
    print("\nANSWER:")
    print(res["answer"])
    print("\nSOURCES RETRIEVED:")
    for src in res["sources"]:
        print(f"- {src}")
