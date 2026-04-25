import os
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Config
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "project_info")
DB_FAISS_PATH = os.path.join(os.path.dirname(__file__), "local_db", "vectorstore")

def create_vector_db():
    print(f"[ingest] Loading documents from {DATA_PATH}...")
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)
        with open(os.path.join(DATA_PATH, "readme.txt"), "w") as f:
            f.write("VeritAI is an AI-powered fact-checking tool.")

    loader = DirectoryLoader(DATA_PATH, glob="*.md", loader_cls=TextLoader)
    documents = loader.load()
    
    if not documents:
        print("[ingest] No documents found to index.")
        return

    print(f"[ingest] Loaded {len(documents)} documents. Splitting into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts = text_splitter.split_documents(documents)
    
    print(f"[ingest] Created {len(texts)} chunks. Generating embeddings (Local CPU)...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    print(f"[ingest] Saving vector index to {DB_FAISS_PATH}...")
    db = FAISS.from_documents(texts, embeddings)
    db.save_local(DB_FAISS_PATH)
    print("[ingest] Success! Vector database created.")

if __name__ == "__main__":
    create_vector_db()
