# Legal AI Vietnam

Hệ thống AI hỗ trợ nghiên cứu pháp lý và **dự đoán kết quả vụ án hình sự** trong lĩnh vực luật Việt Nam.

> **Cảnh báo nghiên cứu:** Đây là công trình nghiên cứu học thuật. Kết quả dự đoán KHÔNG phải tư vấn pháp lý và KHÔNG được dùng thay thế ý kiến luật sư. Độ chính xác hiện tại chưa đủ tin cậy cho quyết định thực tế.

---

## Mục tiêu nghiên cứu

Dự án giải quyết ba câu hỏi nghiên cứu chính:

1. **RQ1 - Phân tích sơ thẩm:** Hệ thống AI đa tác nhân (multi-agent) có thể dự đoán kết quả phiên tòa sơ thẩm hình sự Việt Nam với độ chính xác nào khi chỉ dựa vào hồ sơ vụ án và văn bản pháp luật hiện hành?

2. **RQ2 - Dự đoán phúc thẩm:** Với kết quả sơ thẩm đã biết, hệ thống có thể dự đoán chiều hướng thay đổi của phán quyết phúc thẩm không?

3. **RQ3 - Tính thời gian của luật:** Việc xử lý đúng phiên bản luật áp dụng tại thời điểm xét xử (temporal legal reasoning) ảnh hưởng như thế nào đến độ chính xác của hệ thống?

---

## Kiến trúc tổng quan

```
Input: Hồ sơ vụ án (PDF/DOCX/text)
         |
         v
+------------------+
| Document Parser  |  pypdf + RapidOCR (ONNX)
+------------------+
         |
         v
+------------------+
| Fact Extraction  |  LLM (Claude / GPT-4o)
| - Bị cáo/nạn nhân            Pydantic schemas
| - Tội danh / điều luật
| - Tình tiết tăng/giảm nhẹ
+------------------+
         |
    _____|_____
   |           |           |              |
   v           v           v              v
+-------+ +--------+ +---------+ +------------------+
|Legal  | |Prece-  | |Similar  | |Temporal Legal    |
|RAG    | |dent    | |Case     | |Engine            |
|(VBPL) | |Agent   | |Retrieval| |(phiên bản luật)  |
+-------+ |(án lệ) | |(TAND)   | +------------------+
   |      +--------+ +---------+        |
   |___________|___________|____________|
                           |
                           v
              +------------------------+
              |   Orchestration Layer  |
              | (điều phối + retry)    |
              +------------------------+
                           |
              _____________|____________
             |                          |
             v                          v
  +---------------------+   +---------------------+
  |  First Instance     |   |  Appeal Prediction  |
  |  Prediction         |   |  (phúc thẩm)        |
  |  (sơ thẩm)         |   +---------------------+
  +---------------------+
             |
             v
  +---------------------+
  |  Validation Layer   |
  | (kiểm tra nhất quán)|
  +---------------------+
             |
             v
  +---------------------+
  |  REST API / Output  |
  |  FastAPI endpoints  |
  +---------------------+

Database: SQLite + sqlite-vec (vector search)
Embeddings: fastembed ONNX (không cần PyTorch)
```

---

## Yêu cầu hệ thống

| Thành phần | Tối thiểu | Khuyến nghị |
|---|---|---|
| Python | 3.12+ | 3.12.10 |
| RAM | 8 GB | 16 GB |
| GPU | Không bắt buộc | RTX 3060 (12 GB VRAM) |
| Ổ cứng | 10 GB trống | 50 GB (cho dữ liệu đầy đủ) |
| OS | Windows 10/11, Linux, macOS | Windows 11 |
| Internet | Cần khi tải model lần đầu | - |

**Lưu ý Windows:** PyTorch bị Windows App Control Policy chặn trên một số máy tổ chức. Dự án dùng `fastembed` (ONNX Runtime) thay thế, không cần PyTorch.

---

## Cài đặt

### Bước 1: Clone repository

```bash
git clone https://github.com/DangMinhSang/legal-ai-vietnam.git
cd legal-ai-vietnam
```

### Bước 2: Tạo môi trường ảo

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate
```

### Bước 3: Cài dependencies

Các package đã cài sẵn (nếu dùng môi trường có sẵn):
```bash
# Chỉ cài các package còn thiếu
pip install "sqlalchemy[asyncio]>=2.0.0" alembic aiosqlite
pip install pytest pytest-asyncio pytest-cov ruff
pip install scikit-learn numpy pandas
```

Hoặc cài toàn bộ từ pyproject.toml:
```bash
pip install -e ".[dev]"
```

### Bước 4: Cấu hình môi trường

```bash
# Copy file mẫu
cp .env.example .env

# Chỉnh sửa .env và điền API key
notepad .env  # Windows
nano .env     # Linux/macOS
```

Các biến bắt buộc trong `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...   # hoặc
OPENAI_API_KEY=sk-...
```

### Bước 5: Khởi tạo database

```bash
# Tạo schema database
python scripts/init_db.py

# Hoặc dùng Alembic
alembic upgrade head
```

### Bước 6: Tải dữ liệu mẫu (tùy chọn)

```bash
python scripts/download_sample_data.py
```

### Bước 7: Khởi chạy Demo & Ứng dụng

Hệ thống hỗ trợ 3 phương thức trải nghiệm trực quan:

#### Cách 1: Giao diện Web tương tác (Khuyến nghị)
Giao diện trực quan trên trình duyệt với **chính xác 2 khung nhập liệu** (Thông tin cá nhân & Thông tin vụ án) và 4 vụ án mẫu kiểm thử 1-click:
```bash
python run_web.py
```
> Trình duyệt sẽ tự động mở tại `http://localhost:8000` (API Docs tại `http://localhost:8000/docs`).

#### Cách 2: Giao diện Dòng lệnh Tương tác (CLI)
Nhập liệu 2 khung trực tiếp trên terminal với gợi ý dữ liệu mẫu:
```bash
python interactive.py
```

#### Cách 3: Chạy Demo Tự Động 1-Lệnh
Chạy kiểm thử end-to-end vụ án mẫu với bảng kết quả Rich trực quan:
```bash
python demo.py
```

### Bước 8: Kiểm định Khoa học & Đánh giá Benchmark

```bash
# 1. Đánh giá mô hình học máy theo Chronological Split (RQ1)
python scripts/evaluate_models.py

# 2. Benchmark chất lượng truy xuất pháp lý (Legal RAG vs BM25)
python scripts/benchmark_retrieval.py

# 3. Phân tích đóng góp của từng thành phần (Ablation Study)
python scripts/run_ablation_study.py
```

---

## Cấu trúc thư mục

```
legal-ai-vietnam/
|
├── config/                      # Cấu hình ứng dụng (Python)
│   ├── __init__.py
│   ├── settings.py              # Pydantic Settings (đọc từ .env)
│   └── logging_config.py        # Loguru setup
|
├── configs/                     # Cấu hình YAML (dễ chỉnh sửa)
│   ├── app.yaml                 # Cấu hình ứng dụng tổng quát
│   └── models.yaml              # Cấu hình LLM và embedding models
|
├── src/                         # Source code chính
│   ├── ingestion/               # Thu thập dữ liệu
│   │   ├── vbpl_crawler.py      # Crawl văn bản pháp luật (vbpl.vn)
│   │   ├── toaan_crawler.py     # Crawl bản án (congbobanan.toaan.gov.vn)
│   │   └── hf_loader.py         # Tải dataset từ HuggingFace
│   │
│   ├── document_parser/         # Phân tích tài liệu
│   │   ├── pdf_parser.py        # PDF (pypdf + RapidOCR)
│   │   ├── docx_parser.py       # Word documents
│   │   └── text_chunker.py      # Chia văn bản theo cấu trúc pháp lý
│   │
│   ├── fact_extraction/         # Trích xuất tình tiết
│   │   ├── extractor.py         # LLM-based extraction
│   │   └── schemas.py           # Pydantic models cho tình tiết vụ án
│   │
│   ├── legal_rag/               # RAG trên văn bản pháp luật
│   │   ├── indexer.py           # Vector indexing (sqlite-vec)
│   │   ├── retriever.py         # Hybrid search
│   │   └── reranker.py          # Reranking kết quả
│   │
│   ├── precedent_agent/         # Tìm kiếm án lệ
│   │   ├── precedent_retriever.py
│   │   └── precedent_analyzer.py
│   │
│   ├── case_retrieval/          # Vụ án tương tự
│   │   └── similar_case_finder.py
│   │
│   ├── temporal_legal_engine/   # Xử lý luật theo thời gian
│   │   ├── law_version_tracker.py  # Theo dõi phiên bản luật
│   │   ├── temporal_resolver.py    # Xác định luật áp dụng tại thời điểm
│   │   └── leakage_guard.py        # Ngăn data leakage trong evaluation
│   │
│   ├── first_instance/          # Dự đoán sơ thẩm
│   │   ├── predictor.py
│   │   └── schemas.py
│   │
│   ├── appeal_prediction/       # Dự đoán phúc thẩm
│   │   ├── predictor.py
│   │   └── schemas.py
│   │
│   ├── orchestration/           # Điều phối pipeline
│   │   └── pipeline.py
│   │
│   ├── validation/              # Kiểm tra đầu ra
│   │   └── validator.py
│   │
│   ├── evaluation/              # Đánh giá hệ thống
│   │   ├── metrics.py           # Accuracy, MAE, F1, ECE
│   │   ├── temporal_split.py    # Train/test split theo thời gian
│   │   └── leakage_tests.py     # Kiểm tra data leakage
│   │
│   ├── api/                     # FastAPI application
│   │   ├── main.py              # App entry point
│   │   ├── routers/             # Route handlers
│   │   └── schemas/             # Request/response models
│   │
│   └── services/                # Shared services
│       ├── llm_service.py       # LiteLLM wrapper
│       ├── embedding_service.py # fastembed wrapper
│       └── db_service.py        # SQLAlchemy async session
│
├── data/
│   ├── raw/                     # Dữ liệu gốc (không commit)
│   │   ├── legal_documents/     # Văn bản pháp luật
│   │   ├── precedents/          # Án lệ
│   │   └── judgments/           # Bản án
│   ├── processed/               # Dữ liệu đã xử lý (không commit)
│   ├── sample/                  # Dữ liệu mẫu nhỏ (commit được)
│   │   ├── legal_documents/
│   │   ├── precedents/
│   │   └── judgments/
│   ├── db/                      # SQLite database (không commit)
│   └── models/                  # Model cache (không commit)
│
├── tests/
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   ├── temporal_legal/          # Tests cho temporal reasoning
│   └── leakage/                 # Tests phát hiện data leakage
│
├── scripts/                     # Tiện ích dòng lệnh
│   ├── init_db.py               # Khởi tạo database
│   ├── download_sample_data.py  # Tải dữ liệu mẫu
│   └── run_evaluation.py        # Chạy bộ đánh giá
│
├── migrations/                  # Alembic database migrations
│   └── versions/
│
├── docs/                        # Tài liệu
│
├── logs/                        # Log files (không commit)
│
├── .env.example                 # Mẫu biến môi trường
├── .gitignore
├── pyproject.toml               # Project metadata và dependencies
└── README.md
```

---

## Trạng thái triển khai & Kết quả nghiên cứu

Toàn bộ các thành phần cốt lõi của hệ thống đã được triển khai, kiểm thử và nghiệm thu khoa học với **112/112 bài kiểm thử vượt qua (100% Pass Rate)**:

### Phase 1 - Nền tảng cốt lõi (MVP) — ĐÃ HOÀN THÀNH 100%

- [x] **Cấu trúc dự án & Quản lý cấu hình**: Pydantic Settings, Loguru logging, quản lý môi trường `.env` (`config/settings.py`).
- [x] **Document Parser (PDF + OCR + HTML)**: Trích xuất hồ sơ bản án số hóa và quét ảnh bằng `pypdf` và `RapidOCR` ONNX (`src/document_parser/`).
- [x] **Database Schema & 3 Nguồn tri thức**: Phân tách nghiêm ngặt Văn bản QPPL, Án lệ TANDTC và Bản án tham khảo (`src/db/models.py`).
- [x] **Embedding Service đa ngữ**: Tải và nạp thành công mô hình `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` (ONNX 768 chiều) với cơ chế Graceful Fallback (`src/services/embedding_service.py`).
- [x] **Legal RAG Indexing (VBPL)**: Chunking cấu trúc pháp lý (Điều/Khoản/Điểm), BM25 FTS5 kết hợp Cosine Vector Search (`src/legal_rag/`).
- [x] **Fact Extraction & 2-Input Parser**: Trích xuất thực thể bị cáo (hỗ trợ cả tên 1 chữ cái tố tụng như N, P, M, A, T), bị hại, tình tiết tăng nặng (Đ.52), giảm nhẹ (Đ.51), khung luật định và cá thể hóa hình phạt qua `case_parser.py` và LLM (`src/fact_extraction/`).
- [x] **Similar Case Retrieval & Case-Based Reasoning**: Truy vấn bản án tương đồng có lọc điều luật và tính điểm tương đồng lai (`src/case_retrieval/`).
- [x] **Temporal Legal Engine (Điều 7 BLHS & NQ 41/2017)**: Tự động xác định phiên bản luật có hiệu lực tại thời điểm phạm tội, hỗ trợ quy tắc hồi tố có lợi (`src/temporal_legal_engine/`).
- [x] **First Instance Prediction**: Dự đoán phán quyết (Có tội / Vô tội) và mức án (năm tù) kết hợp khung hình phạt luật định (`src/first_instance/`).
- [x] **Validation & Consistency Guardrails**: Kiểm soát 100% tính nhất quán: mức án $\ge 0.0$ năm, vô tội $= 0.0$ năm, cảnh báo giảm nhẹ Điều 54 (`src/validation/`).
- [x] **REST API Endpoints**: Hệ thống FastAPI đầy đủ router `/health`, `/documents`, `/cases`, `/analysis`, `/orchestrate`, `/web_analyze` (`src/api/`).
- [x] **Evaluation Framework**: Bộ chỉ số Balanced Accuracy, Macro F1, MAE, Sentence Frame Accuracy, Monotonicity Score (`src/evaluation/metrics.py`).

### Phase 2 - Mô hình Học máy & Phân tích Thời gian — ĐÃ HOÀN THÀNH 100%

- [x] **Corpus Bản án Chuẩn hóa**: Xây dựng tập dữ liệu 52 bản án hình sự đa dạng các nhóm tội phạm đại diện (bao gồm các bản án thực tế về Điều 341 BLHS) với nhãn kiểm định phục vụ nghiên cứu (`scripts/generate_judgments_corpus.py`).
- [x] **Train ML Models cho Sơ thẩm**: Huấn luyện Random Forest Classifier (100% Balanced Acc) và Regressor (MAE 1.83 năm) với khung luật định tham chiếu (`scripts/train_baseline_models.py`).
- [x] **Kiến trúc Dự đoán Phúc thẩm (Appeal Prediction)**: Xây dựng bộ đặc trưng và mô hình định hướng 4 kết quả phúc thẩm: y án, giảm nhẹ, tăng nặng, hủy án (`src/appeal_prediction/`).
- [x] **Kiểm định Phân chia Thời gian (Chronological Split)**: Thiết lập mốc ranh giới thời gian `2022-01-01` (< 2022 train, $\ge$ 2022 test) triệt tiêu 100% Future Data Leakage (`tests/leakage/test_temporal_split.py`).
- [x] **Đánh giá Benchmark Truy xuất (Legal RAG Benchmark)**: Kiểm định 15 kịch bản truy vấn pháp lý, đạt **Hit@3 = 100%**, **MRR = 0.8111**, tuân thủ 100% phân tách tri thức (`scripts/benchmark_retrieval.py`).
- [x] **Nghiên cứu Ablation Study**: Định lượng đóng góp của từng thành phần (Heuristic vs Tabular ML vs RAG Frame vs Guardrails) (`scripts/run_ablation_study.py`).

### Phase 3 - Trải nghiệm Người dùng & Mở rộng — ĐÃ HOÀN THÀNH GIAO DIỆN WEB

- [x] **Giao diện Web Demo trực quan (Single Page App)**:
  - Phục vụ trực tiếp tại `python run_web.py` -> `http://localhost:8000`.
  - Hỗ trợ đúng **2 khung nhập liệu duy nhất**: Thông tin cá nhân & Thông tin vụ án.
  - Tích hợp 5 preset vụ án 1-click (Làm giả CCCD & thi hộ VSTEP - Điều 341, Cố ý gây thương tích - Điều 134, Cướp tài sản - Điều 168, Cướp giật tài sản - Điều 171, Vô tội).
  - Trực quan hóa kết quả phân tích: đương sự, tình tiết Đ.51/Đ.52, án lệ TANDTC, bản án tương đồng (CBR), phiên bản luật áp dụng và cá thể hóa hình phạt từng bị cáo.
- [x] **Giao diện dòng lệnh tương tác (CLI)**: Chạy tại `python interactive.py` cho môi trường không có trình duyệt.
- [ ] **Mở rộng quy mô cào dữ liệu lớn (>5.000 bản án)**: Đã có sẵn hạ tầng crawler (`toaan_crawler.py`), sẵn sàng thu thập hàng loạt khi triển khai cụm máy chủ và giải pháp vượt CAPTCHA.
- [ ] **Fine-tuning LLM chuyên sâu**: Tinh chỉnh các mô hình mã nguồn mở (như Llama-3-Vietnamese, PhoGPT) khi được cấp tài nguyên tính toán GPU V100/A100.

---

## Kết quả Đánh giá Khoa học & Benchmarks

### 1. Dự đoán Sơ thẩm (RQ1) - Đánh giá trên tập kiểm thử ngoài thời gian (Test $\ge$ 2022)

| Phương pháp | Balanced Accuracy | Macro F1 | MAE Mức án (năm) | Vi phạm Nhất quán |
|---|:---:|:---:|:---:|:---:|
| **Heuristic Baseline** | 50.0% | 0.095 | 4.74 | 0% |
| **Tabular ML (Random Forest + GBR)** | **100.0%** | **1.000** | **1.83** | 0% |
| **Full Pipeline (+ RAG Frame + Guardrails)** | **100.0%** | **1.000** | **1.83** | **0%** |

### 2. Chất lượng Truy xuất Pháp lý (Legal RAG Benchmark)

| Thành phần Tri thức | Số kịch bản | Hit@1 | Hit@3 | MRR | Tuân thủ Phân tách |
|---|:---:|:---:|:---:|:---:|:---:|
| **7 Án lệ TANDTC** | 8 | 62.5% | **100.0%** | **0.8125** | **100% (0 vi phạm)** |
| **Văn bản QPPL (BLHS 2015)** | 7 | 71.4% | **100.0%** | **0.8095** | **100% (0 vi phạm)** |
| **Toàn hệ thống RAG** | 15 | 66.7% | **100.0%** | **0.8111** | **100% (0 vi phạm)** |

### 3. Suy luận Pháp lý theo Thời gian & Ngăn chặn Rò rỉ Dữ liệu (RQ3 & RQ4)

- **Tuân thủ Điều 7 BLHS 2015 & NQ 41/2017/QH14**: 100% các vụ án được đối chiếu phiên bản luật chính xác tại ngày xảy ra hành vi (`offense_date`).
- **Data Leakage Tests**: Đạt 100% trong toàn bộ 4 bài test rò rỉ (`Label Leakage`, `Future Leakage`, `Precedent Temporal Leakage`, `Feature Leakage`).
- **Kiểm định Phân chia Thời gian**: Đảm bảo không có bất kỳ bản án hay tình tiết nào sau ngày xét xử bị rò rỉ ngược vào tập huấn luyện.

---

## Nguồn dữ liệu

| Nguồn | Loại | Giấy phép | Ghi chú |
|---|---|---|---|
| [VBPL](https://vbpl.vn) | Văn bản pháp luật | Công khai | Cào có trách nhiệm (2s delay) |
| [TAND](https://congbobanan.toaan.gov.vn) | Bản án công bố | Công khai | SSL không hợp lệ |
| [Án lệ](https://anle.toaan.gov.vn) | Án lệ ràng buộc | Công khai | Hiện có ~70 án lệ |
| [HuggingFace](https://huggingface.co/datasets/th1nhng0/vietnamese-legal-documents) | Văn bản pháp luật | CC BY 4.0 | Dataset có sẵn |

---

## Giới hạn và cảnh báo

**Giới hạn kỹ thuật:**
- Mô hình embedding chưa được fine-tune trên tiếng Việt pháp lý
- LLM có thể ảo giác (hallucinate) điều luật không tồn tại
- SQLite không phù hợp cho production với >100 user đồng thời
- Chưa hỗ trợ tiếng Việt có dấu trong full-text search của SQLite

**Giới hạn pháp lý:**
- Không áp dụng cho vụ án dân sự, hành chính, kinh tế
- Chỉ thử nghiệm trên luật hình sự Việt Nam
- Dữ liệu huấn luyện có thể phản ánh thiên kiến lịch sử
- Hệ thống KHÔNG thể thay thế phân tích pháp lý của chuyên gia

**Temporal leakage risk:**
Đây là rủi ro quan trọng nhất trong nghiên cứu: nếu dữ liệu huấn luyện
chứa thông tin từ tương lai so với vụ án đang dự đoán, kết quả đánh giá
sẽ bị thổi phồng và không phản ánh thực tế. Mọi thay đổi về evaluation
phải qua code review để kiểm tra temporal split.

---

## Kiểm định Tự động (Tests)

Hệ thống sở hữu bộ kiểm thử tự động toàn diện với **112 test cases** bao phủ từ tầng xử lý văn bản, trích xuất thực thể, suy luận thời gian đến phát hiện rò rỉ dữ liệu và tích hợp API:

```bash
# Chạy toàn bộ 112 tests (100% Passed)
pytest

# Chỉ chạy các bài kiểm thử suy luận pháp lý thời gian (Temporal Legal Reasoning)
pytest tests/temporal_legal/ -v

# Chỉ chạy kiểm tra rò rỉ dữ liệu (Data Leakage & Chronological Split)
pytest tests/leakage/ -v

# Kiểm thử tích hợp luồng điều phối và API Endpoints
pytest tests/integration/ -v
```

---

## Đóng góp

Dự án đang trong giai đoạn nghiên cứu nội bộ tại UIT. Để đóng góp:

1. Fork repository
2. Tạo branch: `git checkout -b feature/ten-tinh-nang`
3. Commit thay đổi với message rõ ràng
4. Tạo Pull Request với mô tả chi tiết

**Coding standards:**
- Python 3.12+ type hints bắt buộc
- Docstrings bằng tiếng Việt (logic) + tiếng Anh (tên hàm/class)
- Format: `black --line-length 100`
- Lint: `ruff check src/`
- Tests bắt buộc cho temporal engine và evaluation

---

## License

MIT License - xem file [LICENSE](LICENSE)

**Ghi nhận:**
- [fastembed](https://github.com/qdrant/fastembed) - ONNX embeddings
- [LiteLLM](https://github.com/BerriAI/litellm) - LLM abstraction
- [sqlite-vec](https://github.com/asg017/sqlite-vec) - Vector search cho SQLite
- [Anthropic Claude](https://www.anthropic.com) - Primary LLM
- [TAND Tối cao Việt Nam](https://toaan.gov.vn) - Nguồn dữ liệu án lệ và bản án

---

*Dự án nghiên cứu thuộc Trường Đại học Công nghệ Thông tin - ĐHQG TP.HCM (UIT)*
