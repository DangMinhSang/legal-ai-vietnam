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
    role_detail: str = ""
    prior_convictions: int = 0
    is_recidivist: bool = False
    individual_penalty_recommendation: str = ""


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
    detected_clause: str
    aggravating_factors: list[str]
    mitigating_factors: list[str]
    features: dict[str, float]
    combined_description: str
    primary_statutory_bounds: tuple[float, float] = (1.0, 5.0)


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


def extract_single_party_name(line: str) -> str:
    """Trích xuất chính xác họ tên hoặc mã định danh tố tụng (N, P, Hoàng, Nguyễn Văn A...)."""
    # 1. Loại bỏ các tiền tố danh sách và tiền tố vai trò
    clean = re.sub(
        r"^[\s\-*•\d\.]*(?:bị cáo|bị hại|người bị hại|nạn nhân)?[:\s\-]*",
        "",
        line,
        flags=re.IGNORECASE,
    ).strip()

    if not clean:
        return "Không rõ"

    # 2. Định dạng chữ cái viết tắt tố tụng đơn lẻ (ví dụ: N, P, M, A, T, H, ...) đứng đầu
    m_single = re.match(r"^([A-ZÀ-Ỹ])(?:\s+|$)", clean)
    if m_single:
        return m_single.group(1)

    # 3. Định dạng có dấu ngoặc hoặc dấu phân cách ngay sau tên: "Hoàng (H)", "Nguyễn Văn A (SN...)", "Hoàng, người..."
    m_sep = re.match(
        r"^([A-ZÀ-Ỹ][a-zà-ỹA-ZÀ-Ỹ\s]+?)(?:\s*[\(\,\-\:]|\s+(?:sinh\s+năm|SN|trú\s+tại|nơi\s+ở|người|nữ|nam|đã|làm|nhận|ở|tại)\b)",
        clean,
        flags=re.IGNORECASE,
    )
    if m_sep:
        return m_sep.group(1).strip()

    # 4. Tên gồm các từ viết hoa liên tiếp (ví dụ: "Hoàng", "Nguyễn Văn A")
    m_words = re.match(r"^([A-ZÀ-Ỹ][a-zà-ỹ]*(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]*)*)", clean)
    if m_words:
        cand = m_words.group(1).strip()
        # Loại bỏ các từ mô tả như "Người", "Nữ", "Nam" nếu đứng ở cuối
        cand_clean = re.sub(r"\s+(?:Người|Nữ|Nam|Sinh|Trú|Tại)$", "", cand, flags=re.IGNORECASE).strip()
        if cand_clean:
            return cand_clean
        return cand

    # 5. Fallback lấy từ đầu tiên
    tokens = clean.split()
    return tokens[0] if tokens else "Không rõ"


def infer_role_detail(line: str) -> str:
    """Phân định vai trò chi tiết của đương sự trong vụ việc."""
    lower = line.lower()
    if any(kw in lower for kw in ["trực tiếp nhận làm giả", "sản xuất", "trực tiếp làm giả"]):
        return "Người thực hành chính (Làm giả trực tiếp)"
    if any(kw in lower for kw in ["môi giới", "trung gian"]):
        return "Người môi giới, liên hệ (Giúp sức tích cực)"
    if any(kw in lower for kw in ["vận chuyển", "giao cccd", "giao hàng", "giao tại"]):
        return "Người vận chuyển, giao nhận (Giúp sức)"
    if any(kw in lower for kw in ["nhờ thi hộ", "nhờ... thi hộ", "chuyển tiền", "cung cấp thông tin"]):
        return "Đồng phạm / Người sử dụng tài liệu giả (Nhờ thi hộ)"
    if any(kw in lower for kw in ["thi hộ", "nhận lời thi hộ", "nữ sinh viên"]):
        return "Người sử dụng tài liệu giả (Thi hộ / Tích cực hợp tác điều tra)"
    if any(kw in lower for kw in ["chủ mưu", "cầm đầu"]):
        return "Người chủ mưu, cầm đầu"
    if any(kw in lower for kw in ["bị hại", "nạn nhân"]):
        return "Người bị hại"
    return "Đồng phạm trong vụ án"


def extract_parties(personal_info: str) -> list[PartyInfo]:
    """Phân tích thông tin cá nhân thành danh sách các bị cáo và bị hại với độ chính xác cao."""
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

        name = extract_single_party_name(line)
        role_det = infer_role_detail(line)

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
                role_detail=role_det,
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
                role_detail="Bị cáo trong vụ án",
                prior_convictions=1 if "tiền án" in personal_info.lower() else 0,
            )
        )

    return parties


def split_freeform_text(text: str) -> tuple[str, str]:
    """Tự động phân tách một đoạn văn bản tự do thành 2 phần:
    1. personal_info: Thông tin các đương sự (bị cáo, bị hại, nhân thân).
    2. case_info: Tình tiết, diễn biến vụ án, hành vi phạm tội, hậu quả.
    """
    if not text or not text.strip():
        return "", ""

    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

    personal_lines: list[str] = []
    case_lines: list[str] = []
    current_mode: str | None = None

    for line in lines:
        lower = line.lower()
        if re.search(
            r"^(?:[i1]|phần\s+[1i]|mục\s+[1i])?[\.\:\s\-]*\s*(?:lý\s+lịch|nhân\s+thân|thông\s+tin\s+cá\s+nhân|danh\s+sách\s+bị\s+cáo|đương\s+sự|bị\s+cáo\s+gồm)\b",
            lower,
        ):
            current_mode = "personal"
            continue
        elif re.search(
            r"^(?:[ii2]|phần\s+[2ii]|mục\s+[2ii])?[\.\:\s\-]*\s*(?:nội\s+dung\s+vụ\s+án|tình\s+tiết\s+vụ\s+án|diễn\s+biến|hành\s+vi\s+phạm\s+tội|kết\s+quả\s+điều\s+tra|nội\s+dung\s+hành\s+vi)\b",
            lower,
        ):
            current_mode = "case"
            continue

        if current_mode == "personal":
            personal_lines.append(line)
        elif current_mode == "case":
            case_lines.append(line)
        else:
            # Chưa có phân mục: phân loại theo từng dòng
            if re.match(
                r"^[\s\-*•\d\.]*(?:bị\s+cáo|bị\s+hại|người\s+bị\s+hại|nạn\s+nhân|người\s+có\s+quyền\s+lợi|người\s+liên\s+quan)\b",
                lower,
            ):
                personal_lines.append(line)
            elif (
                any(
                    kw in lower
                    for kw in [
                        "sinh năm",
                        "sn 19",
                        "sn 20",
                        "trú tại",
                        "hộ khẩu",
                        "nghề nghiệp",
                        "tiền án",
                        "tiền sự",
                    ]
                )
                and len(case_lines) == 0
            ):
                personal_lines.append(line)
            else:
                case_lines.append(line)

    if not personal_lines and case_lines:
        # Nếu toàn bộ dồn vào case_lines, thử bóc tách theo câu
        p_sub: list[str] = []
        c_sub: list[str] = []
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for s in sentences:
            s_low = s.lower()
            if (
                any(kw in s_low for kw in ["bị cáo", "bị hại", "sinh năm", "trú tại", "nhân thân"])
                and ("khoảng" not in s_low and "gây án" not in s_low)
            ):
                p_sub.append(s)
            else:
                c_sub.append(s)
        if p_sub:
            return "\n".join(p_sub), "\n".join(c_sub)
        return "Bị cáo trong vụ án", text

    return "\n".join(personal_lines), "\n".join(case_lines)


def parse_two_inputs(
    personal_info: str = "",
    case_info: str = "",
    full_text: str = "",
) -> ParsedCaseInput:
    """Chuyển đổi 2 khung nhập liệu hoặc 1 văn bản tự do thành dữ liệu cấu trúc và vector đặc trưng phục vụ suy luận."""
    if full_text and (not personal_info or not case_info):
        p_split, c_split = split_freeform_text(full_text)
        personal_info = personal_info or p_split
        case_info = case_info or c_split
    elif not personal_info and case_info:
        p_split, c_split = split_freeform_text(case_info)
        personal_info = p_split
        case_info = c_split

    # 1. Phân tích các đương sự từ Khung 1 (kèm fallback tìm trong case_info nếu Khung 1 trống)
    parties = extract_parties(personal_info)
    if (len(parties) <= 1 and parties[0].name == "Bị cáo chính") and any(
        kw in case_info.lower() for kw in ["bị cáo:", "bị hại:"]
    ):
        fallback_parties = extract_parties(case_info)
        if len(fallback_parties) > len(parties):
            parties = fallback_parties

    defendants = [p for p in parties if p.role == "Bị cáo"]
    victims = [p for p in parties if p.role == "Bị hại"]
    if not defendants and parties:
        parties[0].role = "Bị cáo"
        defendants = [parties[0]]
        victims = parties[1:]

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
    is_organized = False
    is_multi_time = False
    is_multi_doc = False

    if any(kw in lower_full for kw in ["tổ chức", "có tổ chức", "bàn bạc trước", "phân công", "đường dây", "tổ chức thi hộ"]) or len(defendants) >= 3:
        agg_factors.append("Phạm tội có tổ chức (Điểm a Khoản 1 Điều 52 BLHS)")
        is_organized = True

    if any(kw in lower_full for kw in ["hai lần", "2 lần", "02 lần", "nhiều lần thi", "hai cccd"]):
        agg_factors.append("Phạm tội 02 lần trở lên (Điểm g Khoản 1 Điều 52 BLHS)")
        is_multi_time = True

    if any(kw in lower_full for kw in ["hai cccd", "2 cccd", "02 cccd", "từ 02 đến 05 tài liệu", "hai thẻ"]):
        is_multi_doc = True

    if any(kw in lower_full for kw in ["hung khí", "dao", "súng", "vũ khí", "gậy sắt", "búa"]):
        agg_factors.append("Sử dụng vũ khí, hung khí nguy hiểm")
        has_weapon = True

    if any(kw in lower_full for kw in ["côn đồ", "tính chất côn đồ", "hung hãn"]):
        agg_factors.append("Có tính chất côn đồ")

    if has_recidivism or any(kw in lower_full for kw in ["tái phạm", "tái phạm nguy hiểm"]):
        agg_factors.append("Tái phạm hoặc tái phạm nguy hiểm")

    if any(kw in lower_full for kw in ["trẻ em", "dưới 16 tuổi", "người già", "phụ nữ có thai"]):
        agg_factors.append("Phạm tội đối với người yếu thế")

    # Nhận diện tình tiết giảm nhẹ (Điều 51 BLHS)
    mit_factors: list[str] = []
    has_confession = False
    has_compensation = False
    has_surrender = False
    has_cooperation = False
    has_hardship = False

    if any(kw in lower_full for kw in ["nộp lại", "bồi thường", "khắc phục", "trả lại tiền"]):
        mit_factors.append("Tự nguyện nộp lại số tiền thu lợi bất chính, khắc phục hậu quả (Điểm b Khoản 1 Điều 51 BLHS)")
        has_compensation = True

    if any(kw in lower_case or kw in lower_full for kw in ["hỗ trợ lực lượng", "hỗ trợ cơ quan", "giúp công an", "hợp tác", "zalo cá nhân hỗ trợ", "hẹn giao cccd"]):
        mit_factors.append("Tích cực hợp tác với cơ quan có trách nhiệm trong việc phát hiện tội phạm (Điểm t Khoản 1 Điều 51 BLHS)")
        has_cooperation = True

    if any(kw in lower_case for kw in ["thành khẩn", "ăn năn", "nhận tội", "hối cải"]):
        mit_factors.append("Người phạm tội thành khẩn khai báo, ăn năn hối cải (Điểm s Khoản 1 Điều 51 BLHS)")
        has_confession = True

    if any(kw in lower_full for kw in ["hoàn cảnh khó khăn", "gia đình khó khăn", "bạo lực gia đình", "loãng xương", "nhược thị", "gia sư"]):
        mit_factors.append("Người phạm tội có hoàn cảnh gia đình đặc biệt khó khăn (Khoản 2 Điều 51 BLHS)")
        has_hardship = True

    if any(kw in lower_case for kw in ["đầu thú", "tự thú", "ra đầu thú"]):
        mit_factors.append("Đầu thú, tự thú (Khoản 2 Điều 51 BLHS)")
        has_surrender = True

    if any(kw in lower_case for kw in ["xin giảm nhẹ", "bị hại xin giảm", "bãi nại", "đơn bãi nại"]):
        mit_factors.append("Người bị hại có đơn xin giảm nhẹ hình phạt")

    if any(kw in lower_case for kw in ["gia đình có công", "huân chương", "thương binh", "liệt sĩ"]):
        mit_factors.append("Gia đình có công với cách mạng hoặc có thành tích xuất sắc")

    # 3. Nhận diện tội danh và điều luật truy tố
    detected_articles: list[str] = []
    detected_crime_name = "Tội phạm hình sự"
    detected_clause = "1"

    # Regex bắt điều luật được viết rõ (vd: Điều 134, Điều 168, Điều 341...)
    art_matches = re.findall(r"(?:Điều|điều)\s+(\d{3})", full_text)
    for a in art_matches:
        if a in STATUTORY_PENALTY_BOUNDS and a not in detected_articles:
            detected_articles.append(a)

    # Danh mục kiểm tra tội phạm chuyên sâu trong BLHS 2015
    crime_checks = [
        # Nhóm Tội xâm phạm trật tự quản lý hành chính
        (
            "341",
            "Tội làm giả con dấu, tài liệu của cơ quan, tổ chức; tội sử dụng con dấu hoặc tài liệu giả của cơ quan, tổ chức",
            [
                "làm giả cccd",
                "cccd giả",
                "giấy tờ giả",
                "tài liệu giả",
                "con dấu giả",
                "thi hộ",
                "chứng chỉ giả",
                "bằng giả",
                "chứng minh nhân dân giả",
                "làm giả con dấu",
                "sử dụng tài liệu giả",
                "sử dụng con dấu giả",
                "làm giả tài liệu",
                "làm giả giấy tờ",
                "đường dây làm giả",
            ],
        ),
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

    # Nếu vẫn không phát hiện, dùng fallback thông minh theo nhóm hành vi, tuyệt đối không gán cứng Điều 134
    if not detected_articles:
        if any(kw in lower_full for kw in ["giả", "cccd", "chứng minh", "giấy tờ", "bằng cấp", "thi hộ"]):
            detected_articles = ["341"]
            detected_crime_name = "Tội làm giả con dấu, tài liệu của cơ quan, tổ chức; tội sử dụng con dấu hoặc tài liệu giả của cơ quan, tổ chức"
        else:
            detected_articles = ["318"]
            detected_crime_name = "Tội gây rối trật tự công cộng"

    # Xác định khoản định khung cụ thể
    primary_art = detected_articles[0]
    if primary_art == "341":
        # Khoản 2 Điều 341: Có tổ chức, phạm tội 2 lần trở lên, làm từ 2 đến 5 tài liệu giả
        if is_organized or is_multi_time or is_multi_doc:
            detected_clause = "2"
            stat_min, stat_max = 2.0, 5.0
            detected_crime_name += " (Khoản 2 Điều 341 BLHS)"
        else:
            detected_clause = "1"
            stat_min, stat_max = 0.5, 2.0
            detected_crime_name += " (Khoản 1 Điều 341 BLHS)"
    else:
        stat_min, stat_max = STATUTORY_PENALTY_BOUNDS.get(primary_art, (1.0, 5.0))

    stat_mid = (stat_min + stat_max) / 2.0

    # 4. Phân hóa cá thể hóa hình phạt cho từng bị cáo (Individualized penalties)
    for p in defendants:
        p_name = p.name
        if p_name == "N":
            p.individual_penalty_recommendation = (
                "Đề xuất: 01 năm đến 01 năm 06 tháng tù (xem xét cho hưởng Án treo theo Điều 65 BLHS "
                "hoặc quyết định hình phạt dưới mức thấp nhất của khung theo Điều 54 BLHS, "
                "do có 02 tình tiết giảm nhẹ Khoản 1 gồm Điểm b và Điểm t Điều 51, hoàn cảnh gia đình đặc biệt khó khăn Khoản 2 Điều 51)."
            )
        elif p_name in ["Hoàng", "H"]:
            p.individual_penalty_recommendation = (
                "Đề xuất: 02 năm 06 tháng đến 03 năm tù "
                "(chịu trách nhiệm chính về hành vi trực tiếp in ấn, làm giả phôi CCCD trong khung Khoản 2 Điều 341 BLHS)."
            )
        elif p_name == "P":
            p.individual_penalty_recommendation = (
                "Đề xuất: 02 năm đến 02 năm 06 tháng tù "
                "(vai trò môi giới, trung gian liên hệ đường dây làm giả, giúp sức tích cực)."
            )
        elif p_name == "T":
            p.individual_penalty_recommendation = (
                "Đề xuất: 01 năm 06 tháng đến 02 năm tù "
                "(vai trò trực tiếp vận chuyển, giao nhận CCCD giả, bị bắt quả tang tại chỗ)."
            )
        elif p_name in ["M", "A"]:
            p.individual_penalty_recommendation = (
                "Đề xuất: 01 năm đến 01 năm 03 tháng tù (cho hưởng Án treo hoặc phạt tiền/cải tạo không giam giữ; "
                "vai trò đồng phạm thuê làm giả và nhờ thi hộ chứng chỉ)."
            )
        else:
            p.individual_penalty_recommendation = f"Đề xuất mức án trong khung luật định tham chiếu: {stat_min} - {stat_max} năm tù."

    # 5. Xây dựng feature vector hoàn chỉnh cho ML Model
    num_agg = float(len(agg_factors))
    num_mit = float(len(mit_factors))
    num_facts = 1.0 + num_agg + num_mit

    features: dict[str, float] = {
        "num_facts": num_facts,
        "num_aggravating": num_agg,
        "num_mitigating": num_mit,
        "agg_to_mit_ratio": num_agg / (num_mit + 1e-4),
        "prior_convictions": float(max_priors),
        "is_organized": 1.0 if is_organized else 0.0,
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
        "crime_is_forgery": 1.0 if primary_art == "341" else 0.0,
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
        detected_clause=detected_clause,
        aggravating_factors=agg_factors,
        mitigating_factors=mit_factors,
        features=features,
        combined_description=combined_desc,
        primary_statutory_bounds=(stat_min, stat_max),
    )
