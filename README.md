# Research Paper RAG System

Production-grade Retrieval-Augmented Generation system for academic papers.

## Features

- **PDF Processing**: Extract and intelligently chunk research papers
- **Vector Search**: Fast semantic similarity search using Qdrant
- **LLM Integration**: Support for Ollama, DeepSeek, and OpenAI
- **API Endpoints**: RESTful API for paper management and querying
- **Comprehensive Logging**: Detailed debugging with [v0] prefixed logs

## Quick Start

### Prerequisites

- Python 3.10+
- Docker (for Qdrant)
- Ollama (or DeepSeek/OpenAI API key)

### Setup

\`\`\`bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/research-paper-rag-assessment.git
cd research-paper-rag-assessment

# Run setup script
chmod +x SETUP.sh
./SETUP.sh

# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Start Ollama (in another terminal)
ollama serve
ollama pull llama2

# Activate environment
source venv/bin/activate

# Run server
python -m uvicorn src.main:app --reload
\`\`\`

## API Documentation

Visit `http://localhost:8000/docs` for interactive API docs.

### Upload Paper

\`\`\`bash
curl -F "file=@paper.pdf" http://localhost:8000/api/papers/upload
\`\`\`

### Query Papers

\`\`\`bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What methodology was used?",
    "top_k": 5
  }'
\`\`\`

## Configuration

Edit `.env` file to customize:

- `LLM_PROVIDER`: ollama, deepseek, or openai
- `CHUNK_SIZE`: Text chunk size (default: 512)
- `TOP_K`: Number of retrieved contexts (default: 5)
- `DEBUG`: Enable debug logging (default: True)

## Debugging

All services include comprehensive logging with `[v0]` prefix:

\`\`\`bash
# Check logs
tail -f logs/rag_system.log

# Debug specific component
# Look for [v0] prefixed messages in output
\`\`\`

## Project Structure

\`\`\`
├── src/
│   ├── config.py              # Configuration management
│   ├── main.py                # FastAPI entry point
│   ├── models/
│   │   └── schemas.py         # Pydantic models
│   ├── services/
│   │   ├── pdf_processor.py   # PDF processing
│   │   ├── embedding_service.py # Text embeddings
│   │   ├── qdrant_client.py   # Vector DB client
│   │   └── rag_pipeline.py    # RAG orchestration
│   └── api/
│       └── routes.py          # API endpoints
└── tests/
    └── test_services.py       # Unit tests
\`\`\`

## Performance

- PDF Upload: < 2 minutes for 5-10 page papers
- Query Response: 2-5 seconds (depends on LLM)
- Vector Search: < 100ms for 1000 papers

## Troubleshooting

### Qdrant Connection Error
\`\`\`bash
# Check if Qdrant is running
curl http://localhost:6333/health

# Restart Qdrant
docker restart <container_id>
\`\`\`

### Ollama Connection Error
\`\`\`bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama service
ollama serve
\`\`\`

### Out of Memory
- Reduce CHUNK_SIZE in .env
- Use smaller embedding model (e.g., "all-MiniLM-L6-v2")
- Process fewer papers at once

## Deployment

### Docker

\`\`\`bash
docker-compose up
\`\`\`

### Production

1. Set `DEBUG=False` in .env
2. Use production LLM provider
3. Set up proper database (PostgreSQL)
4. Enable authentication
5. Use proper secret management

## Testing

\`\`\`bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src
\`\`\`

## License

MIT
\`\`\`

---

### **STEP 17: Approach Documentation**
