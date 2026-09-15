#venv\Scripts\python view_chroma.py
import chromadb
import json

def view_chroma():
    print("Connecting to ChromaDB...")
    # Point to the local chroma data folder
    client = chromadb.PersistentClient(path="./chroma_data")
    
    try:
        # Get the collection
        collection = client.get_collection("tripmate_knowledge")
        
        total_items = collection.count()
        print(f"\n--- Total Items in 'tripmate_knowledge' Collection: {total_items} ---")
        
        if total_items == 0:
            print("No documents found in the collection yet.")
            return

        # Peek at the first 5 entries (or fewer if there aren't 5)
        limit = min(5, total_items)
        results = collection.peek(limit)
        
        print(f"\nShowing the first {limit} entries:\n")

        for i in range(len(results["documents"])):
            print(f"========== [ Entry {i+1} ] ==========")
            print(f"ID: {results['ids'][i]}")
            print(f"Metadata: {json.dumps(results['metadatas'][i], indent=2)}")
            print(f"Document Text:\n{results['documents'][i]}")
            print("=====================================\n")
            
    except Exception as e:
        print(f"Error accessing collection: {e}")
        print("Note: If the collection doesn't exist yet, it means no data has been saved to the vector database.")

if __name__ == "__main__":
    view_chroma()
