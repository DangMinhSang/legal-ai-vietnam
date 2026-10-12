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

## Trạng thái dự án

### Phase 1 - MVP (Đang triển khai)

- [x] Cấu trúc dự án và cấu hình
- [ ] Document parser (PDF + OCR)
- [ ] Database schema (SQLite + sqlite-vec)
- [ ] Embedding service (fastembed)
- [ ] Legal RAG indexing (VBPL)
- [ ] Fact extraction (LLM)
- [ ] Similar case retrieval
- [ ] First instance prediction (LLM-based)
- [ ] REST API endpoints
- [ ] Evaluation framework

### Phase 2 - ML Models (Kế hoạch)

- [ ] Thu thập đủ dữ liệu (>500 vụ án có nhãn)
- [ ] Train ML classifier cho sơ thẩm
- [ ] Train appeal prediction model
- [ ] Temporal split evaluation

### Phase 3 - Nâng cao (Tương lai)

- [ ] Fine-tuning LLM trên dữ liệu pháp lý Việt Nam
- [ ] Multi-modal (hình ảnh chứng cứ)
- [ ] Web interface

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

## Chạy tests

```bash
# Tất cả tests
pytest

# Chỉ unit tests
pytest tests/unit/

# Kiểm tra temporal leakage
pytest tests/leakage/ -v

# Với coverage report
pytest --cov=src --cov-report=html
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
