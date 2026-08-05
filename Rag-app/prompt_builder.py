DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful and precise assistant. Answer the user's question based strictly on the provided context.\n"
    "If the context does not contain enough information to answer the question, state clearly that you do not know "
    "based on the provided context. Do not invent or hallucinate any facts not mentioned in the context."
)

DEFAULT_RAG_TEMPLATE = """Context information is below.
---------------------
{context}
---------------------
Given the context information above and not prior knowledge, answer the user's question.

Question: {query}
Answer:"""

def format_context(retrieved_chunks: list, include_source: bool = True) -> str:
    """
    Format a list of retrieved chunks into a clean context string.

    :param retrieved_chunks: List of dicts, each containing at least 'content' and optionally 'source'.
    :param include_source: Whether to include source metadata in the formatted string.
    :return: Formatted context string.
    """
    if not retrieved_chunks:
        return "No relevant context found."

    formatted_blocks = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        content = chunk.get("content", "").strip() if isinstance(chunk, dict) else str(chunk).strip()
        source = chunk.get("source", "Unknown") if isinstance(chunk, dict) else "Unknown"

        if include_source:
            formatted_blocks.append(f"[Document {i} | Source: {source}]\n{content}")
        else:
            formatted_blocks.append(f"[Document {i}]\n{content}")

    return "\n\n".join(formatted_blocks)


def build_rag_messages(query: str, retrieved_chunks: list, system_prompt: str = None, include_source: bool = True) -> list:
    """
    Build OpenAI/LM Studio compatible chat completion messages list.

    :param query: User question string.
    :param retrieved_chunks: List of retrieved context chunks.
    :param system_prompt: Optional custom system prompt.
    :param include_source: Whether to include source file names in context.
    :return: List of message dictionaries [{'role': 'system', ...}, {'role': 'user', ...}]
    """
    sys_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
    context_str = format_context(retrieved_chunks, include_source=include_source)
    user_content = DEFAULT_RAG_TEMPLATE.format(context=context_str, query=query)

    return [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_content}
    ]


def build_rag_prompt(query: str, retrieved_chunks: list, system_prompt: str = None, include_source: bool = True) -> str:
    """
    Build a single formatted RAG prompt string.

    :param query: User question string.
    :param retrieved_chunks: List of retrieved context chunks.
    :param system_prompt: Optional custom system prompt.
    :param include_source: Whether to include source file names in context.
    :return: Full formatted prompt string.
    """
    sys_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
    context_str = format_context(retrieved_chunks, include_source=include_source)
    user_content = DEFAULT_RAG_TEMPLATE.format(context=context_str, query=query)

    return f"System: {sys_prompt}\n\n{user_content}"
