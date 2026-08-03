import os
from dotenv import load_dotenv
from loader import get_markdown_file
from database import get_connection, update_markdown_note
from chunker import parse_frontmatter, clean_syntax, compute_hash
from embedder import embed_document

load_dotenv()

def main():
    #get vault path from environment
    vault_path = os.getenv("VAULT_PATH")
    if not vault_path:
        print("error when try to find vault path")
        return

    #connect to database
    conn = get_connection()
    if not conn:
        print("error when try to connect database")
        return

    try:
        #get list markdown file
        files = get_markdown_file(vault_path)
        print(f"found {len(files)} file markdown")

        #scan and update new or modified markdown file to database
        updated_count = 0
        skipped_count = 0

        for filepath in files:
            result = update_markdown_note(filepath, conn=conn)
            if result:
                updated_count += 1
            else:
                skipped_count += 1

        print(f"Done scanning: {updated_count} files inserted/updated, {skipped_count} files unchanged.")
    finally:
        #close connection
        if conn:
            conn.close()

if __name__ == "__main__":
    main()




