
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.services.vector_service import add_chunks

async def process_resume(file):
    text=""
    with pdfplumber.open(file.file) as pdf:
        for p in pdf.pages:
            text+=p.extract_text()

    splitter=RecursiveCharacterTextSplitter(chunk_size=500,chunk_overlap=50)
    chunks=splitter.split_text(text)
    add_chunks(chunks)

    return "Resume processed"
