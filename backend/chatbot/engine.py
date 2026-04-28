import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate

# Config
DB_FAISS_PATH = os.path.join(os.path.dirname(__file__), "local_db", "vectorstore")

# System Prompt
RAG_PROMPT_TEMPLATE = """You are the VeritAI Assistant. Answer the user's question using ONLY the provided context.
If the answer is not in the context, say you only know about VeritAI's features and capabilities.
Be concise (max 3 sentences).

Context:
{context}

Question: {question}

Helpful Answer:"""

ARTICLE_PROMPT_TEMPLATE = """You are the VeritAI Article Assistant. You are analyzing a specific article.
Answer the user's question about the article using ONLY the provided article context and analysis details.
If the answer is not in the article or analysis, say you don't know based on the provided information.
Be concise and helpful.

Article & Analysis Context:
{context}

Question: {question}

Helpful Answer:"""

# Globals to cache embeddings and vector store
_embeddings = None
_vector_store = None

def load_llm():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY not set in environment.")
    return ChatGoogleGenerativeAI(
        model=os.getenv("LLM_MODEL", "gemini-2.5-flash"),
        google_api_key=api_key,
        temperature=0.2,
    )

def get_vector_store():
    global _embeddings, _vector_store
    if not os.path.exists(DB_FAISS_PATH):
        return None
    
    if _vector_store is None:
        print("[chatbot] Initializing vector store...")
        if _embeddings is None:
            _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        _vector_store = FAISS.load_local(DB_FAISS_PATH, _embeddings, allow_dangerous_deserialization=True)
    return _vector_store

async def get_chatbot_response(query: str, article_context: str = ""):
    if article_context:
        try:
            llm = load_llm()
            prompt = ARTICLE_PROMPT_TEMPLATE.format(context=article_context, question=query)
            response = await llm.ainvoke(prompt)
            return response.content
        except Exception as e:
            print(f"[chatbot] Error in engine with article: {e}")
            return "I'm having trouble analyzing this article right now. Please check if GEMINI_API_KEY is set correctly."
            
    db = get_vector_store()
    if db is None:
        return "System error: Vector database not initialized. Please run ingest.py first."

    try:
        # 1. Search for relevant context (top 3)
        docs = db.similarity_search(query, k=3)
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # 2. Prepare Prompt
        llm = load_llm()
        prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=query)
        
        # 3. Get response from Gemini
        response = await llm.ainvoke(prompt)
        return response.content
    except Exception as e:
        print(f"[chatbot] Error in engine: {e}")
        return "I'm having trouble accessing my knowledge base right now. Please check if GEMINI_API_KEY is set correctly."
