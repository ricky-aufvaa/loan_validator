import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from typing import List, Dict
import fitz
from langchain.text_splitter import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi


#The embeddings model used to embed the query and the text chunks
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")  

def check_faiss_exists(db_path: str, collection_name: str) -> bool:
    index_file = os.path.join(db_path, "index.faiss")
    store_file = os.path.join(db_path, "index.pkl")
    return os.path.exists(index_file) and os.path.exists(store_file)

def embed_and_store(chunks_with_metadata: List[Dict], db_path: str, collection_name: str):
    documents = [chunk["text"] for chunk in chunks_with_metadata]
    metadatas = [chunk["metadata"] for chunk in chunks_with_metadata]

    db = FAISS.from_texts(documents, embedding_model, metadatas=metadatas)
    db.save_local(db_path)
    

def load_local_faiss(db_path: str):
    return FAISS.load_local(db_path, embedding_model, allow_dangerous_deserialization=True)

def load_pdf(file_path):
    """
    Load a PDF file and extract its text content along with page numbers.
    :param file_path: Path to the PDF file.
    :return: A list of tuples containing (text, page_number).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    doc = fitz.open(file_path)
    pages = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        if not text.strip():  # Skip empty pages
            continue
        pages.append((text, page_num + 1))  # Store text and page number (1-based indexing)
    return pages

def chunk_text(pages: List[tuple], chunk_size=500, chunk_overlap=50):
    """
    Split the text into smaller chunks while preserving metadata (page number).
    :param pages: List of tuples containing (text, page_number).
    :param chunk_size: Maximum size of each chunk.
    :param chunk_overlap: Overlap between consecutive chunks.
    :return: List of dictionaries containing chunk text and metadata.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks_with_metadata = []
    for text, page_number in pages:
        chunks = splitter.split_text(text)
        for i, chunk in enumerate(chunks):
            if not chunk.strip():  # Skip empty chunks
                continue
            chunks_with_metadata.append({
                "text": chunk,
                "metadata": {
                    "page_number": page_number,
                    "chunk_index": f"id_{len(chunks_with_metadata)}",
                    "section_title": "Unknown"  # Placeholder for section title (can be improved)
                }
            })
    return chunks_with_metadata

def extract_keywords_bm25(chunks_with_metadata):
    """
    Extract keywords from each chunk using BM25.
    :param chunks_with_meta List of dictionaries containing chunk text and metadata.
    :return: Updated list of dictionaries with added keywords in metadata.
    """
    if not chunks_with_metadata:
        raise ValueError("No chunks available for keyword extraction.")

    # Tokenize all chunks
    tokenized_chunks = [chunk["text"].lower().split() for chunk in chunks_with_metadata]

    # Train BM25 model
    bm25 = BM25Okapi(tokenized_chunks)

    # Extract top keywords for each chunk
    for i, chunk in enumerate(chunks_with_metadata):
        # Tokenize the current chunk
        query_tokens = chunk["text"].lower().split()
        # Calculate BM25 scores for the query tokens
        scores = bm25.get_scores(query_tokens)
        # Get the indices of the top-scoring words
        top_indices = sorted(range(len(scores)), key=lambda x: scores[x], reverse=True)[:5]
        # Extract the top keywords
        keywords = list(set([tokenized_chunks[i][idx] for idx in top_indices]))
        # Store keywords as a comma-separated string in metadata
        chunk["metadata"]["keywords"] = ", ".join(keywords)
        for i in range(4):
            print(f"Chunk -{id}--{chunk}") 

    return chunks_with_metadata