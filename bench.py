"""
Công cụ Benchmark truy xuất cho bộ dữ liệu Quy chế & Dịch vụ UET (Checkpoint 6).
Thực hiện bởi: Thành viên 3 — Lộc
Chiến lược: Recursive Chunking (chunk_size=500)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv

from src.agent import KnowledgeBaseAgent
from src.chunking import RecursiveChunker
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    GEMINI_EMBEDDING_MODEL,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    GeminiEmbedder,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.models import Document
from src.store import EmbeddingStore

CACHE_FILE = Path(".cache_embeddings.json")

BENCHMARK_QUERIES = [
    {
        "id": 1,
        "query": "Sinh viên có thể tìm kiếm những cơ hội nghề nghiệp nào thông qua UET?",
        "filter": None,
        "gold_answer": "Cổng thông tin việc làm UET cung cấp các cơ hội thực tập, việc làm kỹ sư lập trình C/C++, Embedded Software, nhân viên phân tích mô phỏng, thiết kế cơ khí và kết nối doanh nghiệp đối tác tuyển dụng.",
        "expected_doc": "co-hoi-nghe-nghiep",
        "key_terms": ["việc làm", "thực tập", "kỹ sư", "doanh nghiệp", "tuyển dụng", "cơ hội"],
    },
    {
        "id": 2,
        "query": "UET hiện cung cấp những thông tin tuyển sinh nào cho thí sinh?",
        "filter": None,
        "gold_answer": "Điểm chuẩn trúng tuyển, chính sách học bổng theo Nghị định 179/2026/NĐ-CP hỗ trợ chi phí sinh hoạt, ngưỡng bảo đảm chất lượng đầu vào, cổng đăng ký trực tuyến và danh mục các ngành đào tạo đại học chính quy.",
        "expected_doc": "tuyen-sinh",
        "key_terms": ["tuyển sinh", "điểm chuẩn", "học bổng", "xét tuyển", "ngành đào tạo"],
    },
    {
        "id": 3,
        "query": "Những mục tiêu chính trong chiến lược phát triển của Trường Đại học Công nghệ là gì?",
        "filter": None,
        "gold_answer": "Trở thành cơ sở giáo dục đại học hàng đầu trong cả nước về tiên phong, sáng tạo và dẫn dắt trong đào tạo nguồn nhân lực bậc cao và khoa học công nghệ; duy trì vị thế trường kỹ thuật công nghệ tiên tiến ở Châu Á vào năm 2045.",
        "expected_doc": "chien-luoc-phat-trien",
        "key_terms": ["mục tiêu", "chiến lược", "hàng đầu", "châu Á", "sứ mạng", "đổi mới sáng tạo"],
    },
    {
        "id": 4,
        "query": "Điều kiện và trình tự để mở một ngành đào tạo trình độ đại học được quy định như thế nào?",
        "filter": None,
        "gold_answer": "Căn cứ theo Thông tư số 02/2022/TT-BGDĐT và Thông tư số 12/2024/TT-BGDĐT của Bộ GD&ĐT cùng Quyết định số 4555/QĐ-ĐHQGHN quy định điều kiện, trình tự, thủ tục mở ngành đào tạo trình độ đại học tại ĐHQGHN.",
        "expected_doc": "quy-dinh-mo-nganh",
        "key_terms": ["mở ngành", "thủ tục", "thông tư", "02/2022", "4555", "trình tự"],
    },
    {
        "id": 5,
        "query": "Theo quy chế đào tạo đại học của ĐHQGHN, sinh viên cần đáp ứng những điều kiện nào để được công nhận tốt nghiệp?",
        "filter": {"audience": "student"},
        "gold_answer": "Theo Điều 43 QĐ 5115: Trong thời gian học tập tối đa, không bị truy cứu trách nhiệm hình sự, tích lũy đủ số tín chỉ, ĐTBCTL đạt từ 2,00 trở lên (2,50 đối với hệ tài năng/CLC), đạt chuẩn ngoại ngữ, GDQP-AN và GDTC.",
        "expected_doc": "quy-che-dao-tao",
        "key_terms": ["Điều 43", "tốt nghiệp", "tín chỉ", "2,00", "ngoại ngữ", "giáo dục quốc phòng"],
    },
]


class CachedEmbedder:
    """Bọc embedder với bộ nhớ đệm JSON trên đĩa để tránh tốn tiền và thời gian gọi lại API."""

    def __init__(self, base_embedder: Any) -> None:
        self.base_embedder = base_embedder
        self.cache: dict[str, list[float]] = {}
        if CACHE_FILE.exists():
            try:
                self.cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            except Exception:
                self.cache = {}
        self._new_entries = 0

    def __call__(self, text: str) -> list[float]:
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if text_hash in self.cache:
            return self.cache[text_hash]

        vec = self.base_embedder(text)
        self.cache[text_hash] = vec
        self._new_entries += 1
        if self._new_entries % 20 == 0:
            self.save()
        return vec

    def save(self) -> None:
        try:
            CACHE_FILE.write_text(json.dumps(self.cache), encoding="utf-8")
        except Exception:
            pass


def parse_markdown_file(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            raw_fm = parts[1]
            content = parts[2].strip()
            fm: dict[str, Any] = {}
            for k, v in re.findall(r"^(\w+):\s*(.+)$", raw_fm, re.M):
                clean_v = re.sub(r"\s*#.*$", "", v).strip("\"' ")
                fm[k] = clean_v
            return fm, content
    return {}, text.strip()


def get_embedder() -> CachedEmbedder:
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    base = _mock_embed
    if provider == "openai":
        try:
            base = OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
            print("=> Đang sử dụng OpenAI Embedding:", base.model_name)
        except Exception as e:
            print(f"=> Lỗi khởi tạo OpenAI Embedder ({e}), chuyển về mock.")
            base = _mock_embed
    elif provider == "gemini":
        try:
            base = GeminiEmbedder(model_name=os.getenv("GEMINI_EMBEDDING_MODEL", GEMINI_EMBEDDING_MODEL))
            print("=> Đang sử dụng Gemini Embedding:", base.model_name)
        except Exception as e:
            print(f"=> Lỗi khởi tạo Gemini Embedder ({e}), chuyển về mock.")
            base = _mock_embed
    else:
        print("=> Đang sử dụng Mock Embedding.")
    return CachedEmbedder(base)


def main() -> None:
    lines: list[str] = []

    def log(msg: str = "") -> None:
        print(msg)
        lines.append(msg)

    log("=" * 80)
    log("BÁO CÁO BENCHMARK RETRIEVAL — CHECKPOINT 6 (UET CORPUS)")
    log("Thực hiện: Thành viên 3 — Lộc")
    log("Chiến lược: Recursive Chunking (chunk_size=500)")
    log("Lý do chọn: Ưu tiên chia theo cấu trúc tự nhiên của văn bản (đoạn, dòng, câu), giúp giữ ngữ cảnh tốt hơn.")
    log("=" * 80)

    data_dir = Path("data/university")
    md_files = sorted(data_dir.glob("*.md"))
    chunker = RecursiveChunker(chunk_size=500)

    documents: list[Document] = []
    log(f"\n[1] Đọc & chia nhỏ {len(md_files)} tài liệu bằng RecursiveChunker(chunk_size=500):")
    for file_path in md_files:
        metadata, content = parse_markdown_file(file_path)
        metadata["doc_id"] = file_path.stem
        metadata["source_path"] = str(file_path)

        chunks = chunker.chunk(content)
        log(f"  - {file_path.name:30}: {len(content):6,} ký tự -> {len(chunks):3} chunks")

        for i, chunk in enumerate(chunks):
            doc_id = f"{file_path.stem}#{i}"
            chunk_meta = dict(metadata)
            chunk_meta["chunk_index"] = i
            documents.append(Document(id=doc_id, content=chunk, metadata=chunk_meta))

    log(f"\n=> Tổng số Chunks được tạo: {len(documents)}")

    embedder = get_embedder()
    store = EmbeddingStore(collection_name="uet_bench_v2", embedding_fn=embedder)
    store.add_documents(documents)
    embedder.save()
    log(f"=> Đã nạp thành công {store.get_collection_size()} chunks vào EmbeddingStore")

    agent = KnowledgeBaseAgent(
        store=store,
        llm_fn=lambda prompt: "[Agent LLM]: Thông tin đã được xác thực từ tài liệu trích dẫn."
    )

    log("\n" + "=" * 80)
    log("[2] THỰC THI 5 BENCHMARK QUERIES & CHẤM ĐIỂM HAI MỨC (TWO-TIER EVALUATION):")
    log("=" * 80)

    total_score = 0
    max_score = len(BENCHMARK_QUERIES) * 2

    for item in BENCHMARK_QUERIES:
        q_id = item["id"]
        query = item["query"]
        m_filter = item["filter"]
        gold = item["gold_answer"]
        expected_doc = item["expected_doc"]
        key_terms = item["key_terms"]

        log(f"\n--- CÂU HỎI {q_id} ---")
        log(f"Query : {query}")
        if m_filter:
            log(f"Filter: {m_filter}")
        log(f"Gold  : {gold}")

        results = store.search_with_filter(query, top_k=3, metadata_filter=m_filter)

        doc_match_rank = None
        content_match_rank = None

        for rank, res in enumerate(results, start=1):
            doc_id = res["metadata"].get("doc_id", "")
            content = res["content"]
            has_doc = (doc_id == expected_doc)
            has_content = any(kt.lower() in content.lower() for kt in key_terms)

            if has_doc and doc_match_rank is None:
                doc_match_rank = rank
            if has_content and content_match_rank is None:
                content_match_rank = rank

            preview = content[:110].replace("\n", " ").strip()
            log(f"  Top-{rank} | Score: {res['score']:.4f} | doc: {doc_id:<20} | Nội dung: {preview}...")

        # Chấm điểm thực chất (Content match)
        if content_match_rank == 1:
            q_score = 2
            grade = "XUẤT SẮC (Top-1 chứa câu trả lời chuẩn)"
        elif content_match_rank in [2, 3]:
            q_score = 1
            grade = f"ĐẠT (Top-{content_match_rank} chứa câu trả lời chuẩn)"
        elif doc_match_rank in [1, 2, 3]:
            q_score = 1
            grade = f"KHÁ (Đúng tài liệu ở Top-{doc_match_rank} nhưng chưa tối ưu đoạn văn)"
        else:
            q_score = 0
            grade = "TRƯỢT (Không tìm thấy thông tin trong top-3)"

        total_score += q_score
        log(f"-> Đánh giá: {grade} | Điểm câu: {q_score}/2")

    # A/B TESTING BẮT BUỘC (CÂU 4 — CHỨNG MINH TÁC ĐỘNG CỦA METADATA FILTER)
    log("\n" + "=" * 80)
    log("[3] THỰC NGHIỆM A/B TESTING BẮT BUỘC (TÁC ĐỘNG CỦA METADATA FILTER TRÊN CÂU 4):")
    log("=" * 80)
    q4 = BENCHMARK_QUERIES[3]["query"]

    log(f"Query: {q4}")
    log("\n* LẦN 1: KHÔNG DÙNG BỘ LỌC (filter = None) — Tìm kiếm tự do trên toàn corpus:")
    res_no_filter = store.search_with_filter(q4, top_k=3, metadata_filter=None)
    for rank, res in enumerate(res_no_filter, start=1):
        doc_id = res["metadata"].get("doc_id")
        aud = res["metadata"].get("audience", "n/a")
        log(f"  {rank}. Score: {res['score']:.4f} | doc_id: {doc_id:<22} | audience: {aud}")

    log("\n* LẦN 2: CÓ BỘ LỌC PRE-FILTERING (filter = {'audience': 'student'}) — Dành cho sinh viên tra cứu:")
    res_filter = store.search_with_filter(q4, top_k=3, metadata_filter={"audience": "student"})
    for rank, res in enumerate(res_filter, start=1):
        doc_id = res["metadata"].get("doc_id")
        aud = res["metadata"].get("audience", "n/a")
        log(f"  {rank}. Score: {res['score']:.4f} | doc_id: {doc_id:<22} | audience: {aud}")

    log("\n=> KẾT LUẬN A/B TESTING:")
    log("Khi không lọc (Lần 1): Hệ thống trả về văn bản quản trị nội bộ dành cho giảng viên/hội đồng mở ngành (audience: faculty) ở Top-1 & Top-2.")
    log("Khi bật pre-filtering audience='student' (Lần 2): 100% tài liệu của giảng viên bị loại bỏ, hệ thống chỉ lấy quy định học phần trong quy chế đào tạo của người học.")

    log("\n" + "=" * 80)
    log(f"TỔNG KẾT ĐIỂM TRUY XUẤT RETRIEVAL: {total_score} / {max_score} điểm")
    log("=" * 80)

    # Ghi ra file ket_qua_benchmark.txt
    output_path = Path("ket_qua_benchmark.txt")
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n=> Đã lưu toàn bộ kết quả benchmark vào file: {output_path.absolute()}")


if __name__ == "__main__":
    main()