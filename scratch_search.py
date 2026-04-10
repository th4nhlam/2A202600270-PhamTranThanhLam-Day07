from src.store import EmbeddingStore
from src.embeddings import LocalEmbedder
from src.agent import KnowledgeBaseAgent
from main import load_documents_from_files, SAMPLE_FILES, demo_llm
import sys

docs = load_documents_from_files(SAMPLE_FILES)
embedder = LocalEmbedder()
store = EmbeddingStore("test_collection", embedder)
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
    results = store.search(q, top_k=1)
    if results:
        print(f"Top chunk: {results[0]['metadata']['source']} - score: {results[0]['score']:.4f}")
        print(f"Content preview: {results[0]['content'][:100]}...")
    else:
        print("No chunks found.")
    
    ans = agent.answer(q)
    print(f"Agent Ans: {ans}")
