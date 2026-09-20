from __future__ import annotations

from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        """
        Retrieve relevant chunks from store and prompt the LLM to answer.
        """
        if self.store.get_collection_size() == 0:
            return "Kho tri thức hiện chưa có tài liệu nào."

        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy thông tin phù hợp trong kho tri thức để trả lời."

        context_blocks: list[str] = []
        for idx, r in enumerate(results, start=1):
            source = (
                r.get("metadata", {}).get("source_url")
                or r.get("metadata", {}).get("source")
                or r.get("id", f"doc_{idx}")
            )
            context_blocks.append(f"[{idx}] (Nguồn: {source})\n{r['content']}")

        context_str = "\n\n".join(context_blocks)

        prompt = f"""
Bạn là trợ lý hỏi đáp dựa trên tài liệu.

Chỉ sử dụng thông tin trong CONTEXT.
Nếu không đủ thông tin, hãy nói rõ là không tìm thấy thông tin.
Khi trả lời, trích dẫn nguồn bằng [1], [2], [3].

CONTEXT:
{context_str}

CÂU HỎI:
{question}

TRẢ LỜI:
"""

        return self.llm_fn(prompt)
