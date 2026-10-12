"""
Kiểm tra cơ bản cho module config/settings.py.

Chạy: pytest tests/unit/test_settings.py -v
"""

from __future__ import annotations

import os
import pytest
from unittest.mock import patch


def test_get_settings_returns_singleton():
    """get_settings() phải trả về cùng một object (lru_cache)."""
    from config.settings import get_settings

    get_settings.cache_clear()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_default_values_are_valid():
    """Settings mặc định phải hợp lệ (không raise exception)."""
    from config.settings import get_settings

    get_settings.cache_clear()
    s = get_settings()
    assert s.app.app_name == "Legal AI Vietnam"
    assert s.llm.llm_temperature == 0.1
    assert s.embedding.embedding_dim == 768
    assert s.evaluation.temporal_split_date == "2022-01-01"


def test_empty_api_keys_become_none():
    """Chuỗi rỗng và placeholder phải được convert thành None."""
    from config.settings import get_settings

    get_settings.cache_clear()
    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "your_anthropic_api_key_here",
        "OPENAI_API_KEY": "",
    }):
        get_settings.cache_clear()
        s = get_settings()
        assert s.llm.anthropic_api_key is None
        assert s.llm.openai_api_key is None
        assert not s.llm.has_any_llm
    get_settings.cache_clear()


def test_real_api_key_detected():
    """API key thực phải được nhận dạng đúng."""
    from config.settings import get_settings

    get_settings.cache_clear()
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test123"}):
        get_settings.cache_clear()
        s = get_settings()
        assert s.llm.has_anthropic
        assert s.llm.has_any_llm
    get_settings.cache_clear()


def test_cors_origins_parsed_correctly():
    """CORS origins phải được split đúng từ chuỗi comma-separated."""
    from config.settings import get_settings

    get_settings.cache_clear()
    with patch.dict(os.environ, {
        "CORS_ORIGINS": "http://localhost:3000,http://localhost:8080,https://example.com"
    }):
        get_settings.cache_clear()
        s = get_settings()
        assert len(s.app.cors_origins_list) == 3
        assert "http://localhost:3000" in s.app.cors_origins_list
    get_settings.cache_clear()


def test_invalid_log_level_raises():
    """Log level không hợp lệ phải raise ValidationError."""
    from pydantic import ValidationError
    from config.settings import AppSettings

    with pytest.raises((ValidationError, ValueError)):
        AppSettings(log_level="VERBOSE")


def test_temporal_split_date_format_validated():
    """temporal_split_date không đúng format phải raise lỗi."""
    from pydantic import ValidationError
    from config.settings import EvaluationSettings

    with pytest.raises((ValidationError, ValueError)):
        EvaluationSettings(temporal_split_date="01/01/2022")


def test_project_root_exists():
    """project_root phải trỏ đến thư mục tồn tại."""
    from config.settings import get_settings

    get_settings.cache_clear()
    s = get_settings()
    assert s.project_root.exists()
    assert s.project_root.is_dir()
