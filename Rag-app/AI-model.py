from openai import OpenAI
import os

def build_project_context(folder_path):
    
    ignore_dirs = {
        '.git', '.vscode', '.idea',
        '__pycache__', '.pytest_cache',        
        'venv', '.venv', 'env',                
        'chroma_db', 'vector_db'               
    }
    context = ""
    
    for root, dirs, files in os.walk(folder_path):
        
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
                
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, folder_path)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                context += f"--- Bắt đầu file: {rel_path} ---\n"
                context += content + "\n"
                context += f"--- Kết thúc file: {rel_path} ---\n\n"
            except UnicodeDecodeError:
                print(f"[Bỏ qua] Không thể đọc nội dung text từ: {rel_path}")
            except Exception as e:
                print(f"[Lỗi] khi đọc {rel_path}: {e}")
                
    return context

project_path = "AI_READ"
context = build_project_context(project_path)


prompt = f"""
Đây là nội dung tài liệu mô tả code cần sửa:

{context}

Hãy phân tích và gợi ý các bước tiếp theo để sửa code của file main.py.
"""



client = OpenAI(
    base_url="http://localhost:1234/v1",  # địa chỉ LM Studio server
    api_key="not-needed"  # LM Studio không check key
)

response = client.chat.completions.create(
    model="gemma",  # tên model bạn đang load trong LM Studio
    messages=[
        {"role": "user", "content": prompt}
    ]
)

print(response.choices[0].message.content)