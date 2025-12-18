from typing import List, Tuple, Dict, Any
import io
import pdfplumber
from docx import Document
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

from ocr.ocr_engine import ocr_image_bytes

def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> List[str]:
    text = " ".join(text.split())
    if not text:
        return []
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i+chunk_size])
        i += (chunk_size - overlap)
    return chunks

def extract_text_from_uploads(files) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Returns:
      extracted_texts: list of doc-level extracted text
      doc_meta: basic metadata
    """
    extracted_texts = []
    doc_meta = []

    for f in files:
        name = getattr(f, "name", "uploaded_file")
        suffix = name.lower().split(".")[-1]

        raw = f.read()

        text = ""
        if suffix == "pdf":
            with pdfplumber.open(io.BytesIO(raw)) as pdf:
                pages = []
                for p in pdf.pages:
                    pages.append(p.extract_text() or "")
                text = "\n".join(pages)

        elif suffix == "docx":
            doc = Document(io.BytesIO(raw))
            text = "\n".join([p.text for p in doc.paragraphs])

        elif suffix == "txt":
            text = raw.decode("utf-8", errors="ignore")

        elif suffix in ("png", "jpg", "jpeg"):
            text = ocr_image_bytes(raw)

        extracted_texts.append(text)
        doc_meta.append({"filename": name, "type": suffix, "chars": len(text)})

    return extracted_texts, doc_meta

def build_vector_store(extracted_texts: List[str]):
    """
    Builds FAISS index over chunked text.
    Returns: index, chunks, embedder
    """
    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    chunks: List[str] = []
    for t in extracted_texts:
        chunks.extend(_chunk_text(t))

    if not chunks:
        raise ValueError("No chunks were created from extracted text.")

    embs = embedder.encode(chunks, normalize_embeddings=True)
    embs = np.array(embs, dtype="float32")

    dim = embs.shape[1]
    index = faiss.IndexFlatIP(dim)  # cosine via normalized vectors + inner product
    index.add(embs)

    return index, chunks, embedder
