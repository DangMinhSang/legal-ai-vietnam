"""Sanity test script for legal-ai-vietnam core services."""

import sys
from pathlib import Path
from datetime import date

print("=== SANITY CHECK SUITE ===")

print("--- Test 1: Service Imports ---")
from src.services import (
    DocumentParser,
    ParsedDocument,
    EmbeddingService,
    LLMService,
    LegalTextChunker,
    TextChunkResult,
)
print("Service imports: OK")

print("--- Test 2: DocumentParser ---")
parser = DocumentParser()
sample_txt = Path("test_sample.txt")
sample_txt.write_text("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\nĐộc lập - Tự do - Hạnh phúc\n\nBẢN ÁN SỐ 12/2023/HS-ST", encoding="utf-8")
doc = parser.parse(sample_txt)
if sample_txt.exists():
    sample_txt.unlink()
assert doc.parse_method == "text_extraction"
assert len(doc.text) > 0
print(f"DocumentParser: OK (text length: {len(doc.text)}, parse_method: {doc.parse_method})")

print("--- Test 3: EmbeddingService LRU Cache & Truncation ---")
embedder = EmbeddingService()
truncated = embedder._truncate("A" * 3000)
assert len(truncated) == 2048
embedder._put_cached("hello", [0.1] * 768)
assert embedder._get_cached("hello") == [0.1] * 768
print("EmbeddingService: LRU cache & truncation logic OK")

print("--- Test 4: LegalTextChunker ---")
chunker = LegalTextChunker(target_chunk_size=200, overlap=30)
legal_sample = """
Chương XIV
CÁC TỘI XÂM PHẠM TÍNH MẠNG, SỨC KHỎE

Điều 123. Tội giết người
1. Người nào giết người thuộc một trong các trường hợp sau đây, thì bị phạt tù từ 12 năm đến 20 năm, tù chung thân hoặc tử hình:
a) Giết 02 người trở lên;
b) Giết người dưới 16 tuổi;

2. Phạm tội không thuộc các trường hợp quy định tại khoản 1 Điều này, thì bị phạt tù từ 07 năm đến 15 năm.
"""
chunks = chunker.chunk_legal_document(legal_sample, doc_type="statute")
assert len(chunks) > 0
has_ref = any(c.legal_ref == "Điều 123" for c in chunks)
assert has_ref
print(f"LegalTextChunker: OK ({len(chunks)} chunks, ref extracted: {has_ref})")

print("--- Test 5: Fact Extraction Schemas & Extractor ---")
from src.fact_extraction import (
    CaseFacts,
    DefendantInfo,
    ExtractedField,
    ExtractionStatus,
    JudgmentOutcomeSchema,
    CaseFactExtractor,
)
extractor = CaseFactExtractor()
empty_facts, defs = extractor.extract("")
assert empty_facts.case_number.status == ExtractionStatus.MISSING
assert len(defs) == 0

sections = extractor._split_judgment_sections(
    "BẢN ÁN SỐ 01/2023\nNỘI DUNG VỤ ÁN:\nBị cáo A thực hiện hành vi trộm cắp.\nQUYẾT ĐỊNH:\nXử phạt bị cáo A 1 năm tù."
)
assert "BẢN ÁN" in sections["header"]
assert "trộm cắp" in sections["body"]
assert "Xử phạt" in sections["verdict"]
print("Fact Extraction & Sections: OK")

print("--- Test 6: Temporal Legal Engine ---")
from src.temporal_legal_engine import TemporalLegalEngine, LegalVersionResult, SelectionBasis
tle = TemporalLegalEngine()

# Case 1: missing offense_date
res1 = tle.select_applicable_version(
    "100/2015/QH13",
    None,
    date(2022, 1, 1),
    [{"id": "v1", "document_number": "100/2015/QH13", "effective_from": date(2018, 1, 1), "effective_to": None}],
)
assert res1.uncertainty is True
assert res1.requires_expert_review is True

# Case 2: standard offense_date
res2 = tle.select_applicable_version(
    "100/2015/QH13",
    date(2019, 6, 1),
    date(2020, 1, 1),
    [{"id": "v1", "document_number": "100/2015/QH13", "effective_from": date(2018, 1, 1), "effective_to": None}],
)
assert res2.selected_version_basis == SelectionBasis.OFFENSE_DATE
assert res2.uncertainty is False

# Case 3: transitional provisions
has_tr, note = tle.check_transitional_provisions("BLHS_2015", date(2017, 1, 1), date(2019, 1, 1))
assert has_tr is True
print("Temporal Legal Engine: OK")

print("--- Test 7: LLM Service JSON Parser ---")
llm = LLMService()
sample_json_text = '{"charges": ["Điều 123"], "status": "extracted"}'
parsed_json = llm._parse_json_response(f"```json\n{sample_json_text}\n```")
assert parsed_json["charges"] == ["Điều 123"]
print("LLM Service JSON Parser: OK")

print("=== ALL 7 SANITY CHECKS PASSED SUCCESSFULLY ===")
