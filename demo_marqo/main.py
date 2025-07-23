import marqo
import time

def main():
    # Create a Marqo client (local instance)
    mq = marqo.Client(url="http://localhost:8882")
    
    # Index name for our demo
    index_name = "movies-index"
    
    print("🎬 Starting Marqo Simple Demo")
    print("=" * 40)
    
    # Step 1: Housekeeping - Delete index if it exists
    print("1. Cleaning up existing index...")
    try:
        mq.index(index_name).delete()
        print(f"   ✓ Deleted existing '{index_name}' index")
    except Exception as e:
        print(f"   ℹ️  No existing index found (this is okay)")
    
    # Step 2: Create a new index
    print("2. Creating new index...")
    try:
        mq.create_index(index_name, model="hf/e5-base-v2")
        print(f"   ✓ Created '{index_name}' with hf/e5-base-v2 model")
        
        # Wait a moment for index to be ready
        print("   ⏳ Waiting for index to be ready...")
        time.sleep(3)
        
    except Exception as e:
        print(f"   ❌ Error creating index: {e}")
        return
    
    # Step 3: Add documents to the index
    print("3. Adding movie documents...")
    movies = [
      {
          "Title": "Finding Nemo",
          "Description": "A clownfish father searches for his lost son across the ocean.",
          "Genre": "Animation"
      },
      {
          "Title": "Inception",
          "Description": "A skilled thief uses dream-sharing technology to implant an idea into a CEO's mind.",
          "Genre": "Science Fiction"
      },
      {
          "Title": "Breaking Bad",
          "Description": "A high school chemistry teacher turns to cooking meth after a cancer diagnosis.",
          "Genre": "Crime Drama (TV Show)"
      },
      {
          "Title": "The Office",
          "Description": "A mockumentary sitcom depicting the daily lives of office employees in Scranton, Pennsylvania.",
          "Genre": "Comedy (TV Show)"
      },
      {
          "Title": "Interstellar",
          "Description": "A team of explorers travel through a wormhole in space in an attempt to save humanity.",
          "Genre": "Science Fiction"
      },
      {
          "Title": "Game of Thrones",
          "Description": "Noble families fight for control over the Seven Kingdoms of Westeros.",
          "Genre": "Fantasy (TV Show)"
      },
      {
          "Title": "The Dark Knight",
          "Description": "Batman faces his greatest challenge yet as he takes on the Joker, a criminal mastermind.",
          "Genre": "Action"
      },
      {
          "Title": "Stranger Things",
          "Description": "A group of kids uncover a government conspiracy and supernatural forces in their small town.",
          "Genre": "Horror, Sci-Fi (TV Show)"
      },
      {
          "Title": "Forrest Gump",
          "Description": "The story of a slow-witted but kind-hearted man who witnesses several historical events in the 20th century.",
          "Genre": "Drama, Romance"
      },
      {
          "Title": "Gladiator",
          "Description": "A betrayed Roman general seeks revenge against the corrupt emperor who murdered his family.",
          "Genre": "Historical Action Drama"
      },
      {
          "Title": "Coco",
          "Description": "A young boy journeys to the Land of the Dead to uncover his family's secrets.",
          "Genre": "Animation, Musical"
      },
      {
          "Title": "Sherlock",
          "Description": "A modern update finds the famous sleuth and his doctor partner solving crime in 21st century London.",
          "Genre": "Mystery, Crime (TV Show)"
      },
      {
          "Title": "The Crown",
          "Description": "A dramatized history of the reign of Queen Elizabeth II.",
          "Genre": "Historical Drama (TV Show)"
      },
      {
          "Title": "The Conjuring",
          "Description": "Paranormal investigators help a family terrorized by a dark presence in their farmhouse.",
          "Genre": "Horror"
      },
      {
          "Title": "Black Mirror",
          "Description": "An anthology series exploring a twisted, high-tech multiverse where humanity's greatest innovations and darkest instincts collide.",
          "Genre": "Science Fiction, Thriller (TV Show)"
      },
      {
          "Title": "The Pursuit of Happyness",
          "Description": "A struggling salesman takes custody of his son as he's poised to begin a life-changing professional career.",
          "Genre": "Drama, Biography"
      },
      {
          "Title": "La La Land",
          "Description": "A jazz musician and an aspiring actress fall in love while pursuing their dreams in Los Angeles.",
          "Genre": "Musical, Romance"
      },
      {
          "Title": "Narcos",
          "Description": "The true story of Colombia's infamously violent and powerful drug cartels.",
          "Genre": "Crime, Thriller (TV Show)"
      },
      {
          "Title": "The Grand Budapest Hotel",
          "Description": "A concierge teams up with one of his employees to prove his innocence after he is framed for murder.",
          "Genre": "Comedy, Drama"
      },
      {
          "Title": "Rick and Morty",
          "Description": "A sociopathic scientist and his grandson go on dangerous, interdimensional adventures.",
          "Genre": "Animated Sci-Fi Comedy (TV Show)"
      }
  ]
    
    try:
        response = mq.index(index_name).add_documents(
            movies,
            tensor_fields=["Description"]  # Use Description field for vector search
        )
        print(f"   ✓ Added {len(movies)} movies to the index")
        
        # Wait for documents to be processed
        print("   ⏳ Processing documents...")
        time.sleep(2)
        
    except Exception as e:
        print(f"   ❌ Error adding documents: {e}")
        return
    
    # Step 4: Perform searches
    print("4. Performing searches...")
    print("-" * 40)
    
    # Search queries to test
    queries = [
        "Movie/TV Show in England",
        "Movie/TV about the main character named Walter White",
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n🔍 Query {i}: {query}")
        try:
            results = mq.index(index_name).search(q=query, limit=3)
            
            for j, result in enumerate(results["hits"], 1):
                score = result['_score']
                title = result['Title']
                description = result['Description']
                genre = result['Genre']
                print(f"   {j}. {title} (Score: {score:.3f})")
                print(f"      Genre: {genre}")
                print(f"      Description: {description}")
                
        except Exception as e:
            print(f"   ❌ Search error: {e}")
    
    # Step 5: Demonstrate getting index stats
    print("\n5. Index Statistics:")
    print("-" * 40)
    try:
        stats = mq.index(index_name).get_stats()
        print(f"   📊 Number of documents: {stats.get('numberOfDocuments', 'N/A')}")
        print(f"   📊 Number of vectors: {stats.get('numberOfVectors', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Error getting stats: {e}")
    
    print("\n🎉 Demo completed successfully!")
    print("\nNext steps:")
    print("- Try modifying the search queries")
    print("- Add more movies with different descriptions")
    print("- Experiment with different models")
    print("- Try image search by adding image URLs to documents")

if __name__ == "__main__":
    main()