import os
from dotenv import load_dotenv
from loader import get_markdown_file
from database import get_connection, filter_unprocessed_files, update_markdown_note
from retriever import search_top_k
from prompt_builder import build_rag_messages
from ai_model import generate_answer

load_dotenv()

# Load markdown file from vault to database
def sync_vault_to_db(conn, vault_path: str):
    files = get_markdown_file(vault_path)
    print(f"Found {len(files)} markdown file in vault.")

    # Filter processed and unprocessed files using hash
    processed_files, unprocessed_files = filter_unprocessed_files(files, conn=conn)
    print(f"Statistics: {len(processed_files)} file have been updated (skip), {len(unprocessed_files)} file is new or has been edited.")

    if not unprocessed_files:
        print("All files have been processed and are up to date!")
        return

    processed_count = 0
    for filepath in unprocessed_files:
        result = update_markdown_note(filepath, conn=conn)
        if result:
            processed_count += 1

    print(f"Completed: processed {processed_count}/{len(unprocessed_files)} file.")

# Start RAG chat
def start_rag_chat(conn):
    print("\n" + "=" * 60)
    print("🤖 RAG SYSTEM READY! Enter your question (type 'exit' or 'q' to quit).")
    print("=" * 60)

    while True:
        try:
            query = input("\nQuestion: ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit", "q"]:
                print("Goodbye! 👋")
                break

            # Find chunk from database
            retrieved_chunks = search_top_k(query, top_k=5, conn=conn)

            # Build messages
            messages = build_rag_messages(query, retrieved_chunks)

            # Generate answer
            print("\nAI is thinking...")
            answer = generate_answer(messages)

            # Print answer
            print(f"\nAI:\n{answer}")

            # Show sources
            if retrieved_chunks:
                sources = sorted(list(set(chunk.get("source", "Unknown") for chunk in retrieved_chunks)))
                print(f"\n Sources: {', '.join(sources)}")
            else:
                print("\n No relevant context found in Database.")

        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye! 👋")
            break

def main():
    # Get vault path from environment variable
    vault_path = os.getenv("VAULT_PATH")
    if not vault_path:
        print("Error: not found VAULT_PATH in .env file")
        return

    # Connect to database
    conn = get_connection()
    if not conn:
        print("Cannot connect to database")
        return

    try:
        # Sync vault to database
        print("--- SYNC VAULT TO DATABASE ---")
        sync_vault_to_db(conn, vault_path)

        # Start RAG chat
        start_rag_chat(conn)

    finally:
        # Close database connection
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
