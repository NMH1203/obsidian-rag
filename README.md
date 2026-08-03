# Obsidian RAG Vault

Hệ thống RAG (Retrieval-Augmented Generation) cá nhân dành cho Obsidian Vault, tự động quét, xử lý, tạo vector embedding và truy vấn dữ liệu các ghi chú Markdown.

## 🚀 Tính Năng Nổi Bật

- **Tự động quét & Đồng bộ Vault**: Quét toàn bộ ghi chú `.md` trong kho Obsidian Vault.
- **Phát hiện thay đổi thông minh (Deduplication & Incremental Sync)**: Dùng Content Hash (`MD5`) để so sánh.
  - File mới: Tự động embed & chèn vào Database.
  - File bị chỉnh sửa: Tự động xóa bản ghi cũ & cập nhật bản ghi mới.
  - File không đổi: Tự động bỏ qua để tiết kiệm tài nguyên.
- **Tiền xử lý văn bản**: Tách Frontmatter YAML, lọc ký tự đặc biệt và làm sạch cú pháp Markdown.
- **Lưu trữ Vector mạnh mẽ**: Sử dụng PostgreSQL với tiện ích mở rộng `pgvector`.
- **Hỗ trợ LLM & Embedding**: Kết nối linh hoạt qua LM Studio / OpenAI API.

## 📁 Cấu Trúc Dự Án

```text
rag-vault/
├── Rag-app/
│   ├── main.py          # Script chính quét vault và đồng bộ dữ liệu vào DB
│   ├── database.py      # Kết nối PostgreSQL, truy vấn & cập nhật bảng notes
│   ├── chunker.py       # Tách frontmatter, làm sạch nội dung & băm hash MD5
│   ├── embedder.py      # Tạo vector embedding qua LM Studio / OpenAI API
│   ├── loader.py        # Đọc danh sách file .md trong vault
│   ├── retriever.py     # Tìm kiếm vector tương đồng (Cosine Distance)
│   ├── AI-model.py      # Tương tác với LLM để trả lời câu hỏi
│   ├── dockerfile       # Dockerfile cho ứng dụng Python
│   └── requirements.txt # Danh sách thư viện Python
├── roadmap/             # Định hướng và lộ trình phát triển RAG Pipeline
├── docker-compose.yml   # Cấu hình container PostgreSQL + pgvector
└── README.md
```

## 🛠️ Hướng Dẫn Cài Đặt & Khởi Chạy

### 1. Yêu cầu hệ thống
- Python 3.10+
- Docker & Docker Compose
- LM Studio (hoặc OpenAI API Key)

### 2. Cấu hình môi trường (`.env`)
Tạo tệp `.env` tại thư mục gốc hoặc trong `Rag-app/.env` theo mẫu:

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=admin
DB_PASSWORD=adminpassword
DB_NAME=vector_db_service

LM_STUDIO_URL=http://localhost:1234/v1
MODEL=text-embedding-nomic-embed-text-v1.5

VAULT_PATH=path/to/your/obsidian/vault
```

### 3. Khởi chạy Database Container
```bash
docker-compose up -d
```

### 4. Cài đặt các thư viện Python
```bash
cd Rag-app
pip install -r requirements.txt
```

### 5. Chạy quét & nạp dữ liệu Vault vào Database
```bash
python main.py
```

## 📝 Roadmap

Xem thông tin chi tiết lộ trình phát triển tại [roadmap/RAG-Pipeline-Roadmap.md](roadmap/RAG-Pipeline-Roadmap.md).
