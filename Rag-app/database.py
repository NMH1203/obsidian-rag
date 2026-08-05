import os
import time
import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv
from chunker import clean_syntax, parse_frontmatter, compute_hash
from embedder import embed_document

load_dotenv()

#Connect to database
def get_connection():
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            port=int(os.environ.get("DB_PORT", 5432)),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            dbname=os.environ.get("DB_NAME")
        )
        return conn
    except OperationalError as e:
        print(f"Can't connect to database:  {e}")
        return None

# Check if database (notes table) is empty
def is_db_empty(conn=None) -> bool:
    should_close_conn = False
    if conn is None:
        conn = get_connection()
        should_close_conn = True

    if not conn:
        return True

    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM notes LIMIT 1")
        has_data = cur.fetchone() is not None
        cur.close()
        return not has_data
    except Exception as e:
        print(f"error when check database: {e}")
        return True
    finally:
        if should_close_conn and conn:
            conn.close()


# Check hash of file in database
def hash_exists(content_hash: str, conn=None) -> bool:
    should_close_conn = False
    if conn is None:
        conn = get_connection()
        should_close_conn = True

    if not conn:
        return False

    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM notes WHERE content_hash = %s LIMIT 1", (content_hash,))
        exists = cur.fetchone() is not None
        cur.close()
        return exists
    except Exception as e:
        print(f"error when check hash file '{content_hash}': {e}")
        return False
    finally:
        if should_close_conn and conn:
            conn.close()

#Filter the list of markdown file paths by content hash.
def filter_unprocessed_files(filepaths: list, conn=None) -> tuple:

    processed_hashes = get_processed_hashes(conn)
    processed_files = []
    unprocessed_files = []

    for filepath in filepaths:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            file_hash = compute_hash(raw_content)

            if file_hash in processed_hashes:
                processed_files.append(filepath)
            else:
                unprocessed_files.append(filepath)
        except Exception as e:
            print(f"error when check hash file '{filepath}': {e}")
            unprocessed_files.append(filepath)

    return processed_files, unprocessed_files

#check source file processed
def is_source_processed(source_name: str, conn=None) -> bool:
    should_close_conn = False
    if conn is None:
        conn = get_connection()
        should_close_conn = True

    if not conn:
        return False

    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM notes WHERE source = %s LIMIT 1", (source_name,))
        exists = cur.fetchone() is not None
        cur.close()
        return exists
    except Exception as e:
        print(f"error when check source file '{source_name}': {e}")
        return False
    finally:
        if should_close_conn and conn:
            conn.close()

#get hash in database
def get_processed_hashes(conn=None) -> set:
    should_close_conn = False
    if conn is None:
        conn = get_connection()
        should_close_conn = True

    if not conn:
        return set()

    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT content_hash FROM notes WHERE content_hash IS NOT NULL")
        rows = cur.fetchall()
        cur.close()
        return {r[0] for r in rows if r[0]}
    except Exception as e:
        print(f"error when get hash file: {e}")
        return set()
    finally:
        if should_close_conn and conn:
            conn.close()

#clear all notes in database
def clear_all_notes(conn=None) -> bool:
    should_close_conn = False
    if conn is None:
        conn = get_connection()
        should_close_conn = True

    if not conn:
        print("error when try to connect database")
        return False

    try:
        cur = conn.cursor()
        cur.execute("TRUNCATE TABLE notes RESTART IDENTITY;")
        conn.commit()
        cur.close()
        print("Delete successfully notes in database")
        return True
    except Exception as e:
        conn.rollback()
        print(f"error when delete notes in database: {e}")
        return False
    finally:
        if should_close_conn and conn:
            conn.close()

#insert data to database
def insert_markdown_to_db(filepath_or_content: str, source_name: str = None, conn=None, skip_if_exists: bool = True):
    # read file markdown
    if os.path.exists(filepath_or_content):
        source = source_name or os.path.basename(filepath_or_content)
        with open(filepath_or_content, 'r', encoding='utf-8') as f:
            raw_content = f.read()
    else:
        source = source_name or "raw_markdown"
        raw_content = filepath_or_content

    # compute hash of file/content
    content_hash = compute_hash(raw_content)

    # check if file already exists in database
    if skip_if_exists and hash_exists(content_hash, conn=conn):
        print(f"skip '{source}' (hash: {content_hash[:10]}...)")
        return None

    #seperate the frontmatter
    content, _ = parse_frontmatter(raw_content)

    #clean the syntax
    cleaned_content = clean_syntax(content)
    if not cleaned_content:
        print(f"The content is empty {source}")
        return None

    #embed document with retry logic
    embedding = None
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        embedding = embed_document(cleaned_content)
        if embedding:
            break
        print(f"Retry embedding ({attempt}/{max_retries}) for: {source}")
        time.sleep(1)

    if not embedding:
        print(f"The embedding is empty after {max_retries} retries for: {source}")
        return None

    #insert to database
    should_close_conn = False
    if conn is None:
        conn = get_connection()
        should_close_conn = True

    if not conn:
        print("can't connect to the database.")
        return None

    try:
        cur = conn.cursor()
        #try insert with content hash
        try:
            cur.execute(
                "INSERT INTO notes (content, source, embedding, content_hash) VALUES (%s, %s, %s, %s) RETURNING id",
                (cleaned_content, source, embedding, content_hash)
            )
        except Exception:
            conn.rollback()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO notes (content, source, embedding) VALUES (%s, %s, %s) RETURNING id",
                (cleaned_content, source, embedding)
            )
        inserted_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        print(f"Successfully insert '{source}' (hash: {content_hash[:10]}...) into database with ID = {inserted_id}")
        return inserted_id
    except Exception as e:
        conn.rollback()
        print(f"error when insert into database: {e}")
        return None
    finally:
        if should_close_conn and conn:
            conn.close()

#delete old notes when update
def delete_note_by_source(source_name: str, conn=None) -> int:

    should_close_conn = False
    if conn is None:
        conn = get_connection()
        should_close_conn = True

    if not conn:
        return 0

    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM notes WHERE source = %s", (source_name,))
        deleted_count = cur.rowcount
        conn.commit()
        cur.close()
        return deleted_count
    except Exception as e:
        conn.rollback()
        print(f"error when try to delete note '{source_name}': {e}")
        return 0
    finally:
        if should_close_conn and conn:
            conn.close()

def update_markdown_note(filepath_or_content: str, source_name: str = None, conn=None):
    #read file or content
    if os.path.exists(filepath_or_content):
        source = source_name or os.path.basename(filepath_or_content)
        with open(filepath_or_content, 'r', encoding='utf-8') as f:
            raw_content = f.read()
    else:
        source = source_name or "raw_markdown"
        raw_content = filepath_or_content

    #compute new hash
    new_hash = compute_hash(raw_content)

    #open connection database
    should_close_conn = False
    if conn is None:
        conn = get_connection()
        should_close_conn = True

    if not conn:
        print("error when connect database")
        return None

    try:
        cur = conn.cursor()

        #get old hash of file 
        old_hash = None
        try:
            cur.execute("SELECT content_hash FROM notes WHERE source = %s LIMIT 1", (source,))
            row = cur.fetchone()
            if row:
                old_hash = row[0]
        except Exception:
            conn.rollback()
            cur = conn.cursor()

        #check if hash is same
        if old_hash is not None and old_hash == new_hash:
            print(f"skip file '{source}' (hash: {new_hash[:10]}...)")
            cur.close()
            return None

        #If hash changed -> delete old chunks/notes
        cur.execute("DELETE FROM notes WHERE source = %s", (source,))
        deleted_count = cur.rowcount
        conn.commit()

        if deleted_count > 0:
            print(f"update file '{source}' (hash: {new_hash[:10]}...)")

        #parse frontmatter and clean syntax
        content, _ = parse_frontmatter(raw_content)
        cleaned_content = clean_syntax(content)
        if not cleaned_content:
            print(f"The content is empty after cleaning for {source}")
            cur.close()
            return None

        #create new embedding
        new_embedding = None
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            new_embedding = embed_document(cleaned_content)
            if new_embedding:
                break
            print(f"Retry embedding ({attempt}/{max_retries}) for: {source}")
            time.sleep(1)

        if not new_embedding:
            print(f"error when embedding for: {source}")
            cur.close()
            return None

        #insert new note with new hash
        try:
            cur.execute(
                "INSERT INTO notes (content, source, embedding, content_hash) VALUES (%s, %s, %s, %s) RETURNING id",
                (cleaned_content, source, new_embedding, new_hash)
            )
        except Exception:
            conn.rollback()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO notes (content, source, embedding) VALUES (%s, %s, %s) RETURNING id",
                (cleaned_content, source, new_embedding)
            )

        inserted_id = cur.fetchone()[0]
        conn.commit()
        cur.close()

        print(f"Successfully update file '{source}' (hash: {new_hash[:10]}...) into database with ID = {inserted_id}")
        return inserted_id
    except Exception as e:
        conn.rollback()
        print(f"error when update note: {e}")
        return None
    finally:
        if should_close_conn and conn:
            conn.close()









