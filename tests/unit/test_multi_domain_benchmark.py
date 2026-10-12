"""Unit tests kiểm thử độ chính xác của Benchmark Đa Lĩnh vực (Multi-Domain Legal Benchmark).

Đảm bảo:
1. 100% hồ sơ benchmark được nhận diện đúng lĩnh vực pháp luật (Domain Classification).
2. 100% hồ sơ tuân thủ các quy tắc định chuẩn pháp định (Statutory Compliance).
3. Hệ thống hình phạt Điều 32 BLHS được áp dụng đúng chuẩn.
4. Trần lãi suất 20% BLDS, án phí NQ 326, trần phạt 8% LTM, thời hiệu LTTHC, điều cấm BLLĐ hoạt động chính xác.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.evaluate_multi_domain import evaluate_case

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_PATH = PROJECT_ROOT / "data" / "multi_domain_benchmark.json"


def test_benchmark_file_structure():
    """Kiểm tra cấu trúc và tính đầy đủ của file multi_domain_benchmark.json."""
    assert BENCHMARK_PATH.exists()
    with open(BENCHMARK_PATH, encoding="utf-8") as f:
        data = json.load(f)

    assert data["version"] == "1.0.0"
    assert len(data["domains_covered"]) == 5
    assert data["total_cases"] == 11
    assert len(data["cases"]) == 11


def test_benchmark_all_cases_statutory_compliance():
    """Kiểm tra toàn bộ 11 hồ sơ benchmark đều đạt chuẩn quy định pháp lý 100%."""
    with open(BENCHMARK_PATH, encoding="utf-8") as f:
        data = json.load(f)

    cases = data["cases"]
    for c in cases:
        eval_result = evaluate_case(c)
        assert eval_result["domain_match"] is True, f"Sai domain cho case {c['id']}: kỳ vọng {c['domain']}, nhận được {eval_result['predicted_domain']}"
        assert eval_result["passed"] is True, f"Không đạt chuẩn quy phạm cho case {c['id']}: {eval_result['checks']}"
