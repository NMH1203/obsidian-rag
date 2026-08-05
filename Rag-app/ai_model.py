import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://127.0.0.1:1234/v1").strip()
LLM_MODEL = os.getenv("LLM_MODEL", os.getenv("MODEL", "gemma")).strip()

client = OpenAI(
    base_url=LM_STUDIO_URL,
    api_key="not-needed"
)

def generate_answer(messages: list, model: str = None) -> str:
    """
    Gửi danh sách thông điệp (messages) tới LLM (LM Studio / OpenAI API) và trả về câu trả lời.
    """
    try:
        selected_model = model or LLM_MODEL
        response = client.chat.completions.create(
            model=selected_model,
            messages=messages,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Lỗi khi tạo câu trả lời từ AI model: {e}")
        return f"[Lỗi kết nối AI model: {e}]"
