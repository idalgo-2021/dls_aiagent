from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from typing import List, Dict, Optional
from .protocol import VectorStoreRepository
from config import config


class ChromaVectorStore(VectorStoreRepository):
    def __init__(
        self,
        persist_dir: str = "knowledge_base/chroma_db",
        collection_name: str = "support_kb",
        # embedding_model: str = "all-MiniLM-L6-v2",
        # embedding_model: str = "intfloat/multilingual-e5-large-instruct",
        embedding_model: str = config["rag"]["embedding_model"],
    ):
        import chromadb  # локальный импорт, чтобы избежать F401 на верхнем уровне

        self.client = chromadb.PersistentClient(path=persist_dir)

        embedding_function = SentenceTransformerEmbeddingFunction(
            model_name=embedding_model,
            normalize_embeddings=True,
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function,
        )

    def add_documents(
        self,
        chunks: List[str],
        metadatas: List[Dict],
        ids: Optional[List[str]] = None,
    ):
        self.collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids or [f"chunk_{i}" for i in range(len(chunks))],
        )

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict] = None,
    ) -> List[Dict]:
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            where=filter,
            include=["documents", "metadatas", "distances"],
        )

        return [
            {
                "text": doc,
                "metadata": meta,
                "score": dist,
            }
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]

    def delete_collection(self):
        try:
            self.client.delete_collection(self.collection.name)
            print(f"Коллекция '{self.collection.name}' удалена.")
        except Exception:
            pass
