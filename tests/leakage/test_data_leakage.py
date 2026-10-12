"""Tests for preventing data leakage in Legal AI Vietnam pipelines."""

from __future__ import annotations

from datetime import datetime

from src.validation.leakage import (
    build_appeal_features,
    build_first_instance_features,
    split_cases_by_case_id,
    temporal_split,
)


class TestDataLeakage:
    """Test suite detecting target leakage and contamination across dataset splits."""

    def test_first_instance_features_no_outcome(self):
        """Feature set cho dự đoán sơ thẩm không được chứa kết quả sơ thẩm."""
        case_with_outcome = {
            "case_code": "HSST-01",
            "charges": ["Điều 173 BLHS"],
            "defendant_age": 30,
            "prior_convictions": 0,
            "damage_vnd": 25000000,
            # Target labels that must NOT leak into feature matrix
            "verdict": "co_toi",
            "sentence_years": 1.5,
            "sentence_type": "tu_giam",
            "first_instance_verdict": "guilty",
            "first_instance_sentence": "1 năm 6 tháng tù",
        }

        features = build_first_instance_features(case_with_outcome)

        assert "verdict" not in features
        assert "sentence_years" not in features
        assert "sentence_type" not in features
        assert "first_instance_verdict" not in features
        assert "first_instance_sentence" not in features
        # Valid features must remain
        assert features["case_code"] == "HSST-01"
        assert features["defendant_age"] == 30
        assert features["damage_vnd"] == 25000000

    def test_appeal_features_no_appellate_outcome(self):
        """Feature set cho dự đoán phúc thẩm không được chứa kết quả phúc thẩm."""
        case_with_appeal = {
            "case_code": "HSPT-02",
            "first_instance_sentence_years": 2.0,
            "appeal_grounds": "Xin giảm nhẹ hình phạt",
            "has_new_mitigating_factors": True,
            # Target labels for appellate court that must NOT leak
            "appellate_outcome": "giam_an",
            "appeal_result": "modified",
            "is_upheld": False,
            "modified_sentence": "1 năm tù",
        }

        features = build_appeal_features(case_with_appeal)

        assert "appellate_outcome" not in features
        assert "appeal_result" not in features
        assert "is_upheld" not in features
        assert "modified_sentence" not in features
        # Inputs from first instance are valid and preserved
        assert features["first_instance_sentence_years"] == 2.0
        assert features["appeal_grounds"] == "Xin giảm nhẹ hình phạt"

    def test_case_split_no_cross_contamination(self):
        """Các tài liệu cùng vụ án phải ở cùng tập train/val/test."""
        # 3 cases, each with first instance and appeal judgments
        documents = [
            {"id": "doc_1a", "case_id": "case_1", "stage": "first_instance"},
            {"id": "doc_1b", "case_id": "case_1", "stage": "appeal"},
            {"id": "doc_2a", "case_id": "case_2", "stage": "first_instance"},
            {"id": "doc_2b", "case_id": "case_2", "stage": "appeal"},
            {"id": "doc_3a", "case_id": "case_3", "stage": "first_instance"},
            {"id": "doc_3b", "case_id": "case_3", "stage": "appeal"},
        ]

        train_docs, test_docs = split_cases_by_case_id(documents, train_ratio=0.67)

        train_case_ids = {d["case_id"] for d in train_docs}
        test_case_ids = {d["case_id"] for d in test_docs}

        # No intersection between train and test cases
        overlap = train_case_ids.intersection(test_case_ids)
        assert len(overlap) == 0, f"Found overlapping cases across splits: {overlap}"

        # Total document count must be conserved
        assert len(train_docs) + len(test_docs) == len(documents)

    def test_temporal_split_ordering(self):
        """Train set chỉ chứa bản án cũ hơn test set."""
        cutoff_date = "2023-01-01"
        cases = [
            {"id": "c1", "judgment_date": "2021-05-10"},
            {"id": "c2", "judgment_date": "2022-12-15"},
            {"id": "c3", "judgment_date": "2023-03-20"},
            {"id": "c4", "judgment_date": "2023-08-01"},
        ]

        train_cases, test_cases = temporal_split(cases, split_date=cutoff_date)

        cutoff_dt = datetime.fromisoformat(cutoff_date)

        for c in train_cases:
            assert datetime.fromisoformat(c["judgment_date"]) < cutoff_dt
        for c in test_cases:
            assert datetime.fromisoformat(c["judgment_date"]) >= cutoff_dt
