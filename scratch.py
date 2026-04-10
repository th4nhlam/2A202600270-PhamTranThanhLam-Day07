from src.store import compute_similarity
from src.embeddings import LocalEmbedder

embedder = LocalEmbedder()
sentences = [
    ("The seller pays for sea freight under CIF.", "Under CIF terms, the seller is responsible for the cost of ocean transport."),
    ("EXW means the buyer handles all transport.", "DDP requires the seller to handle all logistics and duties."),
    ("Incoterms 2020 are published by the ICC.", "International Chamber of Commerce created the Incoterms rules."),
    ("The risk transfers to the buyer when goods are loaded on the ship in FOB.", "What is the capital of France?"),
    ("FCA can be used for any mode of transport.", "FOB is strictly for sea or inland waterway transport.")
]

embeddings1 = embedder([s[0] for s in sentences])
embeddings2 = embedder([s[1] for s in sentences])

for i, (s1, s2) in enumerate(sentences):
    score = compute_similarity(embeddings1[i], embeddings2[i])
    print(f"{i+1}: {score:.4f}")

