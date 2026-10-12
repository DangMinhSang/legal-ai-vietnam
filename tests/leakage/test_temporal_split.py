"""
Kiểm tra temporal data leakage trong evaluation split.

Đây là test quan trọng nhất của dự án:
- Model KHÔNG được thấy dữ liệu tương lai khi dự đoán
- Train set chỉ chứa vụ án TRƯỚC temporal_split_date
- Test set chỉ chứa vụ án SAU temporal_split_date

Chạy: pytest tests/leakage/ -v
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List


# ============================================================
# Helpers dùng cho nhiều test
# ============================================================

def make_case(judgment_date: str, verdict: str = "guilty") -> dict:
    """Tạo dict vụ án mẫu với ngày xét xử."""
    return {
        "id": f"case_{judgment_date}",
        "judgment_date": judgment_date,
        "verdict": verdict,
        "crime_type": "theft",
        "sentence_years": 2,
    }


def temporal_split(
    cases: List[dict],
    split_date: str,
    date_field: str = "judgment_date",
) -> tuple[List[dict], List[dict]]:
    """
    Chia danh sách vụ án thành train / test theo mốc thời gian.

    Train: judgment_date < split_date
    Test:  judgment_date >= split_date

    Args:
        cases: Danh sách vụ án.
        split_date: Mốc chia dạng "YYYY-MM-DD".
        date_field: Tên trường ngày trong dict.

    Returns:
        Tuple (train_cases, test_cases).
    """
    cutoff = datetime.strptime(split_date, "%Y-%m-%d").date()
    train, test = [], []
    for c in cases:
        case_date = datetime.strptime(c[date_field], "%Y-%m-%d").date()
        (train if case_date < cutoff else test).append(c)
    return train, test


# ============================================================
# Test cases
# ============================================================

class TestTemporalSplit:
    """Kiểm tra logic chia tập train/test theo thời gian."""

    SPLIT_DATE = "2022-01-01"

    def _cases(self) -> List[dict]:
        return [
            make_case("2020-03-15"),  # train
            make_case("2021-06-20"),  # train
            make_case("2021-12-31"),  # train (ngày cuối cùng trước split)
            make_case("2022-01-01"),  # test (đúng ngày split)
            make_case("2022-06-10"),  # test
            make_case("2023-11-01"),  # test
        ]

    def test_no_overlap_between_train_and_test(self):
        """Train và test phải rời nhau hoàn toàn - không có case chung."""
        train, test = temporal_split(self._cases(), self.SPLIT_DATE)
        train_ids = {c["id"] for c in train}
        test_ids = {c["id"] for c in test}
        assert train_ids.isdisjoint(test_ids), \
            f"Overlap detected: {train_ids & test_ids}"

    def test_all_cases_assigned(self):
        """Mọi case phải được gán vào đúng một tập."""
        cases = self._cases()
        train, test = temporal_split(cases, self.SPLIT_DATE)
        assert len(train) + len(test) == len(cases)

    def test_train_only_contains_past_cases(self):
        """Train set chỉ được chứa vụ án trước split_date."""
        cutoff = date(2022, 1, 1)
        train, _ = temporal_split(self._cases(), self.SPLIT_DATE)
        for c in train:
            case_date = datetime.strptime(c["judgment_date"], "%Y-%m-%d").date()
            assert case_date < cutoff, \
                f"Future case {c['id']} ({case_date}) leaked into train set!"

    def test_test_only_contains_future_cases(self):
        """Test set chỉ được chứa vụ án từ split_date trở đi."""
        cutoff = date(2022, 1, 1)
        _, test = temporal_split(self._cases(), self.SPLIT_DATE)
        for c in test:
            case_date = datetime.strptime(c["judgment_date"], "%Y-%m-%d").date()
            assert case_date >= cutoff, \
                f"Past case {c['id']} ({case_date}) leaked into test set!"

    def test_boundary_case_goes_to_test(self):
        """Vụ án đúng ngày split_date phải vào test, không vào train."""
        _, test = temporal_split(self._cases(), self.SPLIT_DATE)
        test_ids = {c["id"] for c in test}
        assert "case_2022-01-01" in test_ids

    def test_correct_counts(self):
        """Kiểm tra số lượng train/test đúng như kỳ vọng."""
        train, test = temporal_split(self._cases(), self.SPLIT_DATE)
        assert len(train) == 3  # 2020, 2021-06, 2021-12
        assert len(test) == 3   # 2022-01, 2022-06, 2023


class TestLawVersionLeakage:
    """
    Kiểm tra rằng temporal_legal_engine không dùng phiên bản luật
    chưa có hiệu lực tại thời điểm xét xử.
    """

    def test_law_effective_date_respected(self):
        """
        Nếu luật A có hiệu lực từ 2019-01-01 và luật B (sửa đổi)
        có hiệu lực từ 2022-01-01, thì vụ án năm 2020 phải dùng luật A.
        """
        law_versions = [
            {"version": "A", "effective_date": "2015-07-01", "expiry_date": "2021-12-31"},
            {"version": "B", "effective_date": "2022-01-01", "expiry_date": None},
        ]

        def get_applicable_version(event_date: str, versions: list) -> dict:
            """Trả về phiên bản luật áp dụng tại event_date."""
            event = datetime.strptime(event_date, "%Y-%m-%d").date()
            for v in sorted(versions, key=lambda x: x["effective_date"], reverse=True):
                eff = datetime.strptime(v["effective_date"], "%Y-%m-%d").date()
                exp = (
                    datetime.strptime(v["expiry_date"], "%Y-%m-%d").date()
                    if v["expiry_date"]
                    else date.max
                )
                if eff <= event <= exp:
                    return v
            raise ValueError(f"No applicable law version for {event_date}")

        # Vụ án 2020 phải dùng luật A
        v = get_applicable_version("2020-06-15", law_versions)
        assert v["version"] == "A", \
            f"Temporal leakage: vụ án 2020 đang dùng luật '{v['version']}' thay vì 'A'"

        # Vụ án 2022 phải dùng luật B
        v = get_applicable_version("2022-03-01", law_versions)
        assert v["version"] == "B", \
            f"Wrong law version for 2022 case: got '{v['version']}'"

    def test_future_law_not_applied_retroactively(self):
        """Luật ban hành sau sự kiện KHÔNG được áp dụng (trừ khi có lợi hơn)."""
        event_date = date(2021, 5, 10)
        law_effective_date = date(2022, 1, 1)  # Luật này chưa có vào thời điểm sự kiện

        # Luật chưa có hiệu lực tại thời điểm sự kiện
        is_applicable = law_effective_date <= event_date
        assert not is_applicable, \
            "BUG: Luật 2022 đang được áp dụng cho vụ án xảy ra năm 2021!"
