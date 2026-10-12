"""Production-ready LLM-based fact extraction from Vietnamese criminal judgments."""

from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Any, Optional

from loguru import logger

from .schemas import CaseFacts, DefendantInfo, ExtractedField, ExtractionStatus

SYSTEM_PROMPT = """Bạn là chuyên gia phân tích bản án hình sự Việt Nam.
Nhiệm vụ: trích xuất thông tin có cấu trúc từ bản án.
Chỉ trích xuất thông tin được ghi rõ trong văn bản.
Nếu thông tin không có hoặc không rõ, đặt status = "missing".
Không suy diễn hoặc bịa đặt thông tin pháp lý.
Trả về JSON hợp lệ."""

HEADER_SECTION_PROMPT = """Bạn đang phân tích PHẦN MỞ ĐẦU của bản án hình sự Việt Nam.
Hãy trích xuất các trường thông tin sau:
- case_number: Số hiệu bản án (ví dụ: "01/2023/HS-ST")
- court_name: Tên Tòa án xét xử (ví dụ: "Tòa án nhân dân tỉnh Bình Định")
- court_level: Cấp Tòa án ("district", "provincial", "high", "supreme")
- judgment_date: Ngày ra bản án/ngày xét xử theo chuẩn ISO 8601 (YYYY-MM-DD)
- proceeding_stage: Giai đoạn tố tụng ("first_instance" cho sơ thẩm, "appeal" cho phúc thẩm)
- defendant_count: Số lượng bị cáo được xét xử

Quy tắc cấu trúc:
Mỗi trường phải là object JSON có dạng:
{{"value": "<giá trị>", "status": "extracted"|"inferred"|"missing"|"conflicting", "confidence": <float từ 0.0 đến 1.0>}}
Nếu văn bản không có thông tin, đặt status = "missing", value = null.

Đoạn văn bản Phần Mở Đầu:
{header_text}

JSON Schema tham chiếu của CaseFacts:
{case_facts_schema}

Trả về duy nhất JSON hợp lệ chứa các trường trên."""

BODY_SECTION_PROMPT = """Bạn đang phân tích PHẦN NỘI DUNG VỤ ÁN & NHẬN ĐỊNH của bản án hình sự Việt Nam.
Hãy trích xuất các trường thông tin sau:
- offense_date: Ngày/thời điểm bắt đầu thực hiện hành vi phạm tội (ISO 8601 nếu rõ, hoặc chuỗi ngày tháng)
- offense_end_date: Ngày/thời điểm kết thúc hành vi phạm tội (nếu hành vi kéo dài)
- damage_description: Mô tả thiệt hại vật chất hoặc phi vật chất
- damage_value_vnd: Giá trị thiệt hại tính bằng tiền VNĐ (dạng chuỗi)
- aggravating_factors: Danh sách các tình tiết tăng nặng trách nhiệm hình sự (theo Điều 52 BLHS)
- mitigating_factors: Danh sách các tình tiết giảm nhẹ trách nhiệm hình sự (theo Điều 51 BLHS)
- first_instance_verdict: Phán quyết sơ thẩm (nếu đây là bản án phúc thẩm ghi nhận)
- first_instance_sentence: Hình phạt sơ thẩm (nếu đây là bản án phúc thẩm ghi nhận)

Quy tắc cấu trúc:
Mỗi trường đơn là object JSON: {{"value": "<giá trị>", "status": "extracted"|"inferred"|"missing"|"conflicting", "confidence": <0.0-1.0>}}
Các trường danh sách (aggravating_factors, mitigating_factors) là mảng các object có cấu trúc trên.
Nếu không có thông tin, đặt status = "missing", value = null (với danh sách thì mảng rỗng []).

Đoạn văn bản Phần Nội Dung & Nhận Định:
{body_text}

JSON Schema tham chiếu của CaseFacts:
{case_facts_schema}

Trả về duy nhất JSON hợp lệ chứa các trường trên."""

VERDICT_SECTION_PROMPT = """Bạn đang phân tích PHẦN QUYẾT ĐỊNH của bản án hình sự Việt Nam.
Hãy trích xuất kết quả xét xử, tội danh, hình phạt và thông tin chi tiết từng bị cáo:
- charges: Danh sách tội danh mà Tòa án tuyên bố bị cáo phạm tội
- applied_articles: Danh sách các điều khoản luật hình sự được áp dụng (ví dụ: ["Điều 173 khoản 1 BLHS 2015"])
- first_instance_verdict: Kết quả phán quyết sơ thẩm (ví dụ: "có tội")
- first_instance_sentence: Hình phạt sơ thẩm tổng hợp
- has_appeal: Có kháng cáo/kháng nghị hay không ("true"/"false")
- appeal_type: Loại kháng cáo/kháng nghị (ví dụ: "Kháng cáo xin giảm nhẹ hình phạt")
- appeal_scope: Phạm vi kháng cáo (ví dụ: "Hình phạt", "Toàn bộ bản án")
- appellate_outcome: Kết quả xét xử phúc thẩm nếu là cấp phúc thẩm (ví dụ: "Giữ nguyên bản án sơ thẩm")
- defendants: Danh sách thông tin chi tiết của từng bị cáo theo DefendantInfo schema:
  Mỗi bị cáo gồm các trường:
  - name: Tên bị cáo
  - birth_year: Năm sinh
  - gender: Giới tính
  - prior_convictions: Tiền án, tiền sự
  - role_in_crime: Vai trò phạm tội (chủ mưu, thực hành, giúp sức, ...)
  - sentence_type: Loại hình phạt (tù có thời hạn, tù chung thân, án treo, phạt tiền, ...)
  - sentence_duration: Thời hạn hình phạt (ví dụ: "3 năm 6 tháng")
  - sentence_years: Số năm phạt tù quy đổi ra số thực (ví dụ: "3.5")
  - fine_amount: Số tiền phạt bổ sung nếu có
  - suspended: Có được hưởng án treo không ("true"/"false")

Mọi trường thông tin trong CaseFacts và DefendantInfo đều là object JSON:
{{"value": "<giá trị>", "status": "extracted"|"inferred"|"missing"|"conflicting", "confidence": <0.0-1.0>}}
Nếu không có thông tin, đặt status = "missing", value = null.

Đoạn văn bản Phần Quyết Định:
{verdict_text}

JSON Schema tham chiếu của CaseFacts:
{case_facts_schema}

JSON Schema tham chiếu của DefendantInfo:
{defendant_schema}

Trả về duy nhất JSON hợp lệ chứa các trường trên và mảng "defendants"."""

FULL_TEXT_PROMPT = """Bạn là chuyên gia phân tích bản án hình sự Việt Nam.
Hãy trích xuất tất cả các thông tin vụ án theo schema CaseFacts và danh sách bị cáo theo schema DefendantInfo.

Văn bản bản án:
{text}

JSON Schema tham chiếu của CaseFacts:
{case_facts_schema}

JSON Schema tham chiếu của DefendantInfo:
{defendant_schema}

Trả về duy nhất JSON hợp lệ bao gồm các trường của CaseFacts và mảng "defendants"."""


class CaseFactExtractor:
    """LLM-based structured fact extractor for Vietnamese criminal judgments."""

    def __init__(self, llm_service: Any = None) -> None:
        """Initialize CaseFactExtractor.

        Args:
            llm_service: Optional LLMService instance, created lazily if not provided.
        """
        if llm_service is not None:
            self.llm_service = llm_service
        else:
            try:
                from ..services.llm_service import LLMService

                self.llm_service = LLMService()
            except Exception as exc:
                logger.debug(f"Could not initialize LLMService during init: {exc}")
                self.llm_service = None

    def _get_llm_service(self) -> Any:
        """Lazy loader for LLMService."""
        if self.llm_service is not None:
            return self.llm_service
        try:
            from ..services.llm_service import LLMService

            self.llm_service = LLMService()
            return self.llm_service
        except Exception as exc:
            logger.debug(f"Lazy import of LLMService failed: {exc}")
            return None

    @staticmethod
    def _run_async(coro: Any) -> Any:
        """Execute a coroutine safely across both sync and running event loop contexts."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None and loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                return executor.submit(asyncio.run, coro).result()
        return asyncio.run(coro)

    def _call_llm(self, prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
        """Invoke the configured LLM service or fallback to litellm."""
        service = self._get_llm_service()
        if service is not None:
            for method_name in ("generate", "complete", "chat"):
                if hasattr(service, method_name):
                    method = getattr(service, method_name)
                    if asyncio.iscoroutinefunction(method):
                        return self._run_async(method(prompt, system_prompt=system_prompt))
                    return method(prompt, system_prompt=system_prompt)

            if callable(service):
                if asyncio.iscoroutinefunction(service):
                    return self._run_async(service(prompt, system_prompt=system_prompt))
                return service(prompt, system_prompt=system_prompt)

        # Fallback to direct litellm call
        try:
            import litellm

            response = litellm.completion(
                model="claude-3-5-haiku-20241022",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content or "{}"
        except Exception as exc:
            logger.warning(f"Direct litellm call failed: {exc}")
            raise

    @staticmethod
    def _clean_and_parse_json(raw_text: str) -> dict[str, Any]:
        """Parse raw response text into a JSON dict."""
        if not raw_text or not isinstance(raw_text, str):
            return {}
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
            if isinstance(parsed, list):
                return {"items": parsed}
        except json.JSONDecodeError:
            pass

        # Try regex search for outermost JSON object
        match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(1))
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass

        return {}

    def _extract_section_data(self, prompt: str) -> dict[str, Any]:
        """Call LLM with specialized prompt and parse JSON response."""
        try:
            raw_response = self._call_llm(prompt, system_prompt=SYSTEM_PROMPT)
            return self._clean_and_parse_json(raw_response)
        except Exception as exc:
            logger.error(f"Error during section LLM extraction: {exc}")
            return {}

    def _split_judgment_sections(self, text: str) -> dict:
        """Split text into sections using Vietnamese judgment patterns:
        - Header: up to "XÉT THẤY" or "NỘI DUNG VỤ ÁN"
        - Body: from header end to "QUYẾT ĐỊNH"
        - Verdict: from "QUYẾT ĐỊNH" to end
        """
        if not text:
            return {"header": "", "body": "", "verdict": ""}

        # Find header split point: first occurrence of "NỘI DUNG VỤ ÁN" or "XÉT THẤY"
        header_patterns = [r"NỘI\s+DUNG\s+VỤ\s+ÁN", r"XÉT\s+THẤY"]
        header_matches: list[int] = []
        for pattern in header_patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                header_matches.append(m.start())

        header_end = min(header_matches) if header_matches else 0

        # Find verdict split point: "QUYẾT ĐỊNH"
        verdict_matches = [
            m.start() for m in re.finditer(r"QUYẾT\s+ĐỊNH", text, re.IGNORECASE)
        ]

        verdict_start = len(text)
        for v_pos in verdict_matches:
            if v_pos >= header_end:
                verdict_start = v_pos
                break
        if verdict_start == len(text) and verdict_matches:
            verdict_start = verdict_matches[-1]

        header = text[:header_end].strip()
        body = text[header_end:verdict_start].strip()
        verdict = text[verdict_start:].strip()

        return {
            "header": header,
            "body": body,
            "verdict": verdict,
        }

    @staticmethod
    def _missing_field() -> ExtractedField:
        """Create a single ExtractedField with ExtractionStatus.MISSING."""
        return ExtractedField(value=None, status=ExtractionStatus.MISSING, confidence=None)

    @classmethod
    def _create_missing_casefacts(cls) -> CaseFacts:
        """Return CaseFacts with all fields set to ExtractionStatus.MISSING."""
        return CaseFacts(
            case_number=cls._missing_field(),
            court_name=cls._missing_field(),
            court_level=cls._missing_field(),
            judgment_date=cls._missing_field(),
            proceeding_stage=cls._missing_field(),
            charges=[],
            applied_articles=[],
            offense_date=cls._missing_field(),
            offense_end_date=cls._missing_field(),
            defendant_count=cls._missing_field(),
            damage_description=cls._missing_field(),
            damage_value_vnd=cls._missing_field(),
            aggravating_factors=[],
            mitigating_factors=[],
            first_instance_verdict=cls._missing_field(),
            first_instance_sentence=cls._missing_field(),
            has_appeal=cls._missing_field(),
            appeal_type=cls._missing_field(),
            appeal_scope=cls._missing_field(),
            appellate_outcome=cls._missing_field(),
        )

    @classmethod
    def _create_missing_defendant(cls) -> DefendantInfo:
        """Return DefendantInfo with all fields set to ExtractionStatus.MISSING."""
        return DefendantInfo(
            name=cls._missing_field(),
            birth_year=cls._missing_field(),
            gender=cls._missing_field(),
            prior_convictions=cls._missing_field(),
            role_in_crime=cls._missing_field(),
            sentence_type=cls._missing_field(),
            sentence_duration=cls._missing_field(),
            sentence_years=cls._missing_field(),
            fine_amount=cls._missing_field(),
            suspended=cls._missing_field(),
        )

    @classmethod
    def _normalize_extracted_field(cls, raw: Any) -> dict[str, Any]:
        """Normalize raw value into ExtractedField payload dict."""
        if isinstance(raw, ExtractedField):
            return raw.model_dump()
        if isinstance(raw, dict):
            status = raw.get("status")
            valid_statuses = {s.value for s in ExtractionStatus}
            if status not in valid_statuses:
                status = (
                    ExtractionStatus.EXTRACTED.value
                    if raw.get("value") is not None
                    else ExtractionStatus.MISSING.value
                )
            confidence = raw.get("confidence")
            if confidence is not None:
                try:
                    confidence = float(confidence)
                except (ValueError, TypeError):
                    confidence = None
            val = str(raw["value"]) if raw.get("value") is not None else None
            if status == ExtractionStatus.MISSING.value or status == ExtractionStatus.MISSING:
                val = None
            return {
                "value": val,
                "status": status,
                "source_page": raw.get("source_page"),
                "source_paragraph": raw.get("source_paragraph"),
                "confidence": confidence,
            }
        if raw is None:
            return {
                "value": None,
                "status": ExtractionStatus.MISSING.value,
                "confidence": None,
            }
        return {
            "value": str(raw),
            "status": ExtractionStatus.EXTRACTED.value,
            "confidence": 0.9,
        }

    @classmethod
    def _normalize_extracted_list(cls, raw_list: Any) -> list[dict[str, Any]]:
        """Normalize raw list into list of ExtractedField payload dicts."""
        if not isinstance(raw_list, list):
            if raw_list is None:
                return []
            raw_list = [raw_list]
        return [cls._normalize_extracted_field(item) for item in raw_list]

    @classmethod
    def _normalize_casefacts_dict(cls, raw_dict: dict[str, Any]) -> dict[str, Any]:
        """Normalize all CaseFacts fields prior to model_validate()."""
        list_fields = {
            "charges",
            "applied_articles",
            "aggravating_factors",
            "mitigating_factors",
        }
        normalized: dict[str, Any] = {}
        for field_name in CaseFacts.model_fields:
            val = raw_dict.get(field_name)
            if field_name in list_fields:
                normalized[field_name] = cls._normalize_extracted_list(val)
            else:
                normalized[field_name] = cls._normalize_extracted_field(val)
        return normalized

    @classmethod
    def _normalize_defendant_dict(cls, raw_dict: dict[str, Any]) -> dict[str, Any]:
        """Normalize all DefendantInfo fields prior to model_validate()."""
        normalized: dict[str, Any] = {}
        for field_name in DefendantInfo.model_fields:
            val = raw_dict.get(field_name)
            normalized[field_name] = cls._normalize_extracted_field(val)
        return normalized

    def _parse_casefacts_from_llm(self, response_json: dict) -> CaseFacts:
        """Parse LLM JSON response into CaseFacts using model_validate().

        On parse error: return CaseFacts with all fields set to ExtractionStatus.MISSING.
        """
        if not isinstance(response_json, dict):
            logger.error(f"Expected dict for CaseFacts response, got {type(response_json)}")
            return self._create_missing_casefacts()

        try:
            normalized = self._normalize_casefacts_dict(response_json)
            return CaseFacts.model_validate(normalized)
        except Exception as exc:
            logger.error(f"Error validating CaseFacts from LLM response: {exc}")
            return self._create_missing_casefacts()

    def _parse_defendants_from_llm(self, response_data: Any) -> list[DefendantInfo]:
        """Extract defendant info using DefendantInfo schema and model_validate()."""
        if not response_data:
            return []
        items: list[Any] = []
        if isinstance(response_data, list):
            items = response_data
        elif isinstance(response_data, dict):
            if "defendants" in response_data and isinstance(response_data["defendants"], list):
                items = response_data["defendants"]
            else:
                items = [response_data]
        else:
            return []

        results: list[DefendantInfo] = []
        for item in items:
            if isinstance(item, dict):
                try:
                    norm = self._normalize_defendant_dict(item)
                    results.append(DefendantInfo.model_validate(norm))
                except Exception as exc:
                    logger.warning(f"Failed to validate DefendantInfo: {exc}")
                    results.append(self._create_missing_defendant())
        return results

    @staticmethod
    def _calculate_overall_confidence(
        case_facts: CaseFacts, defendants: list[DefendantInfo]
    ) -> float | None:
        """Compute the mean of all non-None confidence values across extracted fields."""
        confidences: list[float] = []

        def _collect(field: Any) -> None:
            if isinstance(field, ExtractedField):
                if field.confidence is not None:
                    try:
                        confidences.append(float(field.confidence))
                    except (ValueError, TypeError):
                        pass
            elif isinstance(field, list):
                for item in field:
                    _collect(item)

        for field_name in case_facts.model_fields:
            _collect(getattr(case_facts, field_name, None))

        for defendant in defendants:
            for field_name in defendant.model_fields:
                _collect(getattr(defendant, field_name, None))

        if not confidences:
            return None
        return sum(confidences) / len(confidences)

    def extract(
        self, text: str, judgment_id: str = None
    ) -> tuple[CaseFacts, list[DefendantInfo]]:
        """Extract structured case facts and defendant info from Vietnamese judgment text.

        Args:
            text: Raw judgment text
            judgment_id: Optional judgment identifier for logging

        Returns:
            Tuple of (CaseFacts, list[DefendantInfo])
        """
        start_time = time.monotonic()
        if not text or not text.strip():
            logger.warning(f"Empty text provided for fact extraction (id={judgment_id})")
            missing_cf = self._create_missing_casefacts()
            elapsed_ms = (time.monotonic() - start_time) * 1000
            logger.info(
                f"Extraction for judgment_id={judgment_id} finished in {elapsed_ms:.2f}ms | overall confidence: None"
            )
            return missing_cf, []

        try:
            sections = self._split_judgment_sections(text)
            header_text = sections.get("header", "").strip()
            body_text = sections.get("body", "").strip()
            verdict_text = sections.get("verdict", "").strip()

            combined_raw: dict[str, Any] = {}
            raw_defendants: list[Any] = []

            # Build JSON schema from CaseFacts and DefendantInfo models
            case_facts_schema_str = json.dumps(
                CaseFacts.model_json_schema(), ensure_ascii=False
            )
            defendant_schema_str = json.dumps(
                DefendantInfo.model_json_schema(), ensure_ascii=False
            )

            if header_text or verdict_text:
                if header_text:
                    h_prompt = HEADER_SECTION_PROMPT.format(
                        header_text=header_text[:6000],
                        case_facts_schema=case_facts_schema_str,
                    )
                    header_res = self._extract_section_data(h_prompt)
                    combined_raw.update(header_res)
                    if "defendants" in header_res and isinstance(header_res["defendants"], list):
                        raw_defendants.extend(header_res["defendants"])

                if body_text:
                    b_prompt = BODY_SECTION_PROMPT.format(
                        body_text=body_text[:8000],
                        case_facts_schema=case_facts_schema_str,
                    )
                    body_res = self._extract_section_data(b_prompt)
                    combined_raw.update(body_res)

                if verdict_text:
                    v_prompt = VERDICT_SECTION_PROMPT.format(
                        verdict_text=verdict_text[:6000],
                        case_facts_schema=case_facts_schema_str,
                        defendant_schema=defendant_schema_str,
                    )
                    verdict_res = self._extract_section_data(v_prompt)
                    combined_raw.update(verdict_res)
                    if "defendants" in verdict_res and isinstance(verdict_res["defendants"], list):
                        raw_defendants.extend(verdict_res["defendants"])
            else:
                f_prompt = FULL_TEXT_PROMPT.format(
                    text=text[:10000],
                    case_facts_schema=case_facts_schema_str,
                    defendant_schema=defendant_schema_str,
                )
                full_res = self._extract_section_data(f_prompt)
                combined_raw.update(full_res)
                if "defendants" in full_res and isinstance(full_res["defendants"], list):
                    raw_defendants.extend(full_res["defendants"])

            case_facts = self._parse_casefacts_from_llm(combined_raw)
            defendants = self._parse_defendants_from_llm(raw_defendants)

            elapsed_ms = (time.monotonic() - start_time) * 1000
            overall_confidence = self._calculate_overall_confidence(case_facts, defendants)

            if overall_confidence is not None:
                logger.info(
                    f"Extraction for judgment_id={judgment_id} completed in {elapsed_ms:.2f}ms | overall confidence: {overall_confidence:.4f}"
                )
            else:
                logger.info(
                    f"Extraction for judgment_id={judgment_id} completed in {elapsed_ms:.2f}ms | overall confidence: None"
                )

            return case_facts, defendants

        except Exception as exc:
            elapsed_ms = (time.monotonic() - start_time) * 1000
            logger.error(f"Fact extraction failed for judgment_id={judgment_id}: {exc}")
            missing_cf = self._create_missing_casefacts()
            logger.info(
                f"Extraction for judgment_id={judgment_id} failed in {elapsed_ms:.2f}ms | overall confidence: None"
            )
            return missing_cf, []
