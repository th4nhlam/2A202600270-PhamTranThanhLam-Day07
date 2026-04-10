import os
from src.embeddings import LocalEmbedder
from src.store import compute_similarity, EmbeddingStore
from src.models import Document
from main import load_documents_from_files, SAMPLE_FILES
from src.agent import KnowledgeBaseAgent

def demo_llm(prompt: str) -> str:
    preview = prompt[:100].replace("\n", " ")
    return f"[DEMO LLM] Answer based on context."

def part5():
    embedder = LocalEmbedder()
    pairs = [
        ("The seller pays for sea freight under CIF.", "Under CIF terms, the seller is responsible for the cost of ocean transport.", "high"),
        ("EXW means the buyer handles all transport.", "DDP requires the seller to handle all logistics and duties.", "low"),
        ("Incoterms 2020 are published by the ICC.", "International Chamber of Commerce created the Incoterms rules.", "high"),
        ("The risk transfers to the buyer when goods are loaded on the ship in FOB.", "What is the capital of France?", "low"),
        ("FCA can be used for any mode of transport.", "FOB is strictly for sea or inland waterway transport.", "low")
    ]
    
    print("=== PART 5: Similarity Predictions ===")
    for a, b, pred in pairs:
        emb_a = embedder(a)
        emb_b = embedder(b)
        score = compute_similarity(emb_a, emb_b)
        print(f"A: {a}\nB: {b}\nPred: {pred} | Score: {score:.4f}\n")

def part6():
    print("=== PART 6: Results ===")
    embedder = LocalEmbedder()
    store = EmbeddingStore(collection_name="manual_test_store_2", embedding_fn=embedder)
    docs = load_documents_from_files(SAMPLE_FILES)
    store.add_documents(docs)
    agent = KnowledgeBaseAgent(store, demo_llm)
    
    queries = [
        "What are the obligations of the seller under EXW?",
        "Does CIF apply to air transport?",
        "Who is responsible for unloading goods at the destination under DPU?",
        "At what point does risk transfer from seller to buyer in FOB?",
        "Are Incoterms legally binding contracts on their own?"
    ]
    
    for q in queries:
        print(f"\nQuery: {q}")
        res = store.search(q, top_k=1)
        if res:
            print(f"Top Chunk: {res[0]['content'][:100]}...")
            print(f"Score: {res[0]['score']:.4f}")
        else:
            print("Top Chunk: None")
            print("Score: 0.0")
        ans = agent.answer(q, top_k=3)
        print(f"Agent: {ans[:100]}")

if __name__ == '__main__':
    part5()
    part6()
