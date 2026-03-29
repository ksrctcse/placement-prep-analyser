"""
PDF Processing Service for RAG
Handles PDF text extraction and chunk creation
"""
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Tuple


def extract_text_from_pdf(file_path: str) -> Tuple[str, int]:
    """
    Extract all text from a PDF file
    Returns: (full_text, total_pages)
    """
    full_text = ""
    total_pages = 0
    
    try:
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"📄 PDF loaded: {total_pages} pages")
            
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    full_text += f"\n--- Page {page_num + 1} ---\n{text}\n"
                else:
                    print(f"⚠️  Page {page_num + 1}: No text extracted (possibly scanned image)")
        
        print(f"✓ Extracted {len(full_text)} characters from {total_pages} pages")
        return full_text, total_pages
    except Exception as e:
        print(f"❌ Error extracting PDF: {e}")
        raise


def create_chunks(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> Tuple[List[str], Dict]:
    """
    Split text into chunks with metadata
    Returns: (chunks, metadata)
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    chunks = splitter.split_text(text)
    
    # Create metadata for each chunk
    chunk_metadatas = []
    current_page = 1
    
    for i, chunk in enumerate(chunks):
        # Try to extract page number from chunk if it contains "--- Page X ---"
        if "--- Page" in chunk:
            try:
                page_str = chunk.split("--- Page ")[1].split(" ---")[0]
                current_page = int(page_str)
            except:
                pass
        
        chunk_metadatas.append({
            "chunk_index": i,
            "page": current_page,
            "chunk_size": len(chunk)
        })
    
    return chunks, chunk_metadatas


def process_pdf_for_rag(file_path: str) -> Tuple[List[str], List[Dict]]:
    """
    Complete pipeline: Extract PDF -> Create Chunks -> Return with metadata
    """
    # Extract text
    text, total_pages = extract_text_from_pdf(file_path)
    
    if not text or not text.strip():
        raise ValueError("No text could be extracted from PDF")
    
    # Create chunks
    chunks, metadatas = create_chunks(text)
    
    if not chunks:
        raise ValueError("No chunks created from PDF text")
    
    print(f"✓ Extracted {len(chunks)} chunks from {total_pages} pages")
    
    return chunks, metadatas
