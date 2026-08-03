import re
import hashlib


def parse_frontmatter(content):
    frontmatter = ""
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            content = parts[2]
    return content.strip(), frontmatter


def chunk_by_heading(content, filename, min_length=20):
    sections = re.split(r'(?=^##\s)', content, flags=re.MULTILINE)

    chunks = []
    for section in sections:
        text = section.strip()
        if len(text) >= min_length:
            chunks.append({
                "text": text,
                "source": filename
            })

    if not chunks and len(content.strip()) >= min_length:
        chunks.append({
            "text": content.strip(),
            "source": filename
        })

    return chunks


def chunk_short_note_as_whole(content, filename, threshold_words=300):
    word_count = len(content.split())
    if word_count <= threshold_words:
        return [{"text": content.strip(), "source": filename}]
    return chunk_by_heading(content, filename)

import re

def remove_html(text):
    return re.sub(r'<.*?>', '', text)

def remove_special_char(text):
    return re.sub(r'[^\w\s]', '', text)

def tokenize(text):
    return text.split()

def clean_syntax(text):
    if not text:
        return ""

    text = str(text) 
    text = remove_html(text)
    text = remove_special_char(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def compute_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


