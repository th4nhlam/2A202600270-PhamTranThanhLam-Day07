# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Phạm Trần Thanh Lâm
**Nhóm:** C4
**Ngày:** 10/04/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> *Viết 1-2 câu:*
Nghĩa là 2 câu/từ tương đồng về ngữ nghĩa

**Ví dụ HIGH similarity:**
- Sentence A: "How to reset my password?"
- Sentence B: "I forgot my password, how can I reset it?"
- Tại sao tương đồng: Cả 2 câu đều nói về việc quên mật khẩu và cách reset nó

**Ví dụ LOW similarity:**
- Sentence A: "How to reset my password?"
- Sentence B: "What is the capital of France?"
- Tại sao khác: Cả 2 câu không có liên quan gì đến nhau

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> *Viết 1-2 câu:* Vì cosine similarity không phụ thuộc vào độ dài của vector, chỉ quan tâm đến góc giữa chúng. Các vector cùng hướng nhưng khác độ lớn vẫn có thể có ý nghĩa tương đồng, điều này ảnh hưởng khi sử dụng Euclidian distance.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> *Đáp án:*   23 chunks
Steps=500-50=450  
Chunks=1+[(10000-500)/450]=1+9500/450=1+21.11=22.11=>23 chunks


**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Khi overlap tăng lên 100, số lượng chunks sẽ **tăng lên**. Điều này là do "bước nhảy" (stride) giữa các chunk (`chunk_size - overlap`) sẽ nhỏ lại (từ 450 xuống còn 400), dẫn đến việc cần nhiều chunk hơn để bao phủ cùng một lượng văn bản. Chúng ta muốn overlap nhiều hơn để đảm bảo các thông tin quan trọng nằm ở ranh giới giữa hai chunk không bị mất ngữ cảnh (context), giúp mô hình LLM có cái nhìn toàn diện hơn về thông tin bị cắt đôi.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** 
Luật/Quy tắc thương mại quốc tế — Incoterms 2020
**Tại sao nhóm chọn domain này?**
> *Viết 2-3 câu:* Incoterms 2020 là bộ quy tắc có tính pháp lý cao, nội dung dài và cấu trúc rõ theo điều khoản/rule nên phù hợp để thử retrieval theo ngữ cảnh. Domain này giúp nhóm đánh giá tốt các bài toán truy xuất như phân biệt trách nhiệm người bán/người mua, điểm chuyển rủi ro và phân bổ chi phí.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | incoterms_intro.md | ICC Publication (extracted from incorterm.md) | ~1,400 | source=icc, domain=incoterms, lang=en, section=introduction |
| 2 | incoterms_any_mode_rules.md | ICC Publication (extracted from incorterm.md) | ~1,600 | source=icc, domain=incoterms, lang=en, section=any_mode |
| 3 | incoterms_sea_rules.md | ICC Publication (extracted from incorterm.md) | ~1,200 | source=icc, domain=incoterms, lang=en, section=sea_inland |
| 4 | incoterms_obligations_ab.md | ICC Publication (extracted from incorterm.md) | ~1,000 | source=icc, domain=incoterms, lang=en, section=obligations |
| 5 | incoterms_risk_cost_focus.md | ICC Publication (extracted from incorterm.md) | ~1,300 | source=icc, domain=incoterms, lang=en, section=risk_cost |
### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| source | string | icc / team_notes | Truy vết nguồn pháp lý của thông tin |
| domain | string | incoterms | Lọc đúng domain khi chạy query nhóm |
| section | string | introduction / any_mode / sea_inland | Filter theo vùng kiến thức trong tài liệu |
| rule | string | EXW / FCA / FOB / CIF / DDP | Tăng precision cho query theo từng điều kiện giao hàng |
| lang | string | en | Đồng bộ ngôn ngữ văn bản để giảm nhiễu |
| doc_id | string | incorterm_main | Hỗ trợ quản lý/xóa tài liệu |


---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên tài liệu chính:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| incoterms_any_mode_rules.md | FixedSizeChunker (`fixed_size`) | 9 | 187.2 | Trung bình (dễ cắt giữa câu) |
| incoterms_any_mode_rules.md | SentenceChunker (`by_sentences`) | 4 | 319.0 | Tốt (giữ nguyên câu văn) |
| incoterms_any_mode_rules.md | RecursiveChunker (`recursive`) | 9 | 142.8 | Rất tốt (giữ theo heading) |

### Strategy Của Tôi

**Loại:** FixedSizeChunker (với overlap thấp)

**Mô tả cách hoạt động:**
> Chiến lược này sử dụng class `FixedSizeChunker` với `chunk_size=200` và `overlap=20`. Văn bản được cắt thành các đoạn có độ dài 200 ký tự liên tiếp nhau. Khoảng overlap 20 ký tự được thêm vào giữa các chunk để đảm bảo các từ khóa ở ranh giới giữa hai đoạn không bị mất hoàn toàn ngữ cảnh, giúp vector search vẫn có thể tìm thấy dữ liệu nếu từ khóa rơi vào điểm cắt.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Với tài liệu Incoterms, các điều khoản và định nghĩa thường súc tích. Việc sử dụng FixedSize giúp quá trình indexing diễn ra nhanh nhất có thể. Mặc dù Recursive là phương án tối ưu về mặt logic, nhưng FixedSize với overlap vừa phải vẫn đảm bảo hiệu suất truy xuất (retrieval) ổn định cho các câu hỏi ngắn về trách nhiệm người bán/mua mà không tốn công sức cấu hình separators phức tạp.

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| incoterms_any_mode_rules.md | best baseline (Recursive) | 9 | 142.8 | 9.0/10 |
| incoterms_any_mode_rules.md | **của tôi** (FixedSize + overlap) | 9 | 187.2 | 8.0/10 |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi (Lâm) | FixedSize + overlap thấp | 8.0 | Tốc độ xử lý nhanh, ổn định | Dễ mất ngữ cảnh ở ranh giới chunk |
| Hiệp | Recursive + metadata filter | 9.1 | Context mạch lạc, chính xác cao | Tốn thời gian tune separator |
| Dũng | FixedSize + overlap cao | 7.8 | Đơn giản, bao phủ từ khóa tốt | Nhiều dữ liệu dư thừa |
| Cường | SentenceChunker | 8.5 | Câu văn tự nhiên, dễ đọc | Khó xử lý các bảng biểu dài |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> Qua so sánh, lược đồ **RecursiveChunker kết hợp Metadata Filter** của Hiệp là tốt nhất cho domain Incoterms. Lý do là vì tài liệu pháp lý này có cấu trúc phân tầng cực kỳ chặt chẽ (Rule -> Gia đình quy tắc -> Điều khoản A/B). Việc dùng Recursive giúp giữ trọn vẹn các block kiến thức theo heading, trong khi metadata filter giúp thu hẹp phạm vi tìm kiếm vào đúng Rule cần tra cứu (ví dụ chỉ tìm trong EXW), loại bỏ hoàn toàn các kết quả nhiễu từ các Rule khác.


---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Sử dụng regex `re.split(r'(?<=[.!?])\s+', text)` tận dụng positive lookbehind để tách câu tại các khoảng trắng theo sau dấu câu kết thúc (.!?) để giữ lại các dấu chấm câu thay vì xóa bỏ chúng. Sau đó lặp qua list các câu, ghép lại các câu liền kề theo số lượng `max_sentences_per_chunk` và `strip()` khoảng trắng thừa trong mỗi chunk để có output gọn gàng.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Giải thuật hoạt động bằng cách nhận văn bản và mảng các ký tự phân cách (separators) sắp xếp theo mức độ ưu tiên từ lớn đến nhỏ (e.g. `\n\n`, `\n`, `. `). Nó thử `split` text bằng separator hiện tại, rồi đệ quy các phần con bằng separator tiếp theo nếu độ dài vẫn vượt quá `chunk_size`. Base case là khi chuỗi đủ ngắn dể chấp nhận (nhỏ hơn `chunk_size`) hoặc khi mảng separators rỗng thì fallback sang cắt chính xác `chunk_size` ký tự. Cuối cùng, các phần hợp lệ được gộp/merge dần lại vào một mảng `chunks` để tối đa hóa chiều dài nội dung mỗi chunk nhưng vẫn nhỏ hơn `chunk_size`.

### EmbeddingStore

**`add_documents` + `search`** — approach:
> Hàm `add_documents` sẽ trích xuất thông tin, format `metadata` (inject thêm `doc_id` bằng id nguyên bản để dễ truy vết) rồi sử dụng `self._embedding_fn` sinh list embedding và lưu toàn bộ vào Chroma collection (`ids`, `documents`, `metadatas`, `embeddings`). Hàm `search` query Chroma collection nhận được dictionary `results`. Hàm sau đó normalize các `distances` trả ra (có the là L2) thành similarity score bằng phép tính `1.0 - distances[i]`, format kết quả dưới dạng mảng các dictionary object và giới hạn theo `top_k`.

**`search_with_filter` + `delete_document`** — approach:
> Hàm `search_with_filter` áp dụng cơ chế lọc trên DB-level thông qua việc đưa `metadata_filter` vào tham số `where=` của hàm query ChromaDB (lọc diễn ra tự động trước khi xếp hạng). Hàm `delete_document` gọi hàm `delete` của collection với filter `where={"doc_id": doc_id}` để xoá gọn các chunks của văn bản tương ứng và đối chiếu `count()` thay đổi để return true.

### KnowledgeBaseAgent

**`answer`** — approach:
> Agent sử dụng instance của class `EmbeddingStore` để gọi hàm `search()` lấy danh sách top_k chunks tương đồng nhất với `question`. Đoạn code lặp qua dictionary extract các field `"content"` để append vào nhau với ngắt dòng `\n\n`. Chuỗi context rút gọn này cộng thêm prompt `question` cuối sau đó được nhét vào hàm `llm_fn(prompt)` để model tham khảo và trả lời.

### Test Results
```
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.0.3, pluggy-1.6.0 -- /home/lam/code/2A202600270-PhamTranThanhLam-Day07/.conda/bin/python3.11
cachedir: .pytest_cache
rootdir: /home/lam/code/2A202600270-PhamTranThanhLam-Day07
plugins: anyio-4.13.0
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================== 42 passed in 0.52s ==============================

```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | The seller pays for sea freight under CIF. | Under CIF terms, the seller is responsible for the cost of ocean transport. | high | 0.8319 | Đúng |
| 2 | EXW means the buyer handles all transport. | DDP requires the seller to handle all logistics and duties. | low | 0.3842 | Đúng |
| 3 | Incoterms 2020 are published by the ICC. | International Chamber of Commerce created the Incoterms rules. | high | 0.4896 | Đúng |
| 4 | The risk transfers to the buyer when goods are loaded on the ship in FOB. | What is the capital of France? | low | -0.0385 | Đúng |
| 5 | FCA can be used for any mode of transport. | FOB is strictly for sea or inland waterway transport. | low | 0.5600 | Sai |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> *Viết 2-3 câu:* Kết quả bất ngờ nhất là cặp số 5 với độ tương đồng lên tới 0.5600, mặc dù nội dung đang hướng đến sự đối lập giữa hai quy tắc khác nhau. Điều này cho thấy văn bản được biểu diễn mạnh theo các cụm từ khóa có chung ngữ cảnh như "transport", "mode", "sea", "FOB". Do đó, các embedding vector đôi khi gặp khó khăn trong việc phân biệt các câu mang sắc thái phủ định hoặc mang ý nghĩa trái ngược nhau nếu chúng dùng chung nhiều từ vựng.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | What are the obligations of the seller under EXW? | Người bán chỉ cần đặt hàng hóa dưới quyền định đoạt của người mua tại cơ sở của người bán. |
| 2 | Does CIF apply to air transport? | Không, CIF chỉ dành riêng cho vận tải biển và đường thủy nội địa. |
| 3 | Who is responsible for unloading goods at the destination under DPU? | Người bán chịu trách nhiệm và chi phí dỡ hàng tại điểm đến. |
| 4 | At what point does risk transfer from seller to buyer in FOB? | Rủi ro chuyển giao khi hàng hóa được giao lên tàu do người mua chỉ định. |
| 5 | Are Incoterms legally binding contracts on their own? | Không, các quy tắc Incoterms không phải là hợp đồng pháp lý hoàn chỉnh mà cần lồng ghép vào hợp đồng mua bán tự nhiên. |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | What are the obligations of the seller under EXW? | Incoterms 2020 - Rules for Any Mode(s) of Transport: EXW details... | 0.54 | Yes | Người bán phải sắp xếp hàng tại điểm hẹn, không chịu trách nhiệm bốc hàng. |
| 2 | Does CIF apply to air transport? | Incoterms 2020 - Sea and Inland Waterway Rules: CIF details... | 0.49 | Yes | CIF chỉ áp dụng cho vận tải biển hoặc thủy nội địa. |
| 3 | Who is responsible for unloading goods at the destination under DPU? | Incoterms 2020 - Rules for Any Mode(s) of Transport: DPU details... | 0.47 | Yes | Người bán chịu trách nhiệm dỡ hàng tại điểm đến đã thoả thuận. |
| 4 | At what point does risk transfer from seller to buyer in FOB? | Incoterms 2020 - Sea and Inland Waterway Rules: FOB details... | 0.56 | Yes | Chuyển rủi ro khi hàng đi qua lan can tàu hoặc được đặt lên tàu. |
| 5 | Are Incoterms legally binding contracts on their own? | Incoterms 2020 - Introduction Notes... | 0.39 | Yes | Incoterms không thay thế cho hợp đồng mua bán đầy đủ, nó chỉ bổ sung. |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 5 / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> *Viết 2-3 câu:* Tôi học được cách sử dụng `RecursiveChunker` từ bạn cùng nhóm với việc setup các separator theo cấp độ heading của markdown. Việc này giữ cho các điều luật không bị cắt làm đôi, giúp bảo toàn trọn vẹn ngữ cảnh của văn bản pháp lý.

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> *Viết 2-3 câu:* Nhóm bạn làm về y khoa có ý tưởng thêm metadata là "độ khó của bài báo" giúp agent có thể trả lời các mức độ học thuật chuẩn xác hơn dựa vào cách biểu diễn của query. Concept *metadata pre-filtering* này rất sáng tạo và hữu hiệu cho các domain kiến thức đa dạng.

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> *Viết 2-3 câu:* Nếu làm lại, tôi sẽ cấu hình chunk size lớn hơn kết hợp với một tỷ lệ overlap đủ sâu để phòng ngừa hiện tượng ngữ cảnh bị phân tán. Ngoài ra, tôi sẽ gán thêm các keyword/term chuyên ngành vào metadata hoặc đầu mỗi chunk để giúp Vector Database tìm kiếm chính xác hơn cho từng câu hỏi nhất định.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5/ 5 |
| Document selection | Nhóm | 10/ 10 |
| Chunking strategy | Nhóm | 13/ 15 |
| My approach | Cá nhân | 8 / 10 |
| Similarity predictions | Cá nhân | 4/ 5 |
| Results | Cá nhân | 10 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 4 / 5 |
| **Tổng** | | **84/ 100** |
