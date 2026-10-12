"""SQLAlchemy ORM models cho hệ thống Legal AI Vietnam.

Schema bao gồm:
- LegalDocument / LegalProvision: văn bản QPPL và điều khoản
- Precedent: án lệ chính thức (Hội đồng thẩm phán TANDTC ban hành)
- JudgmentDocument: bản án cụ thể từ toà án
- Case / CaseFact / JudgmentOutcome: vụ án, tình tiết, kết quả
- AppealRecord: kháng cáo và kết quả phúc thẩm
- TextChunk: đoạn văn bản được index cho RAG + vector embedding
- DocumentSource: log nguồn thu thập dữ liệu
- PredictionRun / EvaluationResult: log dự đoán và đánh giá

Lưu ý kỹ thuật:
- UUID lưu dưới dạng TEXT (SQLite không có UUID native type)
- Vector embedding lưu dưới dạng JSON list[float] trong cột Text;
  sqlite-vec virtual table được tạo riêng qua DDL thủ công nếu cần
  full ANN search (xem scripts/setup_db.py).
- JSON columns dùng SQLAlchemy JSON type (serialize/deserialize tự động).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Shared base for all ORM models."""

    pass


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _new_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# 1. LegalDocument — văn bản quy phạm pháp luật
# ---------------------------------------------------------------------------
class LegalDocument(Base):
    """Văn bản QPPL: luật, nghị định, thông tư, quyết định, nghị quyết."""

    __tablename__ = "legal_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    # Loại văn bản: law | decree | circular | decision | resolution | ordinance
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Số ký hiệu, ví dụ "15/2022/QH15"
    doc_number: Mapped[str | None] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    issuing_body: Mapped[str | None] = mapped_column(String(255))
    signing_date: Mapped[datetime | None] = mapped_column(DateTime)
    effective_date: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    # Trạng thái hiệu lực: active | expired | superseded | draft
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    # URL nguồn gốc (VBPL, Công báo, v.v.)
    source_url: Mapped[str | None] = mapped_column(Text)
    # Nội dung toàn văn (có thể rất dài)
    full_text: Mapped[str | None] = mapped_column(Text)
    # Metadata bổ sung (lĩnh vực pháp lý, từ khoá, v.v.)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    provisions: Mapped[list[LegalProvision]] = relationship(
        "LegalProvision", back_populates="document", cascade="all, delete-orphan"
    )
    chunks: Mapped[list[TextChunk]] = relationship(
        "TextChunk",
        back_populates="legal_document",
        foreign_keys="TextChunk.legal_document_id",
    )

    __table_args__ = (UniqueConstraint("doc_number", "doc_type", name="uq_doc_number_type"),)

    def __repr__(self) -> str:
        return f"<LegalDocument {self.doc_number!r} ({self.doc_type})>"


# ---------------------------------------------------------------------------
# 2. LegalProvision — điều / khoản / điểm trong văn bản
# ---------------------------------------------------------------------------
class LegalProvision(Base):
    """Một điều, khoản, hoặc điểm cụ thể trong văn bản QPPL."""

    __tablename__ = "legal_provisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    legal_document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("legal_documents.id", ondelete="CASCADE"), index=True
    )
    # Loại: article | clause | point | section | chapter
    provision_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # Số thứ tự trong văn bản, ví dụ "Điều 10" → "10"
    provision_number: Mapped[str | None] = mapped_column(String(20))
    title: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # ID điều khoản cha (nếu là khoản/điểm con)
    parent_provision_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("legal_provisions.id", ondelete="SET NULL")
    )
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    document: Mapped[LegalDocument] = relationship("LegalDocument", back_populates="provisions")
    children: Mapped[list[LegalProvision]] = relationship("LegalProvision")

    def __repr__(self) -> str:
        return f"<LegalProvision {self.provision_type} {self.provision_number}>"


# ---------------------------------------------------------------------------
# 3. Precedent — án lệ chính thức
# ---------------------------------------------------------------------------
class Precedent(Base):
    """Án lệ do Hội đồng thẩm phán TANDTC ban hành."""

    __tablename__ = "precedents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    # Số án lệ, ví dụ "01/2016/AL"
    precedent_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    # Tóm tắt tình huống pháp lý
    legal_issue_summary: Mapped[str | None] = mapped_column(Text)
    # Giải pháp pháp lý của án lệ
    legal_solution: Mapped[str | None] = mapped_column(Text)
    # Nội dung toàn văn
    full_text: Mapped[str | None] = mapped_column(Text)
    # Lĩnh vực pháp lý: civil | criminal | administrative | commercial | family
    legal_domain: Mapped[str | None] = mapped_column(String(50), index=True)
    publication_date: Mapped[datetime | None] = mapped_column(DateTime)
    # Quyết định giám đốc thẩm làm nguồn gốc án lệ
    source_judgment_ref: Mapped[str | None] = mapped_column(String(200))
    source_url: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    chunks: Mapped[list[TextChunk]] = relationship(
        "TextChunk",
        back_populates="precedent",
        foreign_keys="TextChunk.precedent_id",
    )

    def __repr__(self) -> str:
        return f"<Precedent {self.precedent_number!r}>"


# ---------------------------------------------------------------------------
# 4. JudgmentDocument — bản án cụ thể
# ---------------------------------------------------------------------------
class JudgmentDocument(Base):
    """Bản án do toà án ban hành (từ congbobanan.toaan.gov.vn)."""

    __tablename__ = "judgment_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    # Số bản án, ví dụ "15/2023/HSST"
    judgment_number: Mapped[str | None] = mapped_column(String(100), index=True)
    # Loại: first_instance | appeal | cassation | re_opening
    judgment_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    # Lĩnh vực: criminal | civil | administrative | commercial | family | labor
    legal_domain: Mapped[str | None] = mapped_column(String(50), index=True)
    court_name: Mapped[str | None] = mapped_column(String(255))
    court_level: Mapped[str | None] = mapped_column(String(50))  # district | province | high | supreme
    judgment_date: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    full_text: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    outcomes: Mapped[list[JudgmentOutcome]] = relationship(
        "JudgmentOutcome", back_populates="judgment"
    )
    chunks: Mapped[list[TextChunk]] = relationship(
        "TextChunk",
        back_populates="judgment_document",
        foreign_keys="TextChunk.judgment_document_id",
    )

    def __repr__(self) -> str:
        return f"<JudgmentDocument {self.judgment_number!r} ({self.judgment_type})>"


# ---------------------------------------------------------------------------
# 5. Case — vụ án (liên kết sơ thẩm + phúc thẩm)
# ---------------------------------------------------------------------------
class Case(Base):
    """Vụ án pháp lý, có thể có nhiều cấp xét xử."""

    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    # Mã vụ án nội bộ
    case_code: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str | None] = mapped_column(Text)
    legal_domain: Mapped[str | None] = mapped_column(String(50), index=True)
    # Trạng thái: open | first_instance | appealing | final | closed
    status: Mapped[str] = mapped_column(String(30), default="open", index=True)
    # Ngày xảy ra sự kiện pháp lý (quan trọng cho temporal engine)
    incident_date: Mapped[datetime | None] = mapped_column(DateTime)
    first_instance_judgment_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("judgment_documents.id", ondelete="SET NULL")
    )
    appeal_judgment_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("judgment_documents.id", ondelete="SET NULL")
    )
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    facts: Mapped[list[CaseFact]] = relationship(
        "CaseFact", back_populates="case", cascade="all, delete-orphan"
    )
    appeal_records: Mapped[list[AppealRecord]] = relationship(
        "AppealRecord", back_populates="case", cascade="all, delete-orphan"
    )
    prediction_runs: Mapped[list[PredictionRun]] = relationship(
        "PredictionRun", back_populates="case"
    )

    def __repr__(self) -> str:
        return f"<Case {self.case_code!r} [{self.status}]>"


# ---------------------------------------------------------------------------
# 6. CaseFact — tình tiết trích xuất từ hồ sơ
# ---------------------------------------------------------------------------
class CaseFact(Base):
    """Tình tiết / dữ kiện được trích xuất từ hồ sơ vụ án."""

    __tablename__ = "case_facts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    # Loại tình tiết: charge | evidence | witness | timeline_event | mitigating | aggravating
    fact_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Ngày/thời điểm của tình tiết này
    event_date: Mapped[datetime | None] = mapped_column(DateTime)
    # Độ tin cậy của việc trích xuất (0.0 – 1.0)
    confidence: Mapped[float | None] = mapped_column(Float)
    # Văn bản nguồn gốc dùng để trích xuất
    source_text: Mapped[str | None] = mapped_column(Text)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    case: Mapped[Case] = relationship("Case", back_populates="facts")

    def __repr__(self) -> str:
        return f"<CaseFact {self.fact_type!r} for case {self.case_id!r}>"


# ---------------------------------------------------------------------------
# 7. JudgmentOutcome — kết quả xét xử
# ---------------------------------------------------------------------------
class JudgmentOutcome(Base):
    """Kết quả xét xử của một bản án cụ thể."""

    __tablename__ = "judgment_outcomes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    judgment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("judgment_documents.id", ondelete="CASCADE"), index=True
    )
    # Bên: plaintiff | defendant | prosecution | accused
    party: Mapped[str] = mapped_column(String(50), nullable=False)
    # Kết quả: guilty | not_guilty | partially_guilty | upheld | overturned | modified | dismissed
    outcome: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Hình phạt (nếu có): "2 năm tù giam", "Phạt tiền 50.000.000đ", v.v.
    sentence: Mapped[str | None] = mapped_column(Text)
    # Điều luật áp dụng (list số điều)
    applied_articles: Mapped[list[str] | None] = mapped_column(JSON)
    # Tội danh (cho vụ hình sự)
    charges: Mapped[list[str] | None] = mapped_column(JSON)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    judgment: Mapped[JudgmentDocument] = relationship(
        "JudgmentDocument", back_populates="outcomes"
    )

    def __repr__(self) -> str:
        return f"<JudgmentOutcome {self.party!r} → {self.outcome!r}>"


# ---------------------------------------------------------------------------
# 8. AppealRecord — kháng cáo / kháng nghị
# ---------------------------------------------------------------------------
class AppealRecord(Base):
    """Ghi nhận việc kháng cáo hoặc kháng nghị và kết quả phúc thẩm."""

    __tablename__ = "appeal_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    # Người kháng cáo: defendant | plaintiff | prosecution | third_party
    appellant: Mapped[str] = mapped_column(String(100), nullable=False)
    # Loại: appeal | protest (kháng nghị của VKS)
    appeal_type: Mapped[str] = mapped_column(String(20), default="appeal")
    appeal_date: Mapped[datetime | None] = mapped_column(DateTime)
    # Lý do kháng cáo
    grounds: Mapped[str | None] = mapped_column(Text)
    # Kết quả phúc thẩm: upheld | overturned | modified | dismissed | pending
    result: Mapped[str | None] = mapped_column(String(30), index=True)
    result_date: Mapped[datetime | None] = mapped_column(DateTime)
    appeal_judgment_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("judgment_documents.id", ondelete="SET NULL")
    )
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    case: Mapped[Case] = relationship("Case", back_populates="appeal_records")

    def __repr__(self) -> str:
        return f"<AppealRecord {self.appellant!r} → {self.result!r}>"


# ---------------------------------------------------------------------------
# 9. TextChunk — đoạn văn bản cho RAG
# ---------------------------------------------------------------------------
class TextChunk(Base):
    """Đoạn văn bản đã được chunked và embedded để phục vụ RAG retrieval.

    Embedding vector lưu dưới dạng JSON list[float].
    sqlite-vec virtual table (vec_chunks) được tạo riêng trong setup_db.py
    để hỗ trợ ANN search hiệu quả.
    """

    __tablename__ = "text_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    # Chỉ một trong ba foreign key sau được set (nguồn tài liệu)
    legal_document_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("legal_documents.id", ondelete="CASCADE"), index=True
    )
    precedent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("precedents.id", ondelete="CASCADE"), index=True
    )
    judgment_document_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("judgment_documents.id", ondelete="CASCADE"), index=True
    )
    # Nội dung đoạn văn bản
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Thứ tự chunk trong tài liệu gốc
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    # Số token ước tính
    token_count: Mapped[int | None] = mapped_column(Integer)
    # Tên model embedding đã dùng
    embedding_model: Mapped[str | None] = mapped_column(String(200))
    # Vector embedding (list[float] serialized as JSON)
    # Để ANN search, dùng sqlite-vec virtual table thay vì cột này
    embedding: Mapped[list[float] | None] = mapped_column(JSON)
    # Chiều embedding (để validate)
    embedding_dim: Mapped[int | None] = mapped_column(Integer)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    legal_document: Mapped[LegalDocument | None] = relationship(
        "LegalDocument",
        back_populates="chunks",
        foreign_keys=[legal_document_id],
    )
    precedent: Mapped[Precedent | None] = relationship(
        "Precedent",
        back_populates="chunks",
        foreign_keys=[precedent_id],
    )
    judgment_document: Mapped[JudgmentDocument | None] = relationship(
        "JudgmentDocument",
        back_populates="chunks",
        foreign_keys=[judgment_document_id],
    )

    def __repr__(self) -> str:
        return f"<TextChunk idx={self.chunk_index} len={len(self.content)}>"


# ---------------------------------------------------------------------------
# 10. DocumentSource — log nguồn thu thập
# ---------------------------------------------------------------------------
class DocumentSource(Base):
    """Log mỗi lần thu thập tài liệu từ nguồn bên ngoài."""

    __tablename__ = "document_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    # Tên nguồn: vbpl | toaan | huggingface | manual
    source_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_url: Mapped[str | None] = mapped_column(Text)
    # Trạng thái: success | failed | partial
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # ID tài liệu đã tạo (nếu thành công)
    created_document_id: Mapped[str | None] = mapped_column(String(36))
    document_type: Mapped[str | None] = mapped_column(String(30))  # legal_document | judgment | precedent
    error_message: Mapped[str | None] = mapped_column(Text)
    raw_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    crawled_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<DocumentSource {self.source_name!r} [{self.status}]>"


# ---------------------------------------------------------------------------
# 11. PredictionRun — log dự đoán
# ---------------------------------------------------------------------------
class PredictionRun(Base):
    """Ghi lại mỗi lần chạy dự đoán kết quả vụ án."""

    __tablename__ = "prediction_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    case_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("cases.id", ondelete="SET NULL"), index=True
    )
    # Loại dự đoán: first_instance | appeal
    prediction_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # Kết quả dự đoán: guilty | not_guilty | upheld | overturned | modified
    predicted_outcome: Mapped[str | None] = mapped_column(String(50))
    # Xác suất dự đoán (0.0 – 1.0)
    confidence: Mapped[float | None] = mapped_column(Float)
    # Model đã dùng
    model_name: Mapped[str | None] = mapped_column(String(100))
    model_version: Mapped[str | None] = mapped_column(String(50))
    # Feature vector đầu vào (JSON)
    input_features: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    # Xác suất từng nhãn
    probabilities: Mapped[dict[str, float] | None] = mapped_column(JSON)
    # Kết quả thực tế (nếu đã có để đánh giá)
    actual_outcome: Mapped[str | None] = mapped_column(String(50))
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    run_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    case: Mapped[Case | None] = relationship("Case", back_populates="prediction_runs")

    def __repr__(self) -> str:
        return f"<PredictionRun {self.prediction_type!r} → {self.predicted_outcome!r} ({self.confidence:.2f})>"


# ---------------------------------------------------------------------------
# 12. EvaluationResult — kết quả đánh giá hệ thống
# ---------------------------------------------------------------------------
class EvaluationResult(Base):
    """Lưu kết quả chạy đánh giá (retrieval metrics, prediction metrics)."""

    __tablename__ = "evaluation_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    # Tên experiment / run
    experiment_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    # Component được đánh giá: retrieval | prediction | fact_extraction | end_to_end
    component: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Dataset dùng để đánh giá
    dataset_name: Mapped[str | None] = mapped_column(String(200))
    # Tất cả metrics (precision@k, recall@k, ndcg, f1, accuracy, v.v.)
    metrics: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False)
    # Hyperparameter / config của run này
    config: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<EvaluationResult {self.experiment_name!r} [{self.component}]>"


# ---------------------------------------------------------------------------
# 13. Document — tài liệu người dùng tải lên
# ---------------------------------------------------------------------------
class Document(Base):
    """Tài liệu hồ sơ hoặc bản án được upload vào hệ thống."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str | None] = mapped_column(Text)
    file_type: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="uploaded", index=True)
    page_count: Mapped[int | None] = mapped_column(Integer)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    extracted_text_length: Mapped[int] = mapped_column(Integer, default=0)
    parse_method: Mapped[str] = mapped_column(String(50), default="text_extraction")
    warnings: Mapped[list[str] | None] = mapped_column(JSON)
    linked_case_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("cases.id", ondelete="SET NULL"), nullable=True
    )
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Document {self.filename!r} [{self.status}]>"


# ---------------------------------------------------------------------------
# 14. AnalysisResultModel — kết quả phân tích AI lưu trữ
# ---------------------------------------------------------------------------
class AnalysisResultModel(Base):
    """Lưu kết quả phân tích AI cho bản án/vụ án."""

    __tablename__ = "analysis_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    judgment_id: Mapped[str] = mapped_column(String(36), index=True)
    analysis_type: Mapped[str] = mapped_column(String(50), index=True)
    model_used: Mapped[str] = mapped_column(String(100), default="unknown")
    result: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    confidence: Mapped[float | None] = mapped_column(Float)
    processing_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    warnings: Mapped[list[str] | None] = mapped_column(JSON)
    uncertainty_flags: Mapped[list[str] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<AnalysisResultModel {self.judgment_id!r} ({self.analysis_type})>"

