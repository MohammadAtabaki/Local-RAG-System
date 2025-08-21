import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import os
import uuid

class ChromaStore:
    def __init__(self, db_dir, collection_name="rag_docs"):
        self.client = chromadb.PersistentClient(path=db_dir)
        self.embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.client.get_or_create_collection(name=collection_name, embedding_function=self.embedding_fn)

    def add_documents(self, docs):
        for doc in docs:
            doc_id = str(uuid.uuid4())
            self.collection.add(
                documents=[doc["text"]],
                metadatas=[doc],
                ids=[doc_id]
            )

    def query(self, text, n_results=5):
        return self.collection.query(query_texts=[text], n_results=n_results)
