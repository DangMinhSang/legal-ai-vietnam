"""
Unit tests for src.services.llm_service.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from src.services.llm_service import LLMService


class TestLLMService:
    """Unit tests for LLMService."""

    def test_initialization(self):
        service = LLMService(
            primary_model="claude-3-5-sonnet-20241022",
            fallback_model="gpt-4o-mini",
            max_tokens=2048,
            timeout=45,
        )
        assert service.primary_model == "claude-3-5-sonnet-20241022"
        assert service.fallback_model == "gpt-4o-mini"
        assert service.max_tokens == 2048
        assert service.timeout == 45

    def test_complete_success(self):
        service = LLMService()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Phân tích bản án thành công."))]
        mock_response.usage = MagicMock(prompt_tokens=50, completion_tokens=20, total_tokens=70)

        with patch("litellm.completion", return_value=mock_response) as mock_comp:
            with patch("litellm.completion_cost", return_value=0.00015):
                output = service.complete(
                    prompt="Tóm tắt bản án",
                    system="Bạn là trợ lý pháp lý",
                    temperature=0.2,
                )
                assert output == "Phân tích bản án thành công."
                mock_comp.assert_called_once()
                call_kwargs = mock_comp.call_args[1]
                assert call_kwargs["model"] == "claude-3-5-sonnet-20241022"
                assert call_kwargs["temperature"] == 0.2
                assert call_kwargs["timeout"] == 60

    def test_fallback_on_primary_failure(self):
        service = LLMService()
        mock_fallback_resp = MagicMock()
        mock_fallback_resp.choices = [MagicMock(message=MagicMock(content="Phản hồi từ GPT-4o-mini."))]
        mock_fallback_resp.usage = MagicMock(prompt_tokens=40, completion_tokens=15, total_tokens=55)

        def mock_completion(*args, **kwargs):
            if kwargs.get("model") == "claude-3-5-sonnet-20241022":
                raise RuntimeError("Claude API RateLimitExceeded")
            return mock_fallback_resp

        with patch("litellm.completion", side_effect=mock_completion) as mock_comp:
            with patch("litellm.completion_cost", return_value=0.00008):
                output = service.complete(prompt="Kiểm tra fallback")
                assert output == "Phản hồi từ GPT-4o-mini."
                models_invoked = [c[1]["model"] for c in mock_comp.call_args_list]
                assert "gpt-4o-mini" in models_invoked

    def test_complete_structured(self):
        service = LLMService()
        expected_dict = {"legal_status": "valid", "confidence": 0.95}
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps(expected_dict)))]
        mock_response.usage = MagicMock(prompt_tokens=30, completion_tokens=15, total_tokens=45)

        with patch("litellm.completion", return_value=mock_response):
            with patch("litellm.completion_cost", return_value=0.0001):
                schema = {"legal_status": "string", "confidence": "float"}
                result = service.complete_structured(
                    prompt="Đánh giá tính hiệu lực",
                    response_schema=schema,
                )
                assert result == expected_dict

    def test_parse_json_markdown_block(self):
        service = LLMService()
        markdown_text = '```json\n{"defendant": "Nguyễn Văn A", "age": 30}\n```'
        result = service._parse_json_response(markdown_text)
        assert result == {"defendant": "Nguyễn Văn A", "age": 30}

    def test_parse_json_graceful_error(self):
        service = LLMService()
        malformed = "Văn bản này không phải là JSON hợp lệ."
        result = service._parse_json_response(malformed)
        assert isinstance(result, dict)
        assert "error" in result

    def test_extract_entities(self):
        service = LLMService()
        extracted_mock = {
            "court": ["Tòa án nhân dân quận Hoàn Kiếm"],
            "crime": ["Cố ý gây thương tích"],
        }
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps(extracted_mock)))]
        mock_response.usage = MagicMock(prompt_tokens=60, completion_tokens=25, total_tokens=85)

        with patch("litellm.completion", return_value=mock_response):
            with patch("litellm.completion_cost", return_value=0.00018):
                entities = service.extract_entities(
                    text="TAND quận Hoàn Kiếm xử tội Cố ý gây thương tích.",
                    entity_types=["court", "crime", "statute"],
                )
                assert entities["court"] == ["Tòa án nhân dân quận Hoàn Kiếm"]
                assert entities["crime"] == ["Cố ý gây thương tích"]
                assert entities["statute"] == []
