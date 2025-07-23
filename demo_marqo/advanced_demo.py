import marqo
import time

def advanced_demo():
    """
    Advanced Marqo demo showing additional features like:
    - Filtering
    - Multiple tensor fields
    - Document updates
    - Different search parameters
    """
    mq = marqo.Client(url="http://localhost:8882")
    index_name = "books-index"
    
    print("📚 Starting Advanced Marqo Demo")
    print("=" * 50)
    
    # Cleanup
    try:
        mq.index(index_name).delete()
        print("🧹 Cleaned up existing index")
    except:
        print("🧹 No existing index to clean")
    
    # Create index
    print("📖 Creating books index...")
    mq.create_index(index_name, model="hf/e5-base-v2")
    time.sleep(3)
    
    # Add documents with multiple searchable fields
    books = [
        {
            "_id": "book1",
            "title": "The Hitchhiker's Guide to the Galaxy",
            "author": "Douglas Adams",
            "description": "A comedic science fiction series following Arthur Dent's adventures across the universe.",
            "genre": "Science Fiction",
            "year": 1979,
            "rating": 4.2
        },
        {
            "_id": "book2",
            "title": "Dune",
            "author": "Frank Herbert",
            "description": "Epic space opera about politics, religion, and ecology on the desert planet Arrakis.",
            "genre": "Science Fiction",
            "year": 1965,
            "rating": 4.3
        },
        {
            "_id": "book3",
            "title": "Pride and Prejudice",
            "author": "Jane Austen",
            "description": "Classic romance novel about Elizabeth Bennet and Mr. Darcy in Regency England.",
            "genre": "Romance",
            "year": 1813,
            "rating": 4.1
        },
        {
            "_id": "book4",
            "title": "The Lord of the Rings",
            "author": "J.R.R. Tolkien",
            "description": "Epic fantasy adventure following Frodo's quest to destroy the One Ring.",
            "genre": "Fantasy",
            "year": 1954,
            "rating": 4.5
        },
        {
            "_id": "book5",
            "title": "1984",
            "author": "George Orwell",
            "description": "Dystopian novel about totalitarian surveillance and thought control.",
            "genre": "Dystopian",
            "year": 1949,
            "rating": 4.0
        }
    ]
    
    # Add documents with both title and description as searchable fields
    print("📚 Adding books...")
    mq.index(index_name).add_documents(
        books,
        tensor_fields=["title", "description"]
    )
    time.sleep(3)
    
    # Demonstrate different types of searches
    print("\n🔍 Search Demonstrations:")
    print("-" * 50)
    
    # 1. Basic semantic search
    print("\n1. Basic search for 'space adventures':")
    results = mq.index(index_name).search(q="space adventures", limit=2)
    for hit in results["hits"]:
        print(f"   📖 {hit['title']} by {hit['author']} (Score: {hit['_score']:.3f})")
    
    # 2. Search with filtering
    print("\n2. Search for sci-fi books only:")
    results = mq.index(index_name).search(
        q="futuristic technology",
        limit=3,
        filter_string="genre:(Science Fiction)"
    )
    for hit in results["hits"]:
        print(f"   📖 {hit['title']} - {hit['genre']} (Score: {hit['_score']:.3f})")
    
    # 3. Search with year filtering
    print("\n3. Books published after 1950:")
    results = mq.index(index_name).search(
        q="adventure",
        limit=3,
        filter_string="year:[1950 TO *]"
    )
    for hit in results["hits"]:
        print(f"   📖 {hit['title']} ({hit['year']}) (Score: {hit['_score']:.3f})")
    
    # 4. Update a document
    print("\n4. Updating a book's rating...")
    mq.index(index_name).add_documents([
        {
            "_id": "book1",
            "title": "The Hitchhiker's Guide to the Galaxy",
            "author": "Douglas Adams",
            "description": "A comedic science fiction series following Arthur Dent's adventures across the universe. Absolutely hilarious!",
            "genre": "Science Fiction",
            "year": 1979,
            "rating": 4.4  # Updated rating
        }
    ], tensor_fields=["title", "description"])
    time.sleep(2)
    
    # 5. Get specific document
    print("\n5. Getting updated document:")
    doc = mq.index(index_name).get_document("book1")
    print(f"   📖 {doc['title']} - New rating: {doc['rating']}")
    
    # 6. Search with attributes to return
    print("\n6. Search returning only specific fields:")
    results = mq.index(index_name).search(
        q="romance love",
        limit=2,
        attributes_to_retrieve=["title", "author", "year"]
    )
    for hit in results["hits"]:
        print(f"   📖 {hit['title']} by {hit['author']} ({hit['year']})")
    
    # Show index stats
    print("\n📊 Index Statistics:")
    stats = mq.index(index_name).get_stats()
    print(f"   Documents: {stats.get('numberOfDocuments', 'N/A')}")
    print(f"   Vectors: {stats.get('numberOfVectors', 'N/A')}")
    
    print("\n✨ Advanced demo completed!")
    print("\nFeatures demonstrated:")
    print("- Multiple tensor fields (title + description)")
    print("- Filtering by genre and year")
    print("- Document updates")
    print("- Specific field retrieval")
    print("- Document retrieval by ID")

if __name__ == "__main__":
    advanced_demo()
