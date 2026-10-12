"""Module trích xuất đặc trưng và phân tích từ 2 khung nhập liệu:
1. Thông tin cá nhân (Bị cáo, Bị hại, nhiều đương sự)
2. Thông tin vụ án (Hành vi, thời gian, công cụ, hậu quả, tình tiết tăng nặng/giảm nhẹ)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from scripts.train_baseline_models import STATUTORY_PENALTY_BOUNDS


@dataclass
class PartyInfo:
    """Thông tin một đương sự trong vụ án (Bị cáo hoặc Bị hại)."""

    name: str
    role: str  # "Bị cáo" hoặc "Bị hại"
    details: str = ""
    prior_convictions: int = 0
    is_recidivist: bool = False


@dataclass
class ParsedCaseInput:
    """Kết quả phân tích từ 2 khung nhập liệu."""

    parties: list[PartyInfo]
    defendants: list[PartyInfo]
    victims: list[PartyInfo]
    incident_date: date
    judgment_date: date
    detected_crime_name: str
    detected_articles: list[str]
    aggravating_factors: list[str]
    mitigating_factors: list[str]
    features: dict[str, float]
    combined_description: str


def parse_dates_from_text(text: str) -> date | None:
    """Trích xuất ngày tháng từ văn bản tiếng Việt."""
    # Pattern 1: dd/mm/yyyy hoặc dd-mm-yyyy
    m1 = re.search(r"(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})", text)
    if m1:
        d, m, y = int(m1.group(1)), int(m1.group(2)), int(m1.group(3))
        try:
            return date(y, m, d)
        except ValueError:
            pass

    # Pattern 2: ngày d tháng m năm yyyy
    m2 = re.search(r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})", text, re.IGNORECASE)
    if m2:
        d, m, y = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
        try:
            return date(y, m, d)
        except ValueError:
            pass

    # Pattern 3: năm yyyy
    m3 = re.search(r"năm\s+(20\d{2})", text, re.IGNORECASE)
    if m3:
        y = int(m3.group(1))
        return date(y, 6, 15)

    return None


def extract_parties(personal_info: str) -> list[PartyInfo]:
    """Phân tích thông tin cá nhân thành danh sách các bị cáo và bị hại."""
    parties: list[PartyInfo] = []
    lines = [ln.strip() for ln in personal_info.split("\n") if ln.strip()]

    # Nếu văn bản ngắn không có xuống dòng, tách theo dấu chấm phẩy hoặc dấu gạch đầu dòng
    if len(lines) <= 1:
        parts = re.split(r"[;\n•\-\*]", personal_info)
        lines = [p.strip() for p in parts if len(p.strip()) > 3]

    current_role = "Bị cáo"
    for line in lines:
        lower = line.lower()
        role = current_role
        if any(kw in lower for kw in ["bị hại", "người bị hại", "nạn nhân"]):
            role = "Bị hại"
        elif any(kw in lower for kw in ["bị cáo", "người phạm tội", "thủ phạm"]):
            role = "Bị cáo"

        # Trích xuất họ tên
        # Mẫu: Bị cáo: Nguyễn Văn A (SN 1990) ... hoặc 1. Nguyễn Văn A
        name_match = re.search(
            r"(?:bị cáo|bị hại|người bị hại|nạn nhân)?[:\s\-\d\.]*([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)+)",
            line,
        )
        name = name_match.group(1).strip() if name_match else line[:40].strip()

        # Tiền án / tiền sự
        priors = 0
        p_match = re.search(r"(\d+)\s+tiền án", lower)
        if p_match:
            priors = int(p_match.group(1))
        elif "có tiền án" in lower or "tái phạm" in lower:
            priors = 1

        is_recid = "tái phạm" in lower or priors > 0

        parties.append(
            PartyInfo(
                name=name,
                role=role,
                details=line,
                prior_convictions=priors,
                is_recidivist=is_recid,
            )
        )

    # Nếu không trích xuất được dòng nào cụ thể, tạo mặc định từ văn bản
    if not parties:
        parties.append(
            PartyInfo(
                name="Bị cáo chính",
                role="Bị cáo",
                details=personal_info.strip()[:100],
                prior_convictions=1 if "tiền án" in personal_info.lower() else 0,
            )
        )

    return parties


def parse_two_inputs(personal_info: str, case_info: str) -> ParsedCaseInput:
    """Chuyển đổi 2 khung nhập liệu thành dữ liệu cấu trúc và vector đặc trưng phục vụ suy luận."""
    # 1. Phân tích các đương sự từ Khung 1
    parties = extract_parties(personal_info)
    defendants = [p for p in parties if p.role == "Bị cáo"]
    victims = [p for p in parties if p.role == "Bị hại"]
    if not defendants and parties:
        # Nếu chưa phân loại rõ, mặc định người đầu tiên là bị cáo
        parties[0].role = "Bị cáo"
        defendants = [parties[0]]
        victims = parties[1:]

    # Tổng hợp tiền án của các bị cáo
    max_priors = max([p.prior_convictions for p in defendants], default=0)
    has_recidivism = any(p.is_recidivist for p in defendants)

    # 2. Phân tích Khung 2: Thông tin vụ án
    full_text = f"{personal_info}\n{case_info}"
    lower_case = case_info.lower()
    lower_full = full_text.lower()

    # Thời gian xảy ra hành vi
    incident_date = parse_dates_from_text(case_info) or parse_dates_from_text(personal_info) or date(2023, 1, 1)
    judgment_date = date.today()

    # Nhận diện tình tiết tăng nặng (Điều 52 BLHS)
    agg_factors: list[str] = []
    has_weapon = False
    if any(kw in lower_case for kw in ["hung khí", "dao", "súng", "vũ khí", "gậy sắt", "búa"]):
        agg_factors.append("Sử dụng vũ khí, hung khí nguy hiểm")
        has_weapon = True
    if any(kw in lower_case for kw in ["côn đồ", "tính chất côn đồ", "hung hãn"]):
        agg_factors.append("Có tính chất côn đồ")
    if any(kw in lower_case for kw in ["tổ chức", "có tổ chức", "bàn bạc trước", "phân công"]):
        agg_factors.append("Phạm tội có tổ chức")
    if has_recidivism or any(kw in lower_case for kw in ["tái phạm", "tái phạm nguy hiểm"]):
        agg_factors.append("Tái phạm hoặc tái phạm nguy hiểm")
    if any(kw in lower_case for kw in ["trẻ em", "dưới 16 tuổi", "người già", "phụ nữ có thai"]):
        agg_factors.append("Phạm tội đối với người yếu thế")

    # Nhận diện tình tiết giảm nhẹ (Điều 51 BLHS)
    mit_factors: list[str] = []
    has_confession = False
    has_compensation = False
    has_surrender = False

    if any(kw in lower_case for kw in ["thành khẩn", "ăn năn", "nhận tội", "hối cải"]):
        mit_factors.append("Người phạm tội thành khẩn khai báo, ăn năn hối cải (Điểm s Khoản 1 Điều 51)")
        has_confession = True
    if any(kw in lower_case for kw in ["bồi thường", "khắc phục", "nộp lại", "trả lại tiền"]):
        mit_factors.append("Tự nguyện bồi thường thiệt hại, khắc phục hậu quả (Điểm b Khoản 1 Điều 51)")
        has_compensation = True
    if any(kw in lower_case for kw in ["đầu thú", "tự thú", "ra đầu thú"]):
        mit_factors.append("Đầu thú, tự thú (Khoản 2 Điều 51)")
        has_surrender = True
    if any(kw in lower_case for kw in ["xin giảm nhẹ", "bị hại xin giảm", "bãi nại", "đơn bãi nại"]):
        mit_factors.append("Người bị hại có đơn xin giảm nhẹ hình phạt")
    if any(kw in lower_case for kw in ["gia đình có công", "huân chương", "thương binh", "liệt sĩ"]):
        mit_factors.append("Gia đình có công với cách mạng hoặc có thành tích xuất sắc")

    # Nhận diện tội danh và điều luật truy tố
    detected_articles: list[str] = []
    detected_crime_name = "Tội phạm hình sự"

    # Regex bắt điều luật được viết rõ (vd: Điều 134, Điều 168...)
    art_matches = re.findall(r"(?:Điều|điều)\s+(\d{3})", full_text)
    for a in art_matches:
        if a in STATUTORY_PENALTY_BOUNDS and a not in detected_articles:
            detected_articles.append(a)

    # Nhận diện theo từ khóa tội danh
    crime_checks = [
        ("123", "Tội giết người", ["giết người"]),
        ("125", "Tội giết người do bị kích động mạnh", ["kích động mạnh", "tinh thần bị kích động"]),
        ("128", "Tội vô ý làm chết người", ["vô ý làm chết người"]),
        ("134", "Tội cố ý gây thương tích", ["cố ý gây thương tích", "thương tích", "tổn hại sức khỏe", "đâm trúng", "chém"]),
        ("168", "Tội cướp tài sản", ["cướp tài sản", "dùng vũ lực cướp", "khống chế cướp"]),
        ("171", "Tội cướp giật tài sản", ["cướp giật", "giật túi xách", "giật điện thoại", "giật dây chuyền"]),
        ("173", "Tội trộm cắp tài sản", ["trộm cắp", "lén lút chiếm đoạt", "bẻ khóa trộm", "đột nhập trộm"]),
        ("174", "Tội lừa đảo chiếm đoạt tài sản", ["lừa đảo", "gian dối chiếm đoạt", "thủ đoạn gian dối"]),
        ("249", "Tội tàng trữ trái phép chất ma túy", ["tàng trữ trái phép chất ma túy", "cất giấu ma túy", "tàng trữ ma túy"]),
        ("250", "Tội vận chuyển trái phép chất ma túy", ["vận chuyển trái phép chất ma túy", "vận chuyển ma túy"]),
        ("251", "Tội mua bán trái phép chất ma túy", ["mua bán trái phép chất ma túy", "bán ma túy", "mua bán ma túy"]),
        ("260", "Tội vi phạm quy định về tham gia giao thông", ["tham gia giao thông", "tai nạn giao thông", "vi phạm giao thông"]),
        ("318", "Tội gây rối trật tự công cộng", ["gây rối trật tự", "đánh nhau nơi công cộng"]),
    ]

    for art_code, cname, keywords in crime_checks:
        if any(kw in lower_full for kw in keywords):
            if art_code not in detected_articles:
                detected_articles.append(art_code)
            detected_crime_name = cname
            break

    if not detected_articles:
        detected_articles = ["134"]  # Fallback phổ biến
        detected_crime_name = "Tội cố ý gây thương tích"

    # Xác định khung hình phạt luật định
    primary_art = detected_articles[0]
    stat_min, stat_max = STATUTORY_PENALTY_BOUNDS.get(primary_art, (1.0, 5.0))
    stat_mid = (stat_min + stat_max) / 2.0

    # 3. Xây dựng feature vector hoàn chỉnh cho ML Model
    num_agg = float(len(agg_factors))
    num_mit = float(len(mit_factors))
    num_facts = 1.0 + num_agg + num_mit

    features: dict[str, float] = {
        "num_facts": num_facts,
        "num_aggravating": num_agg,
        "num_mitigating": num_mit,
        "agg_to_mit_ratio": num_agg / (num_mit + 1e-4),
        "prior_convictions": float(max_priors),
        "is_organized": 1.0 if any("tổ chức" in a.lower() for a in agg_factors) else 0.0,
        "has_dangerous_weapon": 1.0 if has_weapon else 0.0,
        "is_recidivist": 1.0 if has_recidivism else 0.0,
        "sincere_confession": 1.0 if has_confession else 0.0,
        "compensation_made": 1.0 if has_compensation else 0.0,
        "surrendered": 1.0 if has_surrender else 0.0,
        "has_legal_factors": 1.0 if (num_agg + num_mit > 0) else 0.0,
        "no_factors": 1.0 if (num_agg + num_mit == 0) else 0.0,
        # Tội danh chi tiết
        "crime_is_robbery": 1.0 if primary_art == "168" else 0.0,
        "crime_is_snatching": 1.0 if primary_art == "171" else 0.0,
        "crime_is_theft": 1.0 if primary_art == "173" else 0.0,
        "crime_is_fraud": 1.0 if primary_art == "174" else 0.0,
        "crime_is_murder": 1.0 if primary_art == "123" else 0.0,
        "crime_is_provoked_murder": 1.0 if primary_art == "125" else 0.0,
        "crime_is_involuntary_manslaughter": 1.0 if primary_art == "128" else 0.0,
        "crime_is_injury": 1.0 if primary_art == "134" else 0.0,
        "crime_is_drug_transport": 1.0 if primary_art == "250" else 0.0,
        "crime_is_drug_trafficking": 1.0 if primary_art == "251" else 0.0,
        "crime_is_drug_possession": 1.0 if primary_art == "249" else 0.0,
        "crime_is_traffic": 1.0 if primary_art == "260" else 0.0,
        "crime_is_public_disorder": 1.0 if primary_art == "318" else 0.0,
        # Khung hình phạt luật định
        "statutory_min": stat_min,
        "statutory_max": stat_max,
        "statutory_mid": stat_mid,
    }

    for art_num in STATUTORY_PENALTY_BOUNDS:
        features[f"crime_is_{art_num}"] = 1.0 if (art_num in detected_articles) else 0.0

    # Tóm tắt kết hợp
    combined_desc = (
        f"Vụ án: {detected_crime_name} (Điều {', '.join(detected_articles)} BLHS).\n"
        f"Đương sự: Bị cáo ({', '.join([d.name for d in defendants]) or 'Không rõ'}); "
        f"Bị hại ({', '.join([v.name for v in victims]) or 'Không có'}).\n"
        f"Diễn biến hành vi: {case_info.strip()}"
    )

    return ParsedCaseInput(
        parties=parties,
        defendants=defendants,
        victims=victims,
        incident_date=incident_date,
        judgment_date=judgment_date,
        detected_crime_name=detected_crime_name,
        detected_articles=detected_articles,
        aggravating_factors=agg_factors,
        mitigating_factors=mit_factors,
        features=features,
        combined_description=combined_desc,
    )
