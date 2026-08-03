import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

EOS_TOKEN = "<|endoftext|>"

LM_STUDIO_URL = os.getenv("LM_STUDIO_URL").strip()
MODEL_NAME = os.getenv("MODEL").strip()

client = OpenAI(
    base_url=LM_STUDIO_URL, 
    api_key="not-needed")

def embed_document(text: str) -> list:
    if not text or not text.strip():
        return []
    response = client.embeddings.create(input=text , model=MODEL_NAME)
    return response.data[0].embedding

def embed_query(text: str) -> list:
    if not text or not text.strip():
        return []
    response = client.embeddings.create(input=text , model=MODEL_NAME)
    return response.data[0].embedding

