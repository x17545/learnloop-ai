from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions


CHROMA_DIR = Path("chroma_db")

client = chromadb.PersistentClient(
    path=str(CHROMA_DIR),
)

embedding_function = embedding_functions.DefaultEmbeddingFunction()

collection = client.get_or_create_collection(
    name="learnloop_documents",
    embedding_function=embedding_function,
)


def add_chunks_to_vector_db(
    document_id: int,
    chunks: list[dict],
) -> None:
    if not chunks:
        return

    ids = []
    documents = []
    metadatas = []

    for chunk in chunks:
        chunk_id = (
            f"document-{document_id}"
            f"-page-{chunk['page_number']}"
            f"-chunk-{chunk['chunk_index']}"
        )

        ids.append(chunk_id)
        documents.append(chunk["text"])

        metadatas.append(
            {
                "document_id": document_id,
                "page_number": chunk["page_number"],
                "chunk_index": chunk["chunk_index"],
            }
        )

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
    )


def search_chunks(
    query: str,
    document_id: int,
    limit: int = 5,
):
    return collection.query(
        query_texts=[query],
        n_results=limit,
        where={
            "document_id": document_id,
        },
    )