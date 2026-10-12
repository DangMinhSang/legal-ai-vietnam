"""Module phân tích và giải quyết vụ việc Kỷ luật & Tranh chấp Lao động - Cán bộ, Công chức.

Căn cứ pháp lý:
1. Bộ luật Lao động 2019 (BLLĐ 2019)
   - 4 Hình thức xử lý kỷ luật lao động theo Điều 124:
     + 1. Khiển trách
     + 2. Kéo dài thời hạn nâng lương không quá 06 tháng
     + 3. Cách chức
     + 4. Sa thải (Điều 125)
   - Các hành vi bị nghiêm cấm khi xử lý kỷ luật (Điều 127): Cấm phạt tiền, cắt lương; cấm xử lý kỷ luật lao động nữ mang thai/nuôi con dưới 12 tháng tuổi.
   - Hậu quả pháp lý khi sa thải hoặc đơn phương chấm dứt HĐLĐ trái pháp luật (Điều 41 BLLĐ).
2. Luật Cán bộ, công chức 2008 (sửa đổi, bổ sung 2019) & Nghị định 112/2020/NĐ-CP
   - Kỷ luật cán bộ: Khiển trách, Cảnh cáo, Cách chức, Bãi nhiệm.
   - Kỷ luật công chức: Khiển trách, Cảnh cáo, Hạ bậc lương, Giáng chức, Cách chức, Buộc thôi việc.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LaborDisciplineMeasure(str, Enum):
    """4 Hình thức kỷ luật lao động theo Điều 124 BLLĐ 2019."""

    KHIEN_TRACH = "khien_trach"  # 1. Khiển trách
    KEO_DAI_NANG_LUONG = "keo_dai_nang_luong"  # 2. Kéo dài thời hạn nâng lương không quá 06 tháng
    CACH_CHUC = "cach_chuc"  # 3. Cách chức
    SA_THAI = "sa_thai"  # 4. Sa thải (Điều 125)


class CivilServantDisciplineMeasure(str, Enum):
    """Hình thức kỷ luật cán bộ, công chức (Luật CBCC)."""

    KHIEN_TRACH = "khien_trach_cc"  # Khiển trách
    CANH_CAO = "canh_cao_cc"  # Cảnh cáo
    HA_BAC_LUONG = "ha_bac_luong"  # Hạ bậc lương
    GIANG_CHUC = "giang_chuc"  # Giáng chức
    CACH_CHUC = "cach_chuc_cc"  # Cách chức
    BUOC_THOI_VIEC = "buoc_thoi_viec"  # Buộc thôi việc


@dataclass
class DisciplinaryAnalysis:
    """Kết quả phân tích kỷ luật lao động hoặc công vụ."""

    target_person: str
    target_role: str  # Người lao động / Cán bộ / Công chức
    employer_or_agency: str
    discipline_matter: str
    applicable_laws: list[str]
    is_discipline_valid: bool = True
    procedural_violations: list[str] = field(default_factory=list)
    recommended_remedy: str = ""
    compensation_entitlement: dict[str, Any] = field(default_factory=dict)
    dispute_resolution_steps: list[str] = field(default_factory=list)
    legal_assessment: str = ""


class DisciplinaryResolver:
    """Động cơ phân tích kỷ luật và bảo vệ quyền lợi người lao động / cán bộ công chức."""

    @classmethod
    def analyze(cls, text: str) -> DisciplinaryAnalysis:
        """Phân tích hồ sơ kỷ luật lao động / công vụ."""
        lower = text.lower()

        # 1. Xác định đối tượng là Người lao động hay Cán bộ, công chức
        is_civil_servant = any(kw in lower for kw in ["cán bộ", "công chức", "viên chức", "cơ quan nhà nước", "sở", "phòng ban", "đảng viên"])
        role = "Cán bộ / Công chức / Viên chức" if is_civil_servant else "Người lao động trong doanh nghiệp"

        target_person = "Người bị xử lý kỷ luật"
        m_person = re.search(r"(?:ông|bà|anh|chị|người lao động|nhân viên)\s+([A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+)*)", text)
        if m_person:
            target_person = m_person.group(1).strip()

        agency = "Doanh nghiệp / Người sử dụng lao động" if not is_civil_servant else "Cơ quan, đơn vị có thẩm quyền quản lý cán bộ công chức"
        m_agency = re.search(r"(?:công ty|tổng công ty|doanh nghiệp|cơ quan)\s+([^\n.,;]+)", text, re.IGNORECASE)
        if m_agency:
            agency = m_agency.group(0).strip()

        # 2. Nhận diện hình thức kỷ luật đang áp dụng hoặc tranh chấp
        discipline_matter = "Xử lý kỷ luật lao động"
        violations: list[str] = []
        is_valid = True

        if is_civil_servant:
            applicable_laws = [
                "Luật Cán bộ, công chức 2008 (sửa đổi, bổ sung 2019)",
                "Nghị định 112/2020/NĐ-CP về xử lý kỷ luật cán bộ, công chức, viên chức",
            ]
            if "buộc thôi việc" in lower or "đuổi việc" in lower:
                discipline_matter = "Kỷ luật Buộc thôi việc công chức"
            elif "cách chức" in lower:
                discipline_matter = "Kỷ luật Cách chức công chức lãnh đạo"
            elif "hạ bậc lương" in lower:
                discipline_matter = "Kỷ luật Hạ bậc lương"
            elif "cảnh cáo" in lower:
                discipline_matter = "Kỷ luật Cảnh cáo"
            else:
                discipline_matter = "Kỷ luật Khiển trách công chức"
        else:
            applicable_laws = [
                "Bộ luật Lao động 2019",
                "Nghị định 145/2020/NĐ-CP hướng dẫn Bộ luật Lao động",
                "Nội quy lao động của doanh nghiệp đã đăng ký",
            ]

            if any(kw in lower for kw in ["sa thải", "đuổi việc", "chấm dứt hợp đồng"]):
                discipline_matter = "Xử lý kỷ luật sa thải (Điều 125 BLLĐ 2019)"
            elif any(kw in lower for kw in ["cách chức"]):
                discipline_matter = "Xử lý kỷ luật Cách chức (Khoản 3 Điều 124 BLLĐ 2019)"
            elif any(kw in lower for kw in ["kéo dài nâng lương", "chậm nâng lương"]):
                discipline_matter = "Kỷ luật Kéo dài thời hạn nâng lương không quá 06 tháng (Khoản 2 Điều 124 BLLĐ 2019)"
            else:
                discipline_matter = "Kỷ luật Khiển trách lao động (Khoản 1 Điều 124 BLLĐ 2019)"

            # 3. Kiểm tra các lỗi vi phạm điều cấm khi kỷ luật lao động
            # Cấm 1: Phạt tiền, cắt lương
            has_wage_penalty = (
                ("trừ" in lower and "lương" in lower)
                or ("cắt" in lower and "lương" in lower)
                or any(kw in lower for kw in ["phạt tiền", "cắt lương", "trừ lương", "thu tiền"])
            )
            if has_wage_penalty:
                is_valid = False
                violations.append(
                    "VI PHẠM ĐIỀU CẤM (Khoản 2 Điều 127 BLLĐ): Người sử dụng lao động tuyệt đối KHÔNG được dùng hình thức phạt tiền, cắt lương thay việc xử lý kỷ luật lao động."
                )

            # Cấm 2: Xử lý khi mang thai, nuôi con nhỏ dưới 12 tháng tuổi
            if any(kw in lower for kw in ["mang thai", "nghỉ thai sản", "nuôi con dưới 12 tháng", "con nhỏ"]):
                is_valid = False
                violations.append(
                    "VI PHẠM ĐIỀU CẤM (Khoản 4 Điều 122 BLLĐ): Không được xử lý kỷ luật lao động đối với người lao động nữ mang thai, nghỉ thai sản hoặc nuôi con dưới 12 tháng tuổi."
                )

            # Cấm 3: Trình tự thủ tục không có công đoàn hoặc không thông báo trước
            if any(kw in lower for kw in ["không họp", "không có công đoàn", "không lập biên bản", "ngay lập tức"]):
                is_valid = False
                violations.append(
                    "VI PHẠM TRÌNH TỰ (Điều 122 BLLĐ): Cuộc họp xử lý kỷ luật bắt buộc phải có sự tham gia của tổ chức đại diện người lao động (Công đoàn cơ sở) và phải thông báo trước ít nhất 05 ngày làm việc."
                )

        # 4. Tính toán quyền lợi bồi thường khi sa thải trái pháp luật (Điều 41 BLLĐ)
        compensation: dict[str, Any] = {}
        if not is_civil_servant and not is_valid and "sa thải" in discipline_matter.lower():
            compensation = {
                "legal_basis": "Điều 41 Bộ luật Lao động 2019 (Bồi thường khi sa thải trái pháp luật)",
                "reinstatement": "Phải nhận người lao động trở lại làm việc theo hợp đồng lao động đã giao kết.",
                "unpaid_salary": "Phải trả đủ tiền lương, đóng bảo hiểm xã hội, BHYT, BHTN trong những ngày người lao động không được làm việc.",
                "additional_damages": "Phải bồi thường thêm một khoản tiền ít nhất bằng 02 tháng tiền lương theo hợp đồng lao động (Khoản 2 Điều 41 BLLĐ).",
                "refuse_reinstatement_compensation": "Nếu người lao động không muốn trở lại làm việc: được trả trợ cấp thôi việc (Điều 46) + khoản bồi thường thêm thỏa thuận ít nhất 02 tháng lương.",
            }

        # 5. Các bước giải quyết tranh chấp kỷ luật lao động
        steps = [
            "Bước 1: Soạn Đơn khiếu nại quyết định kỷ luật gửi Tổng Giám đốc / Giám đốc Người sử dụng lao động hoặc Người đứng đầu cơ quan.",
            "Bước 2: Yêu cầu Hòa giải viên lao động (thuộc Phòng LĐ-TB&XH quận/huyện) tiến hành hòa giải tranh chấp lao động cá nhân.",
            "Bước 3: Khởi kiện tại Tòa án nhân dân cấp huyện nơi doanh nghiệp đặt trụ sở theo thủ tục Tố tụng Dân sự (Tranh chấp về kỷ luật sa thải KHÔNG BẮT BUỘC phải qua hòa giải cơ sở theo Điểm a Khoản 1 Điều 188 BLLĐ).",
            "Bước 4: Yêu cầu Tòa án tuyên bố Quyết định kỷ luật sa thải là trái pháp luật và buộc doanh nghiệp thực hiện nghĩa vụ bồi thường theo Điều 41 BLLĐ 2019.",
        ]

        legal_eval = (
            f"Vụ việc thuộc phạm vi điều chỉnh của pháp luật về Kỷ luật lao động và Tranh chấp lao động. "
            f"Bản chất: {discipline_matter}. "
            f"{'Quyết định kỷ luật có dấu hiệu vi phạm pháp luật nghiêm trọng về thẩm quyền, căn cứ hoặc trình tự thủ tục, cần được khiếu nại hoặc khởi kiện hủy bỏ.' if not is_valid else 'Cần đối chiếu với Nội quy lao động và quy trình điều tra làm rõ hành vi vi phạm để bảo đảm tính hợp pháp.'}"
        )

        return DisciplinaryAnalysis(
            target_person=target_person,
            target_role=role,
            employer_or_agency=agency,
            discipline_matter=discipline_matter,
            applicable_laws=applicable_laws,
            is_discipline_valid=is_valid,
            procedural_violations=violations,
            recommended_remedy="Khiếu nại nội bộ và Khởi kiện tại TAND để hủy quyết định kỷ luật trái luật, yêu cầu bồi thường theo Điều 41 BLLĐ 2019.",
            compensation_entitlement=compensation,
            dispute_resolution_steps=steps,
            legal_assessment=legal_eval,
        )


def analyze_disciplinary_matter(text: str) -> dict[str, Any]:
    """Hàm tiện ích phân tích kỷ luật lao động / cán bộ công chức."""
    res = DisciplinaryResolver.analyze(text)
    return {
        "domain": "disciplinary",
        "domain_name": "Pháp luật Kỷ luật Lao động & Cán bộ, Công chức",
        "target_person": res.target_person,
        "target_role": res.target_role,
        "employer_or_agency": res.employer_or_agency,
        "discipline_matter": res.discipline_matter,
        "applicable_laws": res.applicable_laws,
        "is_discipline_valid": res.is_discipline_valid,
        "procedural_violations": res.procedural_violations,
        "recommended_remedy": res.recommended_remedy,
        "compensation_entitlement": res.compensation_entitlement,
        "dispute_resolution_steps": res.dispute_resolution_steps,
        "legal_assessment": res.legal_assessment,
    }
