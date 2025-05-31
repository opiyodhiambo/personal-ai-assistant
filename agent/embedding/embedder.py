from uuid import uuid4
import hashlib
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.vectorstores.atlas import AtlasDB
from pymongo import MongoClient


class EmbeddingModel:
    def __init__(
        self,    
        mongo_uri: str = "",
        db_name: str = "langchain_test_db",
        collection_name: str = "langchain_test_vectorstores",
        index_name: str = "langchain-test-index-vectorstores",
        embedding_model: str = "nomic-embed-text:v1.5",
        dimensions: int = 768
    ):
        self.mongo_client = MongoClient(mongo_uri)
        self.embedding = OllamaEmbeddings(model=embedding_model) 
        self.collection = self.mongo_client[db_name][collection_name]
        self.dimensions = dimensions
        self.vector_store = MongoDBAtlasVectorSearch(
            collection = self.collection,
            embedding=self.embedding,
            index_name=index_name,
            relevance_score_fn="cosine" # We use cosine similarity as the relevance scoring function
        )
        self._ensure_index_exists() # We create the index if it does not exist

    """
    | Scenario                            | Recommended Setting                           |
    | ----------------------------------- | --------------------------------------------- |
    | Very long documents                 | Larger `chunk_size`, moderate `chunk_overlap` |
    | Need for precise semantic search    | Smaller `chunk_size`, low `chunk_overlap`     |
    | LLM input context is limited        | Smaller `chunk_size`                          |
    | Token-based limits (not char-based) | Use `length_function` that counts tokens      |

    """

    def index(self, documents, chunk_size, chunk_overlap):
        # Chunking the documents for faster indexing and retrieval
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        chunks = splitter.split_documents(documents)
        new_chunks = []
        new_ids = []

        for chunk in chunks:
            doc_hash = self._compute_doc_hash(chunk)
            if not self._document_exists(doc_hash):
                chunk.metadata["hash"] = doc_hash
                new_chunks.append(chunk)
                new_ids.append(str(uuid4()))


        if new_chunks:
            self.vector_store.add_documents(documents=new_chunks, ids=new_ids)



    def retrieve_context(self, user_query: str, k: int = 5, score_threshold: float = 0.7) -> str:
        """
        This performs semantic search on the vector store using the user query.

        Args:
            user_query (str): The input query string from the user.
            k (int): Number of top results to return.
            score_threshold (float): Minimum relevance score (0 to 1) for results to be considered relevant.

        Returns:
            str: A single string containing the combined content of the top relevant documents.
        """
        try:
            results = self.vector_store.similarity_search_with_score(user_query, k=k)

            # Filter by relevance score if specified
            filtered_context = [
                doc for doc, score in results if score >= score_threshold
            ]

            return "\n\n".join(filtered_context)

        except Exception as e:
            print(f"Error retrieving context: {e}")
            return ""


    def _ensure_index_exists(self):
        try:
            self.vector_store.create_vector_search_index(dimensions=self.dimensions) # perfect for our embedding model (nomic-embed-text:v1.5)
        except Exception as e:
            # We handle gracefully if index already exists
            if "already exists" not in str(e):
                raise
        
    
    def _document_exists(self, doc_hash):
        return self.collection.find_one({"hash": doc_hash}) is not None
    

    def _compute_doc_hash(self, doc):
        raw = doc.page_content + str(doc.metadata)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()






    