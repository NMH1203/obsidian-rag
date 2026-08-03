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

# Check hash of file in database
def hash_exists(content_hash: str, conn=None) -> bool:
    """
    Kiểm tra xem content_hash đã tồn tại trong bảng 'notes' hay chưa.
    Nếu 'conn' không được truyền vào, hàm sẽ tự mở và tự đóng kết nối database.
    """
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
        print(f"Lỗi khi kiểm tra hash '{content_hash}': {e}")
        return False
    finally:
        if should_close_conn and conn:
            conn.close()

def is_source_processed(source_name: str, conn=None) -> bool:
    """
    Kiểm tra xem tên file/nguồn (source) đã tồn tại trong bảng 'notes' chưa.
    """
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
        print(f"Lỗi khi kiểm tra source '{source_name}': {e}")
        return False
    finally:
        if should_close_conn and conn:
            conn.close()

def get_processed_hashes(conn=None) -> set:
    """
    Lấy tập hợp tất cả các content_hash đã lưu trong database.
    """
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
        print(f"Lỗi khi lấy danh sách hash đã xử lý: {e}")
        return set()
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

            if file_hash in processed_hashes or hash_exists(file_hash, conn=conn):
                processed_files.append(filepath)
            else:
                unprocessed_files.append(filepath)
        except Exception as e:
            print(f"Lỗi khi kiểm tra file {filepath}: {e}")
            unprocessed_files.append(filepath)

    return processed_files, unprocessed_files

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
        print(f"Lỗi khi xóa chunk cũ của source '{source_name}': {e}")
        return 0
    finally:
        if should_close_conn and conn:
            conn.close()

def update_markdown_note(filepath_or_content: str, source_name: str = None, conn=None):
    """
    Cập nhật file note trong DB khi nội dung bị chỉnh sửa:
    1. Đọc nội dung file và tính Hash mới bằng `compute_hash` từ `chunker.py`.
    2. So sánh Hash mới với Hash cũ trong DB.
    3. Nếu Hash giống nhau -> Bỏ qua (không cần làm gì).
    4. Nếu Hash khác nhau -> Xóa sạch các chunk/bản ghi cũ của file đó trong DB,
       lọc lại ký tự đặc biệt bằng `clean_syntax`, tạo embedding mới và lưu lại với Hash mới.
    """
    # 1. Đọc file hoặc lấy chuỗi trực tiếp
    if os.path.exists(filepath_or_content):
        source = source_name or os.path.basename(filepath_or_content)
        with open(filepath_or_content, 'r', encoding='utf-8') as f:
            raw_content = f.read()
    else:
        source = source_name or "raw_markdown"
        raw_content = filepath_or_content

    # 2. Tính Hash mới từ nội dung vừa đọc
    new_hash = compute_hash(raw_content)

    # 3. Mở kết nối DB
    should_close_conn = False
    if conn is None:
        conn = get_connection()
        should_close_conn = True

    if not conn:
        print("[Lỗi] Không thể kết nối cơ sở dữ liệu.")
        return None

    try:
        cur = conn.cursor()

        # 4. Lấy Hash cũ của file theo `source`
        old_hash = None
        try:
            cur.execute("SELECT content_hash FROM notes WHERE source = %s LIMIT 1", (source,))
            row = cur.fetchone()
            if row:
                old_hash = row[0]
        except Exception:
            conn.rollback()
            cur = conn.cursor()

        # 5. Kiểm tra nếu Hash không đổi -> Bỏ qua
        if old_hash is not None and old_hash == new_hash:
            print(f"[Bỏ qua] File '{source}' nội dung không đổi (Hash khớp nhau).")
            cur.close()
            return None

        # 6. Nếu Hash thay đổi -> Xóa toàn bộ chunk/bản ghi CŨ của note này
        cur.execute("DELETE FROM notes WHERE source = %s", (source,))
        deleted_count = cur.rowcount
        conn.commit()

        if deleted_count > 0:
            print(f"[Cập nhật] Xóa {deleted_count} chunk/bản ghi CŨ của file '{source}' (Hash cũ: {old_hash[:10] if old_hash else 'N/A'}).")

        # 7. Tách Frontmatter và lọc ký tự đặc biệt bằng `clean_syntax` từ chunker.py
        content, _ = parse_frontmatter(raw_content)
        cleaned_content = clean_syntax(content)
        if not cleaned_content:
            print(f"[Cảnh báo] Nội dung rỗng sau khi lọc: {source}")
            cur.close()
            return None

        # 8. Tạo Embedding mới (có retry)
        new_embedding = None
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            new_embedding = embed_document(cleaned_content)
            if new_embedding:
                break
            print(f"Retry embedding ({attempt}/{max_retries}) for: {source}")
            time.sleep(1)

        if not new_embedding:
            print(f"[Lỗi] Không thể tạo embedding mới cho: {source} sau {max_retries} lần thử.")
            cur.close()
            return None

        # 9. Chèn bản ghi MỚI với Hash MỚI
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

        print(f"[Thành công] Đã CẬP NHẬT file '{source}' (Hash mới: {new_hash[:10]}...) vào DB với ID = {inserted_id}")
        return inserted_id
    except Exception as e:
        conn.rollback()
        print(f"[Lỗi] Cập nhật note thất bại: {e}")
        return None
    finally:
        if should_close_conn and conn:
            conn.close()

#reprocess all note in database
def reprocess_existing_notes(max_retries: int = 3):
    conn = get_connection()
    if not conn:
        print("error when try to connect database")
        return

    try:
        cur = conn.cursor()
        cur.execute("SELECT id, content, source FROM notes")
        rows = cur.fetchall()

        if not rows:
            print("No notes found in database to reprocess.")
            cur.close()
            conn.close()
            return

        print(f"Reprocessing {len(rows)} notes in database...")

        updated_count = 0
        for row_id, old_content, source in rows:
            if not old_content:
                continue

            #seperate frontmatter
            content, _ = parse_frontmatter(old_content)
            #clean the syntax
            cleaned_content = clean_syntax(content)
            if not cleaned_content:
                print(f"Skipping ID {row_id} ({source}): content is empty after cleaning.")
                continue

            #compute new hash
            new_hash = compute_hash(cleaned_content)

            #compute new embedding
            new_embedding = None
            for attempt in range(1, max_retries + 1):
                new_embedding = embed_document(cleaned_content)
                if new_embedding:
                    break
                print(f"Retry embedding ({attempt}/{max_retries}) for ID {row_id} ({source})")
                time.sleep(1)

            if not new_embedding:
                print(f"Failed to generate embedding for ID {row_id} ({source}) after {max_retries} retries.")
                continue

            #update into database
            try:
                cur.execute(
                    "UPDATE notes SET content = %s, embedding = %s, content_hash = %s WHERE id = %s",
                    (cleaned_content, new_embedding, new_hash, row_id)
                )
            except Exception:
                conn.rollback()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE notes SET content = %s, embedding = %s WHERE id = %s",
                    (cleaned_content, new_embedding, row_id)
                )

            updated_count += 1

        conn.commit()
        cur.close()
        print(f"Successfully reprocessed {updated_count}/{len(rows)} notes in database.")
    except Exception as e:
        conn.rollback()
        print(f"Error when reprocessing notes: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    reprocess_existing_notes()








