# RAG System Implementation Guide

## Overview

A **Retrieval-Augmented Generation (RAG)** system has been integrated into the placement prep analyzer platform. This system enables semantic search within uploaded topic PDFs, allowing students and staff to find relevant content using natural language queries.

## Architecture

### Components

1. **PDF Processing Service** (`app/services/pdf_service.py`)
   - Extracts text from PDF files
   - Splits text into chunks for embedding
   - Handles metadata tracking (page numbers, chunk indices)

2. **Vector Service** (`app/services/vector_service.py`)
   - Manages embeddings using Google Generative AI
   - Stores embeddings in Chroma vector database (per-topic isolation)
   - Performs similarity searches on embeddings

3. **Database Models** (`app/database/models.py`)
   - Topic model enhanced with RAG fields:
     - `is_indexed`: Boolean flag indicating if topic has been embedded
     - `embedding_chunks`: Number of text chunks created
     - `last_indexed_at`: Timestamp of last embedding generation

4. **API Endpoints** 
   - **Staff**: `POST /staff/upload-topic` - Upload PDF with automatic embedding
   - **Staff**: `POST /staff/search-topic/{topic_id}` - Search topics
   - **Student**: `POST /student/search-topic/{topic_id}` - Search topics
   - **Student**: `GET /student/topics` - Retrieve all indexed topics

## Data Flow

### Upload Flow
```
PDF Upload
    ↓
Validation (size, format)
    ↓
Save to Disk
    ↓
Extract Text (pdfplumber)
    ↓
Create Chunks (RecursiveCharacterTextSplitter)
    ↓
Generate Embeddings (Google Generative AI)
    ↓
Store in Vector DB (Chroma - per topic)
    ↓
Update Topic Metadata (is_indexed=True, chunk_count)
```

### Search Flow
```
User Query
    ↓
Validate Query & Topic
    ↓
Generate Query Embedding
    ↓
Similarity Search in Vector Store
    ↓
Retrieve Top K Results
    ↓
Return Ranked Results with Metadata
```

## Configuration

### Environment Variables
```bash
GOOGLE_API_KEY=<your-google-generative-ai-key>
GEMINI_API_KEY=<alternative-key>
```

### Vector Database Location
```
backend/vector_db/
├── topic_1/
│   ├── .chroma/
│   ├── chroma.sqlite3
│   └── [embeddings and metadata]
├── topic_2/
└── topic_N/
```

Each topic gets its own Chroma collection for isolated embeddings and efficient searches.

## API Usage Examples

### Upload Topic with RAG
```bash
curl -X POST http://localhost:8003/staff/upload-topic \
  -H "Authorization: Bearer <token>" \
  -F "title=Python Basics" \
  -F "description=Python fundamentals" \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "id": 1,
  "title": "Python Basics",
  "description": "Python fundamentals",
  "file_size": 524288,
  "is_indexed": true,
  "embedding_chunks": 45,
  "message": "Topic uploaded successfully! Processed 45 chunks for semantic search."
}
```

### Search Topic (Staff)
```bash
curl -X POST "http://localhost:8003/staff/search-topic/1?query=what+is+a+function" \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
  "topic_id": 1,
  "topic_title": "Python Basics",
  "query": "what is a function",
  "num_results": 5,
  "results": [
    {
      "content": "A function is a reusable block of code that performs a specific task...",
      "page": "3",
      "score": 0.92
    },
    {
      "content": "Functions help organize code and make it more maintainable...",
      "page": "4",
      "score": 0.88
    }
  ]
}
```

### Search Topic (Student)
```bash
curl -X POST "http://localhost:8003/student/search-topic/1?query=function+parameters" \
  -H "Authorization: Bearer <token>"
```

## Database Migrations

A migration script has been created to add RAG fields to existing databases:

```bash
cd backend
python app/database/migrate_rag.py
```

**Fields Added:**
- `is_indexed` BOOLEAN DEFAULT FALSE
- `embedding_chunks` INTEGER DEFAULT 0
- `last_indexed_at` TIMESTAMP NULL

## Embedding Process Details

### Text Splitting
- **Chunk Size**: 500 characters
- **Overlap**: 50 characters
- **Separators**: `["\\n\\n", "\\n", ".", " ", ""]` (hierarchical)

### Embeddings
- **Model**: Google Generative AI `models/embedding-001`
- **Dimensions**: 768
- **Similarity Metric**: Cosine similarity

### Search Parameters
- **Top K Results**: 5 (configurable per search)
- **Minimum Query Length**: 1 character
- **Metadata Returned**: Content, Page number, Relevance score

## Error Handling

### Upload Errors
- File format validation (PDF only)
- File size check (max 10MB)
- PDF text extraction failures (graceful degradation)
- Vector store initialization failures

### Search Errors
- Topic not found (404)
- Topic not indexed (400)
- Invalid query (400)
- Vector search failures (500)

## Performance Considerations

### Embedding Generation
- First-time embedding: ~2-10 seconds per PDF (depending on size)
- Uses asynchronous processing for non-blocking uploads
- Embeddings cached in per-topic Chroma collections

### Search Performance
- Semantic search: O(1) with Chroma indexing
- Top K retrieval: ~100-500ms for typical documents
- No database hits required for search (vector DB only)

### Storage
- Estimated: ~1KB per chunk in vector DB
- 1000-chunk PDF = ~1MB vector index
- Separate from original PDF file storage

## Future Enhancements

1. **Multi-Topic Search**: Cross-topic semantic search with ranking
2. **Custom Embeddings**: Fine-tuned embeddings for domain-specific content
3. **Semantic Caching**: Cache results for frequent queries
4. **Batch Reindexing**: Bulk update embeddings for updated topics
5. **Search Analytics**: Track popular queries and search performance
6. **Similarity Thresholding**: Filter results by minimum relevance score
7. **Sparse Retrieval**: Combine BM25 with semantic search for hybrid retrieval

## Troubleshooting

### Topics Not Being Indexed
- Check if PDF text extraction succeeds
- Verify GOOGLE_API_KEY is set correctly
- Check `vector_db/` directory permissions

### Poor Search Results
- Ensure queries are specific and relevant to topic
- Check if topic has sufficient content (minimum 500 chars recommended)
- Verify topic is marked `is_indexed=true`

### High Memory Usage
- Each topic's vector store is loaded on first search
- Consider implementing lazy loading for large deployments
- Chroma handles memory efficiently with on-disk storage

## Security Notes

- Vector embeddings are stored locally (not sent to external services except Google AI)
- Topics are isolated per topic ID (no cross-topic leakage)
- Search results respect topic access permissions (handled by API authentication)
- Raw PDFs are stored separately from embeddings for audit trail

## Testing

To test the RAG system:

```bash
# Start the server
cd intelligent_placement_prep_analyser
./run-backend.sh

# Upload a topic
curl -X POST http://localhost:8003/staff/upload-topic \
  -H "Authorization: Bearer <token>" \
  -F "title=Test Topic" \
  -F "file=@sample.pdf"

# Search the topic
curl -X POST "http://localhost:8003/student/search-topic/1?query=your+search+query" \
  -H "Authorization: Bearer <token>"
```

## References

- [LangChain Documentation](https://python.langchain.com/)
- [Chroma Documentation](https://docs.trychroma.com/)
- [Google GenerativeAI](https://ai.google.dev/)
- [PDFPlumber](https://github.com/jsvine/pdfplumber)
