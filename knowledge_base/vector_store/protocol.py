from typing import Protocol, List, Dict, Optional


class VectorStoreRepository(Protocol):
    def add_documents(
        self,
        chunks: List[str],
        metadatas: List[Dict],
        ids: Optional[List[str]] = None,
    ) -> None: ...

    def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter: Optional[Dict] = None,
    ) -> List[Dict]: ...

    def delete_collection(self) -> None: ...
