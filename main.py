import os
from dotenv import load_dotenv
from config import config
from knowledge_base.vector_store.chroma_repo import ChromaVectorStore
from smolagents import OpenAIModel, ToolCallingAgent, DuckDuckGoSearchTool
from tools.rag_tool import retrieve_knowledge
from tools.rag_tool import set_vector_store
from tools.product_db_tool import search_models, get_stock_and_price, get_model_details
from tools.order_tool import create_order_request

load_dotenv()

llm_config = config["llm"]
model = OpenAIModel(
    model_id=llm_config["model_id"],
    api_base=llm_config["api_base"],
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=llm_config.get("temperature", 0.7),
    # max_output_tokens=llm_config.get("max_tokens"),  # не для всех моделей
    # max_tokens=llm_config.get("max_tokens", 1024),
)


system_prompt = config["system_prompt"]

web_search_tool = DuckDuckGoSearchTool(max_results=5)

agent = ToolCallingAgent(
    tools=[
        # -- RAG
        retrieve_knowledge,
        #
        # -- запросы к БД
        search_models,
        get_stock_and_price,
        get_model_details,
        create_order_request,
        #
        # -- ВЕБ-поиск
        web_search_tool,
    ],
    model=model,
)

vector_store_instance = ChromaVectorStore()
set_vector_store(vector_store_instance)

# Экспортируем для импорта
__all__ = ["agent", "config"]

if __name__ == "__main__":

    print(
        "Агент поддержки Интернет-магазина кроссовок SneakerHub запущен! Задавай вопросы (или 'exit' для выхода).\n"
    )

    history = []

    while True:
        user_input = input("Вы: ").strip()
        if user_input.lower() in ["exit", "quit", "выход"]:
            print("До свидания!")
            break
        if not user_input:
            continue

        history.append({"role": "user", "content": user_input})

        full_context = config["system_prompt"] + "\n\nИстория диалога:\n"
        for msg in history:
            role = "Пользователь" if msg["role"] == "user" else "Агент"
            full_context += f"{role}: {msg['content']}\n"

        try:
            response = agent.run(full_context, max_steps=4)
            print(f"\nАгент: {response}\n")
            history.append({"role": "assistant", "content": response})
        except Exception as e:
            print(f"Ошибка: {e}")

        # Ограничиваем длину истории
        if len(history) > 20:
            history = history[-20:]
