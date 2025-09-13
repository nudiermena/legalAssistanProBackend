import os
import sys
from config.settings import POSTGRES_URL, MISTRAL_API_KEY
from agno.vectordb.pgvector import PgVector, SearchType
from agno.embedder.mistral import MistralEmbedder

def interactive_search():
    """Interactive knowledge base search interface."""
    
    print("🔍 Interactive Legal Knowledge Base Search")
    print("=" * 50)
    print("Search through your ingested legal documents!")
    print("Type 'quit' to exit, 'help' for search tips")
    print()
    
    # Convert POSTGRES_URL to the format expected by PgVector
    db_url = POSTGRES_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    
    # Create Mistral embedder
    print("📡 Initializing Mistral embedder...")
    mistral_embedder = MistralEmbedder(
        id="mistral-embed",
        dimensions=1024,
        api_key=MISTRAL_API_KEY
    )
    
    # Create PgVector instance for document_templates table
    print("🗄️  Connecting to document_templates table...")
    vector_db = PgVector(
        table_name="document_templates",
        db_url=db_url,
        search_type=SearchType.hybrid,
        embedder=mistral_embedder
    )
    
    print("✅ Ready for searching!")
    print()
    
    while True:
        try:
            # Get user query
            query = input("🔎 Enter your search query: ").strip()
            
            if query.lower() == 'quit':
                print("👋 Goodbye!")
                break
            elif query.lower() == 'help':
                print_search_help()
                continue
            elif not query:
                print("⚠️  Please enter a search query")
                continue
            
            # Get search type
            search_type = input("🔍 Search type (hybrid/vector/keyword) [hybrid]: ").strip().lower()
            if not search_type:
                search_type = 'hybrid'
            
            # Get result limit
            try:
                limit = int(input("📊 Number of results [5]: ").strip() or "5")
            except ValueError:
                limit = 5
            
            print(f"\n🔍 Searching for: '{query}'")
            print(f"🔍 Type: {search_type}")
            print(f"📊 Limit: {limit}")
            print("-" * 50)
            
            # Perform search
            results = perform_search(vector_db, query, search_type, limit)
            
            if results:
                display_results(results, query)
            else:
                print("❌ No results found")
            
            print("\n" + "=" * 50)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Please try again or type 'quit' to exit")

def perform_search(vector_db, query, search_type, limit):
    """Perform the specified type of search."""
    try:
        if search_type == 'vector':
            return vector_db.vector_search(query, limit=limit)
        elif search_type == 'keyword':
            return vector_db.keyword_search(query, limit=limit)
        else:  # hybrid
            return vector_db.hybrid_search(query, limit=limit)
    except Exception as e:
        print(f"❌ Search error: {e}")
        return []

def display_results(results, query):
    """Display search results in a formatted way."""
    print(f"✅ Found {len(results)} results for '{query}':")
    print()
    
    for i, result in enumerate(results, 1):
        print(f"📄 Result {i}:")
        
        # Display content
        if hasattr(result, 'content') and result.content:
            content = result.content.strip()
            # Truncate if too long
            if len(content) > 300:
                content = content[:300] + "..."
            print(f"   📝 Content: {content}")
        
        # Display metadata
        if hasattr(result, 'meta_data') and result.meta_data:
            print(f"   📊 Metadata: {result.meta_data}")
        
        # Display score if available
        if hasattr(result, 'score'):
            print(f"   🎯 Score: {result.score:.3f}")
        elif hasattr(result, 'hybrid_score'):
            print(f"   🎯 Hybrid Score: {result.hybrid_score:.3f}")
        
        print()

def print_search_help():
    """Print search help information."""
    print("\n📚 Search Help:")
    print("=" * 30)
    print("🔍 Search Types:")
    print("   • hybrid: Combines vector similarity and keyword matching (recommended)")
    print("   • vector: Uses only vector similarity (semantic search)")
    print("   • keyword: Uses only keyword matching (exact text search)")
    print()
    print("💡 Search Tips:")
    print("   • Use specific legal terms: 'contrato de arrendamiento'")
    print("   • Try different variations: 'demanda', 'demanda de divorcio'")
    print("   • Use legal concepts: 'prescripción', 'tutela', 'sucesión'")
    print("   • Search by document type: 'contrato', 'demanda', 'minuta'")
    print()
    print("📋 Example Queries:")
    print("   • 'contrato laboral'")
    print("   • 'demanda de alimentos'")
    print("   • 'tutela pensional'")
    print("   • 'prescripción de deudas'")
    print("   • 'propiedad intelectual'")
    print("   • 'derechos de autor'")
    print("   • 'sucesión intestada'")
    print()

if __name__ == "__main__":
    interactive_search() 