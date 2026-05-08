from chromadb import PersistentClient

client = PersistentClient(
    path="./chroma_db"
)

collection = client.get_or_create_collection(
    name="resume_embeddings"
)