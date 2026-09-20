# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Đức Lộc
**Nhóm:** G49
**Ngày:** 19/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (High cosine similarity) nghĩa là hai văn bản có góc giữa hai vectơ đại diện rất nhỏ, phản ánh việc chúng có nội dung hoặc ngữ nghĩa rất giống nhau. Giá trị này tiến càng gần 1 thì mức độ tương đồng giữa hai văn bản càng cao.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Sinh viên đăng ký học phần trong cổng học vụ theo lịch của từng học kỳ."
- Câu B: "Khi gặp lỗi trùng lịch, sinh viên điều chỉnh lớp học phần trước thời hạn điều chỉnh được công bố."
- Tại sao tương đồng: Cả hai cùng thuộc nội dung đăng ký học phần trong `data/university/course-registration.md`, nên embedding của chúng đều tập trung vào hoạt động học vụ của sinh viên.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Sinh viên đăng ký học phần trong cổng học vụ theo lịch của từng học kỳ."
- Câu B: "Trường Đại học Công nghệ tập trung phát triển các nhóm nghiên cứu quốc tế và đổi mới sáng tạo."
- Tại sao khác: Một câu nói về quy trình đăng ký học phần, câu kia nói về chiến lược phát triển trường, nên hai nội dung thuộc chủ đề khác nhau và vector của chúng lệch hướng.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Với văn bản, điều quan trọng là hai embedding có cùng hướng nghĩa hay không, chứ không phải vector có dài bao nhiêu. Cosine similarity đo góc giữa hai vector nên rất phù hợp cho ngữ nghĩa; Euclidean distance lại nhạy cảm hơn với độ lớn của vector và ít phản ánh ý nghĩa ngữ văn bản hơn.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Công thức: số chunks = ceil((N - overlap) / (chunk_size - overlap))
>
> Với N = 10,000, overlap = 50, chunk_size = 500:
>
> số chunks = ceil((10,000 - 50) / (500 - 50)) = ceil(9,950 / 450) = ceil(22.11) = 23 chunks
>
> *Đáp án:* 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng từ 50 lên 100, bước trượt giảm từ 450 xuống 400, nên số chunk tăng thành ceil((10,000 - 100)/(500 - 100)) = ceil(9,900/400) = 25 chunks. Trong dự án này, overlap lớn giúp giữ mạch ngữ nghĩa giữa các đoạn trong `quy-che-dao-tao.md`, tránh mất ngữ cảnh ở giữa các mục như “Điều 4”, “Điều 5”, “Điều 21”.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng regex `(?<=[.!?])(?:\s+|\n)` để tách văn bản theo các dấu chấm, chấm than, chấm hỏi và khoảng trắng hoặc xuống dòng. Cách này rất hợp với tài liệu quy chế như `quy-che-dao-tao.md`, vì các câu trong tài liệu đều kết thúc bằng dấu câu rõ ràng, và sau đó tôi bỏ các câu rỗng để tránh chunk thừa khoảng trắng hoặc chunk quá nhỏ không mang nội dung.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán hoạt động theo kiểu đệ quy: thử tách theo các separator theo độ ưu tiên `\n\n`, `\n`, `. `, ` `, cuối cùng là rỗng `""` nếu không còn cách chia hợp lý. Base case là khi đoạn văn bản còn lại có độ dài nhỏ hơn hoặc bằng `chunk_size`, lúc đó tôi trả về đoạn đó; nếu không còn separator nào thì cắt cố định theo `chunk_size` để tránh vòng lặp hoặc tạo ra các chunk quá ngắn như “khỏe”, “phó”, “số”. Đây là điều rất quan trọng khi xử lý văn bản dài trong quy chế đào tạo và các chính sách học vụ.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` trong corpus được chuyển thành record có `id`, `content`, `metadata` và embedding tương ứng. Trong dự án, metadata gồm `doc_id`, `source_file`, `audience`, `department`, ...; khi thêm tài liệu, tôi tính embedding cho từng chunk rồi lưu vào bộ nhớ để truy xuất nhanh mà không cần cơ sở dữ liệu ngoài. Search sử dụng tích vô hướng giữa query vector và từng record vector để xếp hạng điểm tương đồng.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Tôi thực hiện lọc trước rồi mới tính similarity: chỉ xét các record phù hợp `metadata_filter` như `{ "audience": "student" }` trước khi xếp hạng. Điều này rất quan trọng cho câu hỏi như “Khi sinh viên gặp lỗi trùng lịch…” vì nếu lọc sau thì các chunk không thuộc sinh viên nhưng có score cao cũng có thể lấn át kết quả đúng. Với `delete_document`, tôi xóa tất cả chunk có `metadata["doc_id"] == doc_id`, nên khi cần loại bỏ toàn bộ nội dung của một tài liệu gốc như `course-registration`, toàn bộ chunk liên quan đều biến mất đồng loạt.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `KnowledgeBaseAgent.answer` đầu tiên gọi `store.search(question, top_k)` để lấy các chunk phù hợp nhất, sau đó tạo prompt theo kiểu RAG: phần `CONTEXT` nằm trước câu hỏi và mỗi đoạn được đánh nhãn `[1]`, `[2]`, ... để LLM có thể trích dẫn nguồn. Trong dự án của chúng tôi, điều này giúp trả lời câu hỏi về tín chỉ, thời hạn đăng ký, hay quy chế đào tạo dựa trên chunk thực tế trong `quy-che-dao-tao.md` và `course-registration.md`, thay vì đoán theo kinh nghiệm hoặc trả lời mơ hồ.

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

(.venv) PS C:\Users\PC\Documents\Downloads\K4-L3A-Data-Foundations> pytest tests/ -v
========================================================== test session starts ==========================================================
platform win32 -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\PC\Documents\Downloads\K4-L3A-Data-Foundations\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\PC\Documents\Downloads\K4-L3A-Data-Foundations
collected 42 items                                                                                                                       

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                              [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                                       [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                                [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                                 [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                                      [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                                      [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                            [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                             [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                           [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                             [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                             [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                                        [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                                    [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                              [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                                     [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                                         [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                                   [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                                         [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                             [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                               [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                                 [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                                       [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                            [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                              [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                                  [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                               [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                                        [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                                       [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                                  [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                              [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                                         [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                             [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                                   [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                             [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED                          [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                                        [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                                       [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                           [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                                      [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                               [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED                     [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED                         [100%]

======================================= 42 passed in 0.30s ================================================
**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 |Sinh viên có thể tìm kiếm những cơ hội nghề nghiệp nào thông qua UET? |Cổng thông tin việc làm UET cung cấp các cơ hội thực tập, việc làm kỹ sư... | cao |0.6263 |Đúng |
| 2 |UET hiện cung cấp những thông tin tuyển sinh nào cho thí sinh? |Điểm chuẩn trúng tuyển, chính sách học bổng, ngưỡng bảo đảm chất lượng... | cao |0.5607 |Đúng |
| 3 |Những mục tiêu chính trong chiến lược phát triển của Trường Đại học Công nghệ là gì? |Trở thành cơ sở giáo dục đại học hàng đầu trong cả nước về tiên phong, sáng tạo... | cao | 0.6135 | Đúng |
| 4 |Điều kiện và trình tự để mở một ngành đào tạo trình độ đại học được quy định như thế nào? |Căn cứ theo Thông tư số 02/2022/TT-BGDĐT và Thông tư số 12/2024/TT-BGDĐT... | cao | 0.7094 | Đúng |
| 5 | Theo quy chế đào tạo đại học của ĐHQGHN, sinh viên cần đáp ứng những điều kiện nào để được công nhận tốt nghiệp? |Theo Điều 43 QĐ 5115: Trong thời gian học tập tối đa, không bị truy cứu trách nhiệm... | cao | 0.5474 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là ở Câu 5 khi điểm Cosine Similarity của đoạn thông tin đúng chỉ đạt ~0.5474 và bị các đoạn thông tin nhập học/xét tuyển vượt mặt khi áp bộ lọc metadata. Điều này phản ánh rằng mô hình embedding dựa rất nhiều vào ngữ cảnh từ vựng chung (các từ như "quy chế", "đại học", "điều kiện") thay vì hiểu sâu logic về giai đoạn "tốt nghiệp" hay "nhập học". Do đó, việc thiết kế chiến lược chunking chuẩn xác kết hợp Metadata Filtering hợp lý là vô cùng quan trọng để định hướng đúng cho Embedding Model.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Sinh viên có thể tìm kiếm những cơ hội nghề nghiệp nào thông qua UET? | Hỗ trợ sinh viên tạo CV điện tử theo tiêu chuẩn, kết nối thông tin tuyển sinh/việc làm... (`co-hoi-nghe-nghiep`) | 0.6263 | Có | [Agent LLM]: Thông tin đã được xác thực từ tài liệu trích dẫn. |
| 2 | UET hiện cung cấp những thông tin tuyển sinh nào cho thí sinh? | Khai báo hồ sơ và nhận giấy báo nhập học qua cổng thông tin... (`tuyen-sinh`) | 0.5607 | Có | [Agent LLM]: Thông tin đã được xác thực từ tài liệu trích dẫn. |
| 3 | Những mục tiêu chính trong chiến lược phát triển của Trường Đại học Công nghệ là gì? | Nhân tố mới, quan trọng là cơ sở để xây dựng Chiến lược phát triển của Trường... (`chien-luoc-phat-trien`) | 0.6135 | Có | [Agent LLM]: Thông tin đã được xác thực từ tài liệu trích dẫn. |
| 4 | Điều kiện và trình tự để mở một ngành đào tạo trình độ đại học được quy định như thế nào? | Quy định điều kiện, trình tự, thủ tục mở ngành đào tạo trình độ Đại học... (`quy-dinh-mo-nganh`) | 0.7094 | Có | [Agent LLM]: Thông tin đã được xác thực từ tài liệu trích dẫn. |
| 5 | Theo quy chế đào tạo đại học của ĐHQGHN, sinh viên cần đáp ứng những điều kiện nào để được công nhận tốt nghiệp? | Phương thức xét tuyển thẳng và ưu tiên xét tuyển theo Quy chế tuyển sinh... (`tuyen-sinh`) | 0.5860 | Không (Lệch mục tiêu) | [Agent LLM]: Thông tin đã được xác thực từ tài liệu trích dẫn. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Qua buổi demo, điều giá trị nhất tôi học được là kỹ thuật Semantic Chunking kết hợp với Parent-Child Retriever để giữ trọn vẹn ngữ cảnh của đoạn văn dài mà không bị mất mát thông tin khi tính vector embedding. Ngoài ra, việc bổ sung bộ lọc Metadata Filter đa cấp (multivalue filter) giúp khắc phục triệt để tình trạng trôi ngữ cảnh khi câu hỏi chạm vào các phần tài liệu có từ khóa gần tương tự nhau.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) |30  / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5/ 5 |
| Kết quả truy xuất của tôi (Competition Results) |9 / 10 |
| **Tổng phần cá nhân** | 59/ 60** |
