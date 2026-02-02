from smolagents import tool
from typing import List, Dict

_vector_store = None


def get_vector_store():
    global _vector_store
    if _vector_store is None:
        raise RuntimeError("Ошибка: база знаний не инициализирована.")
    return _vector_store


@tool
def retrieve_knowledge(query: str, top_k: int = 6) -> str:
    """
    Ищет релевантные фрагменты из базы знаний техподдержки.

    Args:
        query (str): Поисковый запрос.
        top_k (int): Количество возвращаемых фрагментов (по умолчанию 6).

    Returns:
        str: Найденные фрагменты или сообщение об ошибке.
    """
    try:
        vector_store = get_vector_store()
        results: List[Dict] = vector_store.similarity_search(query, k=top_k)

        if not results:
            return "В базе знаний не найдено релевантной информации по вашему запросу."

        formatted = []
        for i, res in enumerate(results, 1):
            source = res["metadata"].get("source", "неизвестно")
            text = res["text"].strip()
            formatted.append(f"[Источник: {source}]\n{text}")

        return "\n\n".join(formatted)

    except Exception as e:
        return f"Ошибка при поиске в базе знаний: {str(e)}"


def set_vector_store(store):
    global _vector_store
    _vector_store = store
