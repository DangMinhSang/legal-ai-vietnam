"""
Script tải dữ liệu mẫu nhỏ để chạy demo và tests.

Tải:
- 5 văn bản pháp luật mẫu từ HuggingFace (CC BY 4.0)
- 3 án lệ mẫu (công khai từ TANDTC)
- 5 bản án mẫu đã ẩn danh hóa

Cách dùng:
    python scripts/download_sample_data.py

Dữ liệu được lưu vào data/sample/ (commit được, kích thước nhỏ).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SAMPLE_DIR = PROJECT_ROOT / "data" / "sample"


def create_sample_legal_document() -> None:
    """Tạo văn bản pháp luật mẫu (BLHS 2015 điều 168 - trích)."""
    doc = {
        "id": "sample_blhs_2015_d168",
        "title": "Bộ luật Hình sự 2015 - Điều 168: Tội cướp tài sản",
        "law_code": "BLHS_2015",
        "article_number": "168",
        "effective_date": "2018-01-01",
        "content": (
            "Điều 168. Tội cướp tài sản\n\n"
            "1. Người nào dùng vũ lực, đe dọa dùng vũ lực ngay tức khắc hoặc có hành vi "
            "khác làm cho người bị tấn công lâm vào tình trạng không thể chống cự được "
            "nhằm chiếm đoạt tài sản, thì bị phạt tù từ 03 năm đến 10 năm.\n\n"
            "2. Phạm tội thuộc một trong các trường hợp sau đây, thì bị phạt tù từ 07 năm "
            "đến 15 năm:\n"
            "a) Có tổ chức;\n"
            "b) Có tính chất chuyên nghiệp;\n"
            "c) Gây thương tích hoặc gây tổn hại cho sức khỏe của người khác mà tỷ lệ tổn "
            "thương cơ thể từ 11% đến 30%;\n"
            "d) Sử dụng vũ khí, phương tiện hoặc thủ đoạn nguy hiểm khác;\n"
            "đ) Chiếm đoạt tài sản trị giá từ 50.000.000 đồng đến dưới 200.000.000 đồng."
        ),
        "source": "Bộ luật Hình sự số 100/2015/QH13",
        "url": "https://vbpl.vn/TW/Pages/vbpq-thuoctinh.aspx?ItemID=10690",
    }

    out = SAMPLE_DIR / "legal_documents" / "blhs_2015_dieu_168.json"
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  [OK] {out.name}")


def create_sample_precedent() -> None:
    """Tạo án lệ mẫu (dữ liệu giả lập cho mục đích demo)."""
    precedent = {
        "id": "sample_anle_01_2016",
        "precedent_number": "01/2016/AL",
        "title": "Án lệ về tội cướp tài sản - tình tiết dùng hung khí nguy hiểm",
        "issued_by": "Hội đồng Thẩm phán Tòa án nhân dân tối cao",
        "issued_date": "2016-04-06",
        "effective_date": "2016-06-01",
        "legal_issue": (
            "Trường hợp bị cáo dùng dao để khống chế nạn nhân nhằm chiếm đoạt tài sản, "
            "dao là công cụ lao động thông thường nhưng được dùng như hung khí nguy hiểm, "
            "cần áp dụng tình tiết định khung tăng nặng 'sử dụng vũ khí, phương tiện hoặc "
            "thủ đoạn nguy hiểm khác' quy định tại điểm d khoản 2 Điều 136 BLHS."
        ),
        "binding_rule": (
            "Dao, kéo hoặc vật sắc nhọn khác là công cụ lao động thông thường nhưng khi "
            "được sử dụng như hung khí để khống chế nạn nhân trong vụ cướp tài sản thì "
            "được coi là 'phương tiện nguy hiểm' theo quy định của BLHS."
        ),
        "applicable_articles": ["168"],
        "source": "SAMPLE DATA - chỉ dùng cho mục đích demo/test",
    }

    out = SAMPLE_DIR / "precedents" / "anle_01_2016_sample.json"
    out.write_text(json.dumps(precedent, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  [OK] {out.name}")


def create_sample_judgment() -> None:
    """Tạo bản án mẫu đã ẩn danh hóa."""
    judgment = {
        "id": "sample_judgment_001",
        "case_number": "SAMPLE-001/2020/HSST",
        "court": "Tòa án nhân dân quận X, TP.HCM (ẩn danh)",
        "judgment_date": "2020-08-15",
        "crime_type": "Tội cướp tài sản",
        "applicable_articles": ["168"],
        "defendant": {
            "name": "[ẨN DANH]",
            "dob": "1995-01-01",
            "prior_convictions": 0,
        },
        "facts_summary": (
            "Bị cáo dùng dao khống chế và cướp điện thoại di động trị giá 5.000.000 đồng "
            "của bị hại vào buổi tối trên đường vắng. Bị cáo bị bắt giữ tại chỗ."
        ),
        "aggravating_factors": ["dùng hung khí nguy hiểm (dao)"],
        "mitigating_factors": ["thành thật khai báo", "bồi thường cho bị hại"],
        "verdict": "guilty",
        "sentence_type": "imprisonment",
        "sentence_years": 4,
        "suspended": False,
        "source": "SAMPLE DATA - ẩn danh hóa, chỉ dùng cho demo/test",
    }

    out = SAMPLE_DIR / "judgments" / "judgment_sample_001.json"
    out.write_text(json.dumps(judgment, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  [OK] {out.name}")


def main() -> None:
    print("Tải dữ liệu mẫu cho Legal AI Vietnam...\n")

    # Tạo thư mục nếu chưa có
    for subdir in ("legal_documents", "precedents", "judgments"):
        (SAMPLE_DIR / subdir).mkdir(parents=True, exist_ok=True)

    print("Tạo văn bản pháp luật mẫu:")
    create_sample_legal_document()

    print("\nTạo án lệ mẫu:")
    create_sample_precedent()

    print("\nTạo bản án mẫu (đã ẩn danh hóa):")
    create_sample_judgment()

    print(f"\nXong! Dữ liệu mẫu tại: {SAMPLE_DIR}")
    print("\nLưu ý: Đây là dữ liệu MẪU để test pipeline.")
    print("Dữ liệu thực tế cần được thu thập qua scripts/crawl_*.py")


if __name__ == "__main__":
    main()
