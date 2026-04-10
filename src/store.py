from __future__ import annotations

from typing import Any, Callable

#from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document
from .chunking import compute_similarity

class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            # TODO: initialize chromadb client + collection
            self._client = chromadb.Client()
            try:
                self._client.delete_collection(self._collection_name)
            except ValueError:
                pass
            self._collection = self._client.get_or_create_collection(self._collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        # TODO: build a normalized stored record for one document
        embedding = self._embedding_fn(doc.content)
        metadata = dict(doc.metadata) if doc.metadata else {}
        metadata["doc_id"] = doc.id
        return {
            "id": doc.id,
            "content": doc.content,
            "embedding": embedding,
            "metadata": metadata,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        # TODO: run in-memory similarity search over provided records
        query_embedding = self._embedding_fn(query)
        results = []
        for record in records:
            similarity = compute_similarity(query_embedding, record["embedding"])
            r = dict(record)
            r["score"] = similarity
            results.append(r)
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        # TODO: embed each doc and add to store
        if self._use_chroma:
            metadatas = []
            for doc in docs:
                m = dict(doc.metadata) if doc.metadata else {}
                m["doc_id"] = doc.id
                metadatas.append(m)
            self._collection.add(
                ids=[doc.id for doc in docs],
                documents=[doc.content for doc in docs],
                embeddings=[self._embedding_fn(doc.content) for doc in docs],
                metadatas=metadatas
            )
        else:
            self._store.extend([self._make_record(doc) for doc in docs])

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        # TODO: embed query, compute similarities, return top_k
        if self._use_chroma:
            results = self._collection.query(
                query_embeddings=[self._embedding_fn(query)],
                n_results=top_k,
                include=["documents", "metadatas", "embeddings", "distances"]
            )
            out = []
            count = len(results["ids"][0]) if results["ids"] else 0
            for i in range(count):
                out.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "embedding": results["embeddings"][0][i] if results.get("embeddings") and results["embeddings"][0] else None,
                    "metadata": results["metadatas"][0][i],
                    "score": 1.0 - results["distances"][0][i] if results.get("distances") and results["distances"][0] else 0.0,
                })
            return out
        else:
            return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        # TODO
        if self._use_chroma:
            return self._collection.count()
        else:
            return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        # TODO: filter by metadata, then search among filtered chunks
        if self._use_chroma:
            kwargs = {
                "query_embeddings": [self._embedding_fn(query)],
                "n_results": top_k,
                "include": ["documents", "metadatas", "embeddings", "distances"]
            }
            if metadata_filter:
                kwargs["where"] = metadata_filter
                
            results = self._collection.query(**kwargs)
            out = []
            count = len(results["ids"][0]) if results["ids"] else 0
            for i in range(count):
                out.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "embedding": results["embeddings"][0][i] if results.get("embeddings") and results["embeddings"][0] else None,
                    "metadata": results["metadatas"][0][i],
                    "score": 1.0 - results["distances"][0][i] if results.get("distances") and results["distances"][0] else 0.0,
                })
            return out
        else:
            filtered_records = self._store
            if metadata_filter:
                filtered_records = [
                    record for record in self._store
                    if all(record["metadata"].get(k) == v for k, v in metadata_filter.items())
                ]
            return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        # TODO: remove all stored chunks where metadata['doc_id'] == doc_id
        if self._use_chroma:
            count_before = self._collection.count()
            self._collection.delete(where={"doc_id": doc_id})
            return self._collection.count() < count_before
        else:
            old_len = len(self._store)
            self._store = [record for record in self._store if record["metadata"].get("doc_id") != doc_id]
            return len(self._store) < old_len
