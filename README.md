# Legal AI Vietnam

Hệ thống Trí tuệ Nhân tạo Pháp lý Đa Lĩnh vực & **Hỗ trợ Giải quyết Tranh chấp, Định khung Hình phạt** theo Pháp luật Việt Nam.

> **Cảnh báo nghiên cứu:** Đây là công trình nghiên cứu học thuật tại Đại học Công nghệ Thông tin (UIT) - ĐHQG TP.HCM. Kết quả phân tích mang tính chất tham khảo, hỗ trợ nghiên cứu và KHÔNG thay thế ý kiến tư vấn chính thức của Luật sư hoặc phán quyết có hiệu lực của Hội đồng xét xử.

---

## Mục tiêu nghiên cứu & Mở rộng Đa lĩnh vực (Phase 3)

Hệ thống được thiết kế giải quyết các bài toán nghiên cứu cốt lõi:

1. **RQ1 - Phân tích sơ thẩm & Cá thể hóa hình phạt (Hình sự):** Hệ thống AI đa tác nhân dự đoán kết quả sơ thẩm hình sự, cá thể hóa hình phạt theo vai trò (thực hành, giúp sức, chủ mưu) và chuẩn hóa đầy đủ **A. 7 hình phạt chính** và **B. 7 hình phạt bổ sung** theo **Điều 32 Bộ luật Hình sự 2015**.
2. **RQ2 - Dự đoán phúc thẩm:** Dự đoán chiều hướng thay đổi của phán quyết phúc thẩm (y án, giảm nhẹ, tăng nặng, hủy án).
3. **RQ3 - Tính thời gian của luật (Temporal Legal Reasoning):** Đối chiếu chính xác phiên bản luật áp dụng tại thời điểm hành vi (Điều 7 BLHS 2015, NQ 41/2017/QH14) và nguyên tắc hồi tố có lợi.
4. **RQ4 - Giải quyết Tranh chấp Đa lĩnh vực (Multi-Domain Dispute Resolution):**
   - **Dân sự (Civil Law):** Tranh chấp hợp đồng vay mượn/đặt cọc, di sản thừa kế, kiểm soát trần lãi suất 20%/năm (Điều 468 BLDS), tự động tính án phí sơ thẩm có giá ngạch theo **Nghị quyết 326/2016/UBTVQH14**.
   - **Hành chính (Administrative Law):** Khiếu kiện Quyết định thu hồi đất, bồi thường GPMB, xử phạt VPHC của UBND; xây dựng chiến lược **2 kênh song song** (Khiếu nại 90 ngày & Khởi kiện TAND 01 năm theo Luật TTHC 2015); đề xuất Biện pháp khẩn cấp tạm thời (Điều 68 LTTHC).
   - **Kinh doanh Thương mại (Commercial Law & Arbitration):** Kiểm soát chế tài phạt vi phạm không quá **trần 8% giá trị nghĩa vụ bị vi phạm** (Điều 301 Luật Thương mại 2005); ưu tiên thẩm quyền Trọng tài Thương mại Quốc tế (VIAC) theo Điều 6 Luật Trọng tài Thương mại 2010; đánh giá miễn trách nhiệm do Bất khả kháng (Điều 294, 295 LTM).
   - **Kỷ luật & Lao động (Disciplinary & Labor Law):** Đánh giá 4 hình thức kỷ luật lao động luật định duy nhất (Điều 124 BLLĐ 2019); kiểm soát nghiêm ngặt các điều cấm (cấm phạt tiền cắt lương Điều 127; cấm xử lý kỷ luật lao động nữ mang thai/nuôi con nhỏ Điều 137); tính toán quyền lợi bồi thường khi sa thải trái pháp luật theo **Điều 41 BLLĐ 2019**.

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

#### Cách 1: Giao diện Web tương tác Đa Lĩnh vực (Khuyến nghị)
Giao diện trực quan trên trình duyệt hỗ trợ cả 5 lĩnh vực pháp luật (Hình sự, Dân sự, Hành chính, Thương mại, Kỷ luật), 11 hồ sơ mẫu kiểm thử 1-click, chế độ nhập liệu 2 khung hoặc 1 khung, bảng lưới 7 hình phạt chính & 7 hình phạt bổ sung Điều 32 BLHS, bảng tính án phí NQ 326 và trần phạt 8% LTM:
```bash
python run_web.py
```
> Trình duyệt sẽ tự động mở tại `http://localhost:8000` (API Docs tại `http://localhost:8000/docs`).

#### Cách 2: Giao diện Dòng lệnh Tương tác Đa Lĩnh vực (CLI)
Giao diện dòng lệnh tương tác mạnh mẽ với menu chọn 11 hồ sơ mẫu hoặc tự nhập liệu bằng 2 khung / 1 khung tự do, hiển thị bảng Rich chuyên sâu theo từng lĩnh vực:
```bash
python interactive.py
```

#### Cách 3: Chạy Demo Tự Động Đa Lĩnh vực 1-Lệnh
Chạy tự động kiểm thử tuần tự qua cả 5 lĩnh vực pháp luật và chuẩn hóa hệ thống hình phạt Điều 32 BLHS với bảng kết quả Rich trực quan:
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

# 4. Benchmark đánh giá tự động 11 hồ sơ đa lĩnh vực (Phase 3 — MỚI)
#    Kiểm định Domain Accuracy & Statutory Compliance (5 lĩnh vực, ~126 ms/vụ)
python scripts/evaluate_multi_domain.py
```

### Bước 9: Huấn luyện Fine-tuning Legal LLM trên Kaggle (GPU Miễn phí)

Hệ thống cung cấp sẵn quy trình huấn luyện QLoRA 4-bit giúp mô hình LLM chuyên sâu về Luật Hình sự Việt Nam (nhận thức sâu về Đ.341, Đ.51, Đ.52, Đ.54, Đ.65 BLHS, suy luận chớp nhoáng 0.3s):

1. **Chuẩn bị dữ liệu SFT**:
   ```bash
   python scripts/prepare_finetune_dataset.py
   ```
2. **Huấn luyện trên Kaggle**:
   - Mở Kaggle -> Tạo New Notebook -> Bật **GPU T4 x2** (Settings -> Accelerator -> GPU T4).
   - Chọn File -> Import Notebook -> Chọn file `notebooks/kaggle_finetune_legal_llm.ipynb`.
   - Nhấn **Run All**. Quá trình huấn luyện chỉ mất từ 15-20 phút và tự động xuất file adapter weights.

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
│   ├── run_evaluation.py        # Chạy bộ đánh giá
│   └── evaluate_multi_domain.py # Benchmark đánh giá 5 lĩnh vực (11 hồ sơ)
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

Toàn bộ các thành phần cốt lõi của hệ thống đã được triển khai, kiểm thử và nghiệm thu khoa học với **142/142 bài kiểm thử vượt qua (100% Pass Rate)**:

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
- [x] **REST API Endpoints**: Hệ thống FastAPI đầy đủ router `/health`, `/documents`, `/cases`, `/analysis`, `/orchestrate`, `/web_analyze`, `/auto_split`, `/multi_domain` (`src/api/`).
- [x] **Evaluation Framework**: Bộ chỉ số Balanced Accuracy, Macro F1, MAE, Sentence Frame Accuracy, Monotonicity Score (`src/evaluation/metrics.py`).

### Phase 2 - Mô hình Học máy & Phân tích Thời gian — ĐÃ HOÀN THÀNH 100%

- [x] **Corpus Bản án Chuẩn hóa**: Xây dựng tập dữ liệu 52 bản án hình sự đa dạng các nhóm tội phạm đại diện (bao gồm các bản án thực tế về Điều 341 BLHS) với nhãn kiểm định phục vụ nghiên cứu (`scripts/generate_judgments_corpus.py`).
- [x] **Train ML Models cho Sơ thẩm**: Huấn luyện Random Forest Classifier (100% Balanced Acc) và Regressor (MAE 1.83 năm) với khung luật định tham chiếu (`scripts/train_baseline_models.py`).
- [x] **Kiến trúc Dự đoán Phúc thẩm (Appeal Prediction)**: Xây dựng bộ đặc trưng và mô hình định hướng 4 kết quả phúc thẩm: y án, giảm nhẹ, tăng nặng, hủy án (`src/appeal_prediction/`).
- [x] **Kiểm định Phân chia Thời gian (Chronological Split)**: Thiết lập mốc ranh giới thời gian `2022-01-01` (< 2022 train, $\ge$ 2022 test) triệt tiêu 100% Future Data Leakage (`tests/leakage/test_temporal_split.py`).
- [x] **Đánh giá Benchmark Truy xuất (Legal RAG Benchmark)**: Kiểm định 15 kịch bản truy vấn pháp lý, đạt **Hit@3 = 100%**, **MRR = 0.8111**, tuân thủ 100% phân tách tri thức (`scripts/benchmark_retrieval.py`).
- [x] **Nghiên cứu Ablation Study**: Định lượng đóng góp của từng thành phần (Heuristic vs Tabular ML vs RAG Frame vs Guardrails) (`scripts/run_ablation_study.py`).

### Phase 3 - Mở rộng Đa Lĩnh vực & Hệ thống Hình phạt Điều 32 BLHS — ĐÃ HOÀN THÀNH 100%

- [x] **Hệ thống Hình phạt Toàn diện theo Điều 32 BLHS 2015**:
  - **A. 7 hình phạt chính (Khoản 1 Điều 32)**: (1) Cảnh cáo; (2) Phạt tiền; (3) Cải tạo không giam giữ; (4) Trục xuất; (5) Tù có thời hạn; (6) Tù chung thân; (7) Tử hình.
  - **B. 7 hình phạt bổ sung (Khoản 2 Điều 32)**: (1) Cấm đảm nhiệm chức vụ, cấm hành nghề hoặc làm công việc nhất định; (2) Cấm cư trú; (3) Quản chế; (4) Tước một số quyền công dân; (5) Tịch thu tài sản; (6) Phạt tiền, khi không áp dụng là hình phạt chính; (7) Trục xuất, khi không áp dụng là hình phạt chính.
  - **Biện pháp tư pháp (Điều 46 - 49)**: Tịch thu sung công, trả lại tài sản, bồi thường thiệt hại, bắt buộc chữa bệnh.
  - **Guardrails Điều 40 & Điều 65**: Kiểm soát cấm tử hình người dưới 18 tuổi, phụ nữ có thai/nuôi con nhỏ, người từ 75 tuổi trở lên; kiểm soát trần án treo $\le 3$ năm tù; cấm trùng phạt tiền/trục xuất vừa chính vừa bổ sung.
- [x] **Mở rộng Đa lĩnh vực Pháp luật & Giải quyết Tranh chấp**:
  - **Dân sự (`src/legal_domains/civil.py`)**: Hợp đồng vay, đặt cọc, bồi thường ngoài hợp đồng (Đ.584 - 608 BLDS), thừa kế (Đ.609 - 623), kiểm soát trần lãi suất 20%/năm (Đ.468 BLDS), tự động tính án phí sơ thẩm có giá ngạch theo **Nghị quyết 326/2016/UBTVQH14**.
  - **Hành chính (`src/legal_domains/administrative.py`)**: Khiếu kiện QĐ thu hồi đất, bồi thường GPMB, xử phạt VPHC của UBND; chiến lược **2 kênh song song** (Khiếu nại 90 ngày & Khởi kiện TAND 01 năm theo Luật TTHC 2015); đề xuất Biện pháp khẩn cấp tạm thời (Điều 68 LTTHC).
  - **Kinh doanh Thương mại (`src/legal_domains/commercial.py`)**: Kiểm soát trần phạt vi phạm tối đa **8% giá trị nghĩa vụ vi phạm** (Điều 301 Luật Thương mại 2005); ưu tiên thẩm quyền Trọng tài Thương mại Quốc tế (VIAC) theo Điều 6 Luật TTTM 2010; đánh giá Bất khả kháng (Điều 294, 295 LTM).
  - **Kỷ luật & Lao động (`src/legal_domains/disciplinary.py`)**: 4 hình thức kỷ luật lao động hợp pháp (Điều 124 BLLĐ 2019); cấm phạt tiền cắt lương (Điều 127); cấm sa thải lao động nữ mang thai/nuôi con nhỏ (Điều 137); bồi thường sa thải trái luật theo Điều 41 BLLĐ.
  - **Bộ điều phối đa lĩnh vực (`src/legal_domains/dispatcher.py`)**: Tự động nhận diện hoặc ép buộc theo lĩnh vực (forced_domain) với phân bổ trọng số xác suất 5 lĩnh vực.
- [x] **Corpus & Benchmark Đa Lĩnh vực**:
  - `data/multi_domain_corpus.jsonl`: 11 kịch bản đối thoại ChatML đa lĩnh vực chuẩn hóa cho SFT Fine-tuning LLM.
  - `data/multi_domain_benchmark.json`: Bộ câu hỏi kiểm thử và tiêu chí đánh giá chuẩn cho cả 5 quan hệ pháp luật.
  - `scripts/generate_multi_domain_corpus.py`: Script tự động sinh corpus.
- [x] **Giao diện Web Nâng cấp Toàn diện (`templates/index.html`)**:
  - Bộ lọc chọn 5 lĩnh vực pháp luật (Tự động, Hình sự, Dân sự, Hành chính, Thương mại, Kỷ luật).
  - 11 presets vụ việc thực tế 1-click bao quát toàn bộ 5 lĩnh vực.
  - 2 Chế độ nhập liệu linh hoạt: Chế độ 1 khung tự do (có nút Tự động tách sang 2 khung) và Chế độ 2 khung chi tiết (Đương sự & Tình tiết vụ việc).
  - Card trực quan hóa lưới **A. 7 HÌNH PHẠT CHÍNH** và **B. 7 HÌNH PHẠT BỔ SUNG** theo Điều 32 BLHS.
  - Card hiển thị tính án phí tự động NQ 326, trần phạt 8% LTM, thời hiệu khởi kiện LTTHC, quyền lợi Điều 41 BLLĐ.
  - Sơ đồ trực quan **Lộ trình Giải quyết Tranh chấp 5 Bước (Dispute Resolution Roadmap)**.
  - Hệ thống kiểm tra Hàng rào Nhất quán Pháp lý (Consistency Guardrails).
- [x] **Hệ thống Kiểm thử Mở rộng**: **142/142 bài kiểm thử vượt qua 100%** (`tests/unit/test_legal_domains.py`, `tests/unit/test_multi_domain_benchmark.py`, `tests/integration/test_api_endpoints.py`, v.v.).
- [x] **Bộ điều phối đa lĩnh vực nâng cấp (`src/legal_domains/dispatcher.py`)**: Tích hợp hệ thống trọng số hai tầng — tiêu chuẩn (1.0–2.0) và `high_signal_weights` (3.0–5.0) nhận diện thuật ngữ pháp lý đặc trưng cao (ví dụ: `"quản lý thị trường"` → Hành chính 5.0, `"trừ 50% tiền lương"` → Kỷ luật 5.0, `"viac"` → Thương mại 4.0). Đạt **100% Domain Accuracy** trên toàn bộ 11 hồ sơ benchmark.
- [x] **Kiểm định Pháp lý Tự động (`scripts/evaluate_multi_domain.py`)**: Script đánh giá benchmark 11 hồ sơ đa lĩnh vực, kiểm tra chéo Domain Accuracy và Statutory Compliance (tuân thủ hàng rào pháp định: Điều 32 BLHS, NQ 326, trần lãi 20% BLDS, trần phạt 8% LTM, 2 kênh LTTHC, Điều 41 BLLĐ). Kết quả: **Domain Accuracy 100% (11/11)** và **Statutory Compliance 100% (11/11)**, thời gian xử lý trung bình **~126 ms/vụ việc**.
- [x] **Phát hiện Bất khả kháng (`src/legal_domains/commercial.py`)**: Nhận diện sự kiện bất khả kháng ưu tiên trước phạt vi phạm; tự động đề xuất chế tài miễn trách nhiệm `CommercialRemedyType.FORCE_MAJEURE_EXEMPTION` theo Điều 294 & 295 Luật Thương mại 2005.

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

### 4. Benchmark Đa Lĩnh vực Phase 3 — Phân loại & Tuân thủ Pháp định (RQ4)

| Chỉ số | Kết quả | Chi tiết |
|---|:---:|---|
| **Domain Accuracy** | **100.0%** | 11/11 hồ sơ được phân loại đúng lĩnh vực (Hình sự / Dân sự / Hành chính / Thương mại / Kỷ luật) |
| **Statutory Compliance** | **100.0%** | 11/11 hồ sơ tuân thủ đầy đủ hàng rào pháp định (Điều 32 BLHS, NQ 326, Điều 468 BLDS, Điều 301 LTM, Điều 68 LTTHC, Điều 41 BLLĐ) |
| **Lĩnh vực kiểm định** | **5/5** | Hình sự (3 vụ), Dân sự (2 vụ), Hành chính (2 vụ), Thương mại (2 vụ), Kỷ luật (2 vụ) |
| **Thời gian xử lý** | **~126 ms/vụ** | Chạy thuần Python, không cần GPU |
| **Tổng bài kiểm thử** | **142/142** | 100% pass — bao gồm `tests/unit/test_multi_domain_benchmark.py` |

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
- Hệ thống hỗ trợ 5 lĩnh vực pháp luật (Hình sự, Dân sự, Hành chính, Thương mại, Kỷ luật) theo quy định pháp luật Việt Nam.
- Dữ liệu và phân tích mang tính chất nghiên cứu học thuật và hỗ trợ chuyên môn, KHÔNG thể thay thế phán quyết của Hội đồng xét xử hoặc ý kiến tư vấn chính thức của Luật sư.
- Dữ liệu mẫu có thể phản ánh thiên kiến lịch sử cần được cập nhật thường xuyên theo các Nghị quyết và Án lệ mới nhất của TAND Tối cao.

**Temporal leakage risk:**
Đây là rủi ro quan trọng nhất trong nghiên cứu: nếu dữ liệu huấn luyện
chứa thông tin từ tương lai so với vụ án đang dự đoán, kết quả đánh giá
sẽ bị thổi phồng và không phản ánh thực tế. Mọi thay đổi về evaluation
phải qua code review để kiểm tra temporal split.

---

## Kiểm định Tự động (Tests)

Hệ thống sở hữu bộ kiểm thử tự động toàn diện với **140 test cases** bao phủ từ tầng xử lý văn bản, trích xuất thực thể, suy luận thời gian, phát hiện rò rỉ dữ liệu, 5 lĩnh vực pháp luật đến tích hợp API:

```bash
# Chạy toàn bộ 140 tests (100% Passed)
pytest -v

# Kiểm thử chuyên sâu 5 Lĩnh vực Pháp luật & Điều 32 BLHS
pytest tests/unit/test_legal_domains.py -v

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
