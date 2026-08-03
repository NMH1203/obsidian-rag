# 🗺️ RAG Pipeline Roadmap - Giai Đoạn 3

> [!INFO] Thông tin tổng quan
> - **Dự án**: RAG Vault (Hệ thống RAG cho Obsidian Notes)
> - **Mục tiêu**: Xây dựng luồng xử lý RAG hoàn chỉnh từ tài liệu Obsidian đến câu trả lời từ LLM.
> - **Cập nhật gần nhất**: 31/07/2026

---

## 📊 Bảng Đánh Giá Tiến Độ Hiện Tại

| Bước | Hạng Mục | Trạng Thái | File Liên Quan | Chi Tiết Đã Làm / Cần Làm |
|---|---|---|---|---|
| 1 | **Chunking** | 🟢 **Hoàn thành** (Cơ bản) | `Rag-app/chunker.py`<br>`Rag-app/loader.py` | - Bỏ frontmatter Obsidian (`---`)<br>- Chia chunk theo Heading `##`<br>- Gom note ngắn |
| 2 | **Embedding** | 🟢 **Hoàn thành** | `Rag-app/embedder.py` | - Kết nối LM Studio Embedding API<br>- Hàm `embed_document()` & `embed_query()` |
| 3 | **Indexing** | 🟡 **Đang dở dang** (50%) | `Rag-app/database.py`<br>`Rag-app/main.py` | - Kết nối PostgreSQL + pgvector<br>🔴 **Cần sửa**: Bug đóng connection sớm ở `database.py`<br>🔴 **Cần làm**: Script khởi tạo Table & Index (HNSW) |
| 4 | **Retrieval** | 🔴 **Chưa bắt đầu** | `Rag-app/retriever.py` | 🔴 **Cần làm**: Hàm `search_similar_chunks(query, top_k)` dùng cosine distance trong pgvector |
| 5 | **Augmentation** | 🔴 **Chưa bắt đầu** | `Rag-app/prompt_builder.py` | 🔴 **Cần làm**: Prompt Template gộp context + câu hỏi người dùng |
| 6 | **Generation** | 🟡 **Thử nghiệm** (30%) | `Rag-app/AI-model.py` | - Đã test gọi LLM qua LM Studio<br>🔴 **Cần làm**: Tích hợp luồng RAG hoàn chỉnh (End-to-End) |

---

## 📍 Chi Tiết Các Bước Cần Thực Hiện Tiếp Theo

### 1. 🔧 Sửa lỗi & Hoàn thiện Indexing (Bước 3)
- [x] Đọc file Obsidian và cắt chunk (`loader.py`, `chunker.py`)
- [x] Vector hóa chunk qua LM Studio (`embedder.py`)
- [x] **Fix bug `database.py`**: Loại bỏ `conn.close()` trong khối `finally` của `get_connection()`.
- [x] **Tạo bảng Database & Vector Index**:
  - Khai báo extension `pgvector` (`CREATE EXTENSION IF NOT EXISTS vector;`)
  - Tạo bảng `notes(id, content, source, embedding vector(dims))`
  - Tạo chỉ mục HNSW/IVFFlat để tăng tốc tìm kiếm vector.
- [x] **Hoàn thiện `main.py`**: Sửa lỗi khởi tạo `cur = conn.cursor()` và chuẩn hóa đường dẫn file trên Windows (`os.path.basename`).

### 2. 🔍 Xây dựng Module Retrieval (Bước 4)
- [x] Tạo file `Rag-app/retriever.py`
- [x] Tạo hàm `embed_query(user_query)`
- [ ] Thực hiện truy vấn Vector Similarity với pgvector:
  ```sql
  SELECT content, source, 1 - (embedding <=> %s::vector) AS similarity
  FROM notes
  ORDER BY embedding <=> %s::vector
  LIMIT %s;
  ```
- [ ] Lọc và trả về Top-K chunks liên quan nhất.

### 3. 📝 Augmentation & Prompt Engineering (Bước 5)
- [ ] Tạo file `Rag-app/prompt_builder.py`
- [ ] Thiết kế Prompt Template cho RAG:
  ```text
  Bạn là một trợ lý AI thông minh. Hãy trả lời câu hỏi của người dùng dựa TRỰC TIẾP vào ngữ cảnh dưới đây. 
  Nếu thông tin không có trong ngữ cảnh, hãy nói "Tôi không tìm thấy thông tin trong tài liệu".

  Context:
  {context_chunks}

  Câu hỏi:
  {user_query}
  ```

### 4. 🤖 Generation & RAG Query Pipeline (Bước 6)
- [ ] Tạo file `Rag-app/rag_service.py` đóng vai trò luồng xử lý chính:
  1. Nhận câu hỏi từ người dùng.
  2. Gọi `retriever.py` lấy Top-K context.
  3. Gọi `prompt_builder.py` tạo prompt.
  4. Gửi prompt sang LM Studio LLM (`client.chat.completions.create`).
  5. Trả câu trả lời cuối cùng kèm nguồn trích dẫn (`source`).

### 5. 🧪 Kiểm thử & Tối ưu (Evaluation)
- [ ] Đánh giá độ chính xác của tìm kiếm (Top-K Retrieval Quality).
- [ ] Thử nghiệm điều chỉnh kích thước Chunk (Chunk Size) và Overlap.
- [ ] Thử nghiệm các prompt khác nhau ([[10. Prompt Engineering for RAG]]).

---

## 🔗 Tài liệu liên quan
- [[2. Chunking Strategies]]
- [[9. Large Language Models (LLMs) for RAG]]
- [[10. Prompt Engineering for RAG]]
- #rag #roadmap #obsidian #vector-db #lm-studio
