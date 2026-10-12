# Kiến trúc hệ thống Legal AI Vietnam

## 1. Tổng quan kiến trúc

Hệ thống được thiết kế theo mô hình Modular Pipeline kết hợp RAG và Machine Learning:

```
[ Hồ sơ vụ án / Văn bản ]
           │
           ▼
[ Document Parser ] ── (pypdf / html_parser)
           │
           ▼
[ Fact Extraction ] ── (LLM qua litellm: Claude / GPT)
           │
     ┌─────┴─────────────────────────┐
     ▼                               ▼
[ Temporal Legal Engine ]    [ Legal RAG & Precedent Agent ]
 (Xác định luật có hiệu lực)  (fastembed + sqlite-vec)
     │                               │
     └─────────────┬─────────────────┘
                   ▼
       [ Case Retrieval Engine ]
                   │
                   ▼
      [ Prediction Sub-system ]
    (First Instance & Appeal Predictors)
                   │
                   ▼
       [ Validation Engine ]
  (Consistency & Citation Checker)
                   │
                   ▼
        [ API & Output Layer ]
```

## 2. Các thành phần chính

- **Storage**: SQLite 3 kết hợp extension `sqlite-vec` cho vector search in-process (không cần PostgreSQL / Docker).
- **Embeddings**: `fastembed` với ONNX runtime, chạy CPU / GPU nhẹ nhàng không phụ thuộc PyTorch.
- **LLM Layer**: Gọi qua `litellm` (Claude 3.5 Sonnet/Haiku, GPT-4o-mini).
- **Prediction Layer**: Feature engineering kết hợp Scikit-Learn / XGBoost.
