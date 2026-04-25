import asyncio
from langchain_ollama import ChatOllama

async def test():
    try:
        print("Connecting to Ollama at 127.0.0.1...")
        llm = ChatOllama(model="qwen2.5:3b", base_url="http://127.0.0.1:11434")
        response = await llm.ainvoke("Hello")
        print("Response:", response.content)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test())
