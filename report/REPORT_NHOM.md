# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** G49
**Thành viên:** Nguyễn Minh Đức, Đặng Hữu Cương, Trần Đức Lộc, Thân Tiến Đạt
**Ngày:** 19/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Thông tin học vụ, tuyển sinh và hỗ trợ sinh viên của Trường Đại học Công nghệ - ĐHQGHN (UET)

**Tại sao nhóm chọn chủ đề này?**
> *Nhóm lựa chọn các tài liệu công khai của Trường Đại học Công nghệ - ĐHQGHN vì chúng chứa nhiều thông tin thực tế liên quan đến sinh viên, giảng viên và hoạt động đào tạo của nhà trường. Bộ tài liệu bao gồm nhiều loại nội dung như tuyển sinh, cơ hội nghề nghiệp, quy chế đào tạo và chiến lược phát triển, phù hợp để xây dựng và đánh giá hệ thống RAG có khả năng truy xuất thông tin theo nhiều chủ đề và nhóm người dùng khác nhau.*

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|--------------------|----------------------|-----------|-----------------|
| 1 | Cơ hội nghề nghiệp | https://vieclam.uet.vnu.edu.vn/co-hoi-nghe-nghiep | Không nêu trong report cá nhân | Không nêu trong report cá nhân | `slug=co-hoi-nghe-nghiep`, `audience=student`, `domain=career-center`, `doc_type=service`, `language=vi`, `source_type=public-source` |
| 2 | Thông tin tuyển sinh | https://uet.edu.vn/tuyen-sinh/ | Không nêu trong report cá nhân | Không nêu trong report cá nhân | `slug=tuyen-sinh`, `audience=student`, `domain=admissions`, `doc_type=admission`, `language=vi`, `source_type=public-source` |
| 3 | Chiến lược phát triển | https://uet.edu.vn/chien-luoc-phat-trien/ | Không nêu trong report cá nhân | Không nêu trong report cá nhân | `slug=chien-luoc-phat-trien`, `audience=all`, `domain=admin`, `doc_type=strategy`, `language=vi`, `source_type=public-source` |
| 4 | Quy định thủ tục mở ngành đào tạo | https://uet.edu.vn/quy-dinh-dieu-kien-trinh-tu-thu-tuc-mo-nganh-dao-tao-trinh-do-dai-hoc/ | Không nêu trong report cá nhân | Không nêu trong report cá nhân | `slug=quy-dinh-mo-nganh`, `audience=faculty`, `domain=academic`, `doc_type=policy`, `language=vi`, `source_type=public-source` |
| 5 | Quy chế đào tạo đại học | https://uet.edu.vn/quy-che-dao-tao-dai-hoc-cua-dai-hoc-quoc-gia-ha-noi-theo-quyet-dinh-5115qd-dhqghn/ | Quyết định 5115/QĐ-ĐHQGHN | Không nêu trong report cá nhân | `slug=quy-che-dao-tao`, `audience=[student, faculty]`, `domain=academic`, `doc_type=policy`, `language=vi`, `source_type=public-source` |
**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|---------------------------------------------|
| `slug` | string | `tuyen-sinh` | Giúp định danh ngắn gọn từng tài liệu/chủ đề, thuận tiện khi lọc hoặc truy vết kết quả về đúng nguồn. |
| `audience` | string / list[string] | `student`, `faculty`, `[student, faculty]` | Cho phép lọc tài liệu theo nhóm người dùng, ví dụ chỉ tìm thông tin dành cho sinh viên hoặc giảng viên. |
| `domain` | string | `academic`, `admissions`, `career-center` | Giúp giới hạn phạm vi tìm kiếm theo lĩnh vực, giảm số tài liệu không liên quan trước khi similarity search. |
| `doc_type` | string | `policy`, `admission`, `service`, `strategy` | Hữu ích khi truy vấn cần một loại tài liệu cụ thể, ví dụ chỉ tìm quy định/chính sách hoặc thông tin tuyển sinh. |
| `language` | string | `vi` | Cho phép lọc theo ngôn ngữ, đặc biệt hữu ích khi hệ thống có corpus đa ngôn ngữ. |
| `source_type` | string | `public-source` | Giúp phân biệt nguồn công khai với nguồn nội bộ hoặc nguồn khác, hỗ trợ kiểm soát phạm vi và độ tin cậy của dữ liệu truy xuất. |
| `doc_id` | string | `quy-che-dao-tao` | Dùng để nhóm nhiều chunk thuộc cùng một tài liệu gốc, hỗ trợ truy vết nguồn và xoá toàn bộ chunk của một document. |
| `source_url` | string | `https://uet.edu.vn/tuyen-sinh/` | Giúp truy vết kết quả về trang nguồn gốc để người dùng kiểm chứng thông tin. |
---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| Bộ 5 tài liệu UET | FixedSizeChunker (`fixed_size`) | Không có số liệu trong report cá nhân | Không có số liệu trong report cá nhân | Có overlap nên giữ được một phần ngữ cảnh, nhưng vẫn có thể cắt gãy câu |
| Bộ 5 tài liệu UET | SentenceChunker (`by_sentences`, 3 câu/chunk) | Không có số liệu trong report cá nhân | Không có số liệu trong report cá nhân | Tốt nhất trong thử nghiệm của nhóm: giữ nguyên ranh giới câu và đạt 5/5 Top-1 |
| Bộ 5 tài liệu UET | RecursiveChunker (`recursive`) | Không có số liệu trong report cá nhân | Không có số liệu trong report cá nhân | Khá tốt: ưu tiên đoạn, dòng và câu; phụ thuộc cấu trúc xuống dòng của tài liệu |

> Các report cá nhân không ghi lại output định lượng của `ChunkingStrategyComparator().compare()`, vì vậy nhóm chỉ tổng hợp kết quả định tính và không tự suy đoán số chunk hoặc độ dài trung bình.

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Nguyễn Minh Đức**
- **Loại chiến lược:** FixedSizeChunker có overlap.
- **Mô tả & lý do chọn cho chủ đề này:** Chia theo kích thước cố định dễ kiểm soát độ dài đầu vào và overlap giúp hạn chế mất ngữ cảnh ở ranh giới chunk. Tuy nhiên, lần benchmark trong report cá nhân đã nạp nhầm corpus mẫu (`vi_retrieval_notes.md`, `rag_system_design.md`) thay vì bộ tài liệu UET, nên cả 5 truy vấn đều không lấy được chunk liên quan.

**Thành viên 2 — Đặng Hữu Cương**
- **Loại chiến lược:** SentenceChunker (`max_sentences_per_chunk=3`) kết hợp Gemini embedding.
- **Mô tả & lý do chọn:** Mỗi chunk gồm tối đa ba câu hoàn chỉnh, phù hợp với văn bản quy chế, tuyển sinh và chiến lược có nhiều mệnh đề. Chiến lược này không cắt gãy câu và đạt kết quả tốt nhất: 5/5 câu hỏi đều lấy đúng chunk ở Top-1.

**Thành viên 3 — Trần Đức Lộc**
- **Loại chiến lược:** RecursiveChunker.
- **Mô tả & lý do chọn:** Tách đệ quy theo thứ tự `\n\n`, `\n`, `. `, khoảng trắng rồi mới cắt cứng, nhờ đó ưu tiên giữ cấu trúc đoạn và câu của các tài liệu dài. Report cá nhân đã hoàn thiện phần cài đặt và 42/42 bài test, nhưng chưa ghi kết quả benchmark 5 câu hỏi chung nên chưa thể chấm điểm truy xuất.

**Thành viên 4 — Thân Tiến Đạt**
- **Loại chiến lược:** RecursiveChunker kết hợp pre-filter metadata và OpenAI `text-embedding-3-small`.
- **Mô tả & lý do chọn:** Chiến lược đệ quy tránh tạo chunk vụn bằng cách gom các mảnh nhỏ tới gần `chunk_size`; bộ lọc metadata giới hạn tập ứng viên trước khi tính similarity. Kết quả đạt 5/5 câu có chunk đúng trong Top-3, trong đó 4 câu ở Top-1 và câu tuyển sinh ở Top-2.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Minh Đức | FixedSize + overlap | 0/10 theo kết quả đã ghi | Đơn giản, độ dài chunk ổn định, có overlap | Nạp sai corpus nên không đánh giá được hiệu quả thực trên bộ UET; có thể cắt gãy câu |
| Đặng Hữu Cương | Sentence, 3 câu/chunk | 10/10 | 5/5 Top-1; giữ trọn câu, phù hợp văn bản quy định | Có thể sinh chunk quá dài/ngắn nếu độ dài câu không đều; regex dễ tách sai từ viết tắt |
| Trần Đức Lộc | Recursive | Chưa có số liệu | Giữ cấu trúc đoạn/câu, có fallback an toàn | Chưa điền bảng benchmark nên chưa so sánh định lượng được |
| Thân Tiến Đạt | Recursive + metadata pre-filter | 9/10 | 5/5 Top-3; kiểm soát đúng nhóm người dùng | Câu tuyển sinh chỉ ở Top-2; phụ thuộc metadata chính xác |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> SentenceChunker với ba câu mỗi chunk cho kết quả tốt nhất trên bộ đánh giá hiện có vì đạt 5/5 câu ở Top-1. Các tài liệu UET chủ yếu là văn bản hành chính, quy chế và thông báo; giữ nguyên ranh giới câu giúp mỗi chunk chứa một đơn vị ý nghĩa hoàn chỉnh. Tuy nhiên, trong hệ thống thực tế nên kết hợp cách chia theo câu với pre-filter metadata của Đạt để vừa bảo toàn ngữ nghĩa vừa tránh trả về tài liệu sai nhóm người dùng.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|----|-------------------------------|--------------------------|
| 1 | Sinh viên có thể tìm kiếm những cơ hội nghề nghiệp nào thông qua UET? | UET cung cấp cổng thông tin việc làm, UET Job Fair với hơn 50 doanh nghiệp, các chương trình thực tập và vị trí tuyển dụng như kỹ sư phần mềm C/C++, AI, Embedded Software và thiết kế cơ khí. | `co-hoi-nghe-nghiep#7` (kết quả Cương); `co-hoi-nghe-nghiep#0` (kết quả Đạt) |
| 2 | UET hiện cung cấp những thông tin tuyển sinh nào cho thí sinh? | UET cung cấp chỉ tiêu, phương thức xét tuyển (thi tốt nghiệp THPT, HSA/ĐGNL, SAT/ACT), ngưỡng và quy đổi điểm, điểm chuẩn, danh mục ngành, chính sách học bổng và hướng dẫn nhập học. | `tuyen-sinh#0` |
| 3 | Những mục tiêu chính trong chiến lược phát triển của Trường Đại học Công nghệ là gì? | Duy trì vị thế đại học nghiên cứu và đổi mới sáng tạo hàng đầu; nâng cao chất lượng nhân lực; tăng hợp tác Trường - Viện - Doanh nghiệp và tự chủ bền vững; hướng tới nhóm trường tiên tiến của châu Á vào năm 2045. | `chien-luoc-phat-trien#12` (kết quả Cương); `chien-luoc-phat-trien#2` (kết quả Đạt) |
| 4 | Điều kiện và trình tự để mở một ngành đào tạo trình độ đại học được quy định như thế nào? | Cơ sở đào tạo phải đáp ứng điều kiện về đội ngũ giảng viên, chương trình/giáo trình và cơ sở vật chất; sau đó xây dựng đề án, tổ chức thẩm định ở cấp khoa/trường và trình cấp có thẩm quyền của ĐHQGHN phê duyệt theo các văn bản hiện hành. | `quy-dinh-mo-nganh#0` |
| 5 | Theo quy chế đào tạo đại học của ĐHQGHN, sinh viên cần đáp ứng những điều kiện nào để được công nhận tốt nghiệp? | Sinh viên phải còn trong thời gian học tối đa, tích lũy đủ tín chỉ, đạt ĐTBCTL từ 2,00 trở lên (2,50 với chương trình tài năng/CLC), đạt chuẩn ngoại ngữ, hoàn thành GDQP-AN và GDTC, đồng thời không đang bị kỷ luật đình chỉ học tập. | Điều 43: `quy-che-dao-tao#122` (kết quả Cương); `quy-che-dao-tao#175` (kết quả Đạt) |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Cơ hội nghề nghiệp | SentenceChunker (Cương) | Có, Top-1 | Score 0.8022; chunk nói về Job Fair, thực tập và tuyển dụng |
| 2 | Thông tin tuyển sinh | SentenceChunker (Cương) | Có, Top-1 | Score 0.7263; với Đạt, chunk đúng nằm ở Top-2 do cạnh tranh từ khóa với trang việc làm |
| 3 | Mục tiêu chiến lược phát triển | SentenceChunker (Cương) | Có, Top-1 | Score 0.7797; lấy đúng mục tiêu chiến lược chung |
| 4 | Điều kiện và trình tự mở ngành | SentenceChunker (Cương) | Có, Top-1 | Score 0.8155; lấy đúng chunk về điều kiện và quy trình thẩm định |
| 5 | Điều kiện công nhận tốt nghiệp | SentenceChunker (Cương) + lọc `audience=student` | Có, Top-1 | Score 0.8290; lấy đúng Điều 43 của quy chế đào tạo |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có. Ở câu 5, lọc `audience=student` giúp loại các tài liệu quản trị dành cho giảng viên và tập trung vào quy chế áp dụng cho người học; ở câu 4 có thể dùng `audience=faculty` và `doc_type=policy` để ưu tiên tài liệu mở ngành. Kết quả của Đạt cho thấy pre-filtering đặc biệt hữu ích khi nhiều tài liệu cùng chứa các từ chung như “đào tạo”, “đại học” và “quy định”.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

- SentenceChunker với ba câu mỗi chunk đạt 5/5 câu hỏi ở Top-1 vì giữ nguyên các mệnh đề trong văn bản hành chính và quy chế.
- Embedding thật (Gemini/OpenAI) nhận biết các cách diễn đạt đồng nghĩa tốt hơn nhiều so với MockEmbedder dùng hash, vốn có thể cho điểm âm ngay cả khi hai câu cùng nghĩa.
- Chất lượng retrieval phụ thuộc trước hết vào việc nạp đúng corpus; trường hợp của Đức cho thấy một pipeline chạy đúng kỹ thuật vẫn thất bại hoàn toàn nếu knowledge base không chứa tài liệu UET.
- Metadata pre-filter giúp tránh lẫn tài liệu dành cho sinh viên với tài liệu dành cho giảng viên/cán bộ.

**Bài học rút ra khi so sánh trong nhóm:**
> Với cùng câu hỏi, cách chia theo câu đưa thông tin đầy đủ vào một chunk nên đạt thứ hạng cao và ổn định hơn cách cắt cố định. RecursiveChunker giữ cấu trúc tốt nhưng còn phụ thuộc cách tài liệu xuống dòng, còn FixedSizeChunker có nguy cơ tách điều kiện khỏi kết luận. Ngoài chunking, embedding model, corpus được nạp và metadata cũng ảnh hưởng trực tiếp đến kết quả nên không thể đánh giá chiến lược chunking một cách tách rời.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ chuẩn hóa pipeline nạp dữ liệu để kiểm tra đúng năm tài liệu UET trước khi benchmark, lưu lại `retrieved_at`, phiên bản và số ký tự của từng tài liệu. Nhóm cũng sẽ chạy tự động cả ba chiến lược trên cùng embedding model và cùng bộ câu hỏi, ghi lại số chunk, độ dài trung bình, Top-1/Top-3 và MRR; sau đó chọn SentenceChunker kết hợp metadata pre-filter làm cấu hình chính.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 12 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 4 / 5 |
| **Tổng phần nhóm** | **35 / 40** |
