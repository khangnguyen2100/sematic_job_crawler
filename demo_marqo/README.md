# Marqo Learning Project

A simple starter project to demonstrate Marqo's vector search capabilities using a local Docker instance.

## What This Demo Does

This project demonstrates the core Marqo functionality:

- Creating a search index
- Adding documents with vector embeddings
- Performing semantic search queries
- Getting index statistics
- Filtering and advanced search features
- Document updates and retrieval

## Prerequisites

- Docker and Docker Compose installed
- Python 3.7+ installed
- curl (for connection testing)

## Quick Start

### Option 1: Automated Setup

```bash
# Run the setup script (recommended)
./setup.sh
```

### Option 2: Manual Setup

1. **Start Marqo Server**

   ```bash
   docker-compose up -d
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Test Connection**

   ```bash
   python test_connection.py
   ```

4. **Run Demos**

   ```bash
   # Basic demo
   python src/main.py
   
   # Advanced demo with filtering and updates
   python src/advanced_demo.py
   ```

## Project Structure

```text
marqo_learning/
├── README.md
├── requirements.txt
├── docker-compose.yml
├── setup.sh                    # Automated setup script
├── test_connection.py          # Connection testing utility
└── src/
    ├── main.py                 # Basic demo
    └── advanced_demo.py        # Advanced features demo
```

## Demo Features

### Basic Demo (`src/main.py`)

- Movie search index with 5 sample movies
- Semantic search queries about space, animation, dreams, and survival
- Shows relevance scoring and basic index statistics

### Advanced Demo (`src/advanced_demo.py`)

- Book search index with richer metadata
- Multiple tensor fields (title + description)
- Filtering by genre and publication year
- Document updates and specific field retrieval
- Demonstrates various search parameters

## What the Demo Shows

The demo will:

1. Clean up any existing index
2. Create a new index called "movies-index" using the `hf/e5-base-v2` model
3. Add 5 movie documents with titles, descriptions, and genres
4. Perform several semantic search queries to find relevant movies
5. Display index statistics

## Sample Output

You'll see output like:

```text
🎬 Starting Marqo Simple Demo
========================================
1. Cleaning up existing index...
2. Creating new index...
3. Adding movie documents...
4. Performing searches...
🔍 Query 1: Which movie is about space exploration?
   1. Interstellar (Score: 0.817)
   2. The Martian (Score: 0.808)
   ...
```

## Understanding the Results

- **Scores**: Higher scores (closer to 1.0) indicate better semantic match
- **Semantic Search**: The system understands meaning, not just keywords
- **Vector Embeddings**: Text is converted to high-dimensional vectors for similarity comparison

## Customization Ideas

- Add more movies/books with different descriptions
- Try different search queries
- Experiment with other embedding models (e.g., `open_clip/ViT-L-14/openai`)
- Add image URLs to documents for multimodal search
- Try filtering by different fields
- Implement custom scoring and ranking

## Troubleshooting

### Marqo Server Issues

```bash
# Check if Marqo is running
docker ps

# View Marqo logs
docker-compose logs marqo

# Restart Marqo
docker-compose restart marqo
```

### Connection Issues

```bash
# Test connection
python test_connection.py

# Check if port 8882 is available
curl http://localhost:8882
```

### Version Compatibility

Note: You might see a warning about Marqo version compatibility. The demos will still work, but consider upgrading to the latest Marqo Docker image for best results.

## Cleanup

To stop the Marqo server:

```bash
docker-compose down
```

To remove all data:

```bash
docker-compose down -v
```

## Next Steps

- Explore the [Marqo documentation](https://docs.marqo.ai/latest/)
- Try image search examples
- Build a web interface with Flask/FastAPI
- Implement RAG (Retrieval Augmented Generation) patterns
- Experiment with different embedding models
- Add real-world datasets

## Support

- [Marqo Community Slack](https://marqo-community.slack.com/join/shared_invite/zt-2sv2dq08k-C2tJbpm60HnH6A6GA2C0kw#/shared-invite/email)
- [Marqo Documentation](https://docs.marqo.ai/latest/)
- [GitHub Repository](https://github.com/marqo-ai/marqo)
