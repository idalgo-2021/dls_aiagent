from pathlib import Path
from knowledge_base.vector_store.chroma_repo import ChromaVectorStore


def load_documents_from_folder(folder: str = "knowledge_base/raw"):
    chunks = []
    metadatas = []
    ids = []

    folder_path = Path(folder)
    if not folder_path.exists():
        print(f"Каталог '{folder}' не существует. Создайте его её и добавьте .md файлы.")
        return chunks, metadatas, ids

    for file_path in folder_path.rglob("*.md"):
        text = file_path.read_text(encoding="utf-8")

        # Чанкирование по заголовкам и абзацам(для md)
        lines = text.split('\n')
        current_chunk = []
        current_header = file_path.name

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                # Новый раздел — сохраняем предыдущий чанк
                if current_chunk:
                    chunks.append('\n'.join(current_chunk).strip())
                    metadatas.append({"source": file_path.name, "header": current_header})
                    ids.append(f"{file_path.stem}_{len(chunks)}")
                current_chunk = [line]
                current_header = stripped
            else:
                current_chunk.append(line)

        # Последний чанк
        if current_chunk:
            chunks.append('\n'.join(current_chunk).strip())
            metadatas.append({"source": file_path.name, "header": current_header})
            ids.append(f"{file_path.stem}_{len(chunks)}")

    return chunks, metadatas, ids


if __name__ == "__main__":
    print("Перестраиваю базу знаний...")

    store = ChromaVectorStore()

    chunks, metadatas, ids = load_documents_from_folder()

    if not chunks:
        print(
            "Нет документов в knowledge_base/raw/. Добавь хотя бы один файл с текстом."
        )
    else:
        store.add_documents(chunks, metadatas, ids)
        print(f"Успешно добавлено {len(chunks)} чанков в базу знаний.")
        print("Готово! Теперь запускай: python3 main.py")
