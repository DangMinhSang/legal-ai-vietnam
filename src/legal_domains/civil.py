"""Module phân tích và giải quyết tranh chấp Dân sự theo Bộ luật Dân sự 2015 (BLDS 2015) và Bộ luật Tố tụng Dân sự 2015 (BLTTDS 2015).

Bao gồm các nhóm quan hệ pháp luật dân sự trọng tâm:
1. Tranh chấp hợp đồng dân sự (Vay mượn, mua bán tài sản, thuê mướn, tặng cho, dịch vụ, đặt cọc).
2. Tranh chấp bồi thường thiệt hại ngoài hợp đồng (Điều 584 - 608 BLDS 2015).
3. Tranh chấp thừa kế di sản và quyền sở hữu (Điều 609 - 662 BLDS 2015).
4. Tranh chấp quyền sử dụng đất và ranh giới bất động sản.

Phương thức giải quyết tranh chấp:
- Thương lượng (Negotiation)
- Hòa giải (Mediation: Hòa giải cơ sở, Hòa giải đối thoại tại Tòa án theo Luật Hòa giải, đối thoại tại Tòa án 2020)
- Khởi kiện tại Tòa án nhân dân có thẩm quyền (Litigation - BLTTDS 2015).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CivilDisputeType(str, Enum):
    """Các nhóm tranh chấp dân sự phổ biến."""

    CONTRACT_LOAN = "contract_loan"  # Tranh chấp hợp đồng vay tài sản (Điều 463 BLDS)
    CONTRACT_SALE = "contract_sale"  # Tranh chấp hợp đồng mua bán tài sản (Điều 430 BLDS)
    CONTRACT_LEASE = "contract_lease"  # Tranh chấp hợp đồng thuê tài sản (Điều 472 BLDS)
    CONTRACT_DEPOSIT = "contract_deposit"  # Tranh chấp đặt cọc (Điều 328 BLDS)
    TORT_DAMAGE = "tort_damage"  # Bồi thường thiệt hại ngoài hợp đồng (Điều 584 BLDS)
    INHERITANCE = "inheritance"  # Tranh chấp chia thừa kế (Điều 609 BLDS)
    PROPERTY_LAND = "property_land"  # Tranh chấp quyền sử dụng đất & sở hữu tài sản
    OTHER_CIVIL = "other_civil"  # Tranh chấp dân sự khác


class CivilResolutionMethod(str, Enum):
    """Phương thức giải quyết tranh chấp dân sự."""

    NEGOTIATION = "thuong_luong"  # Tự thương lượng, thỏa thuận
    COURT_MEDIATION = "hoa_giai_tai_toa"  # Hòa giải theo Luật Hòa giải đối thoại tại Tòa án 2020
    COURT_LITIGATION = "khoi_kien_toa_an"  # Khởi kiện sơ thẩm tại TAND (BLTTDS 2015)


@dataclass
class CivilDisputeAnalysis:
    """Kết quả phân tích toàn diện tranh chấp dân sự."""

    dispute_type: CivilDisputeType
    dispute_name: str
    applicable_laws: list[str]
    plaintiff: str = "Nguyên đơn"
    defendant: str = "Bị đơn"
    third_parties: list[str] = field(default_factory=list)
    claim_amount_vnd: float = 0.0
    interest_rate_claim_valid: bool = True
    statute_of_limitations_valid: bool = True  # Thời hiệu khởi kiện (thường 03 năm theo Điều 429 BLDS)
    statute_of_limitations_note: str = ""
    suggested_steps: list[str] = field(default_factory=list)
    estimated_court_fee_vnd: float = 0.0  # Án phí dân sự sơ thẩm ước tính theo Nghị quyết 326/2016/UBTVQH14
    legal_assessment: str = ""
    risk_warnings: list[str] = field(default_factory=list)


class CivilDisputeResolver:
    """Động cơ phân tích tranh chấp dân sự và định hướng giải quyết."""

    @staticmethod
    def calculate_civil_court_fee(claim_amount: float) -> float:
        """Tính án phí dân sự sơ thẩm có giá ngạch theo Nghị quyết 326/2016/UBTVQH14."""
        if claim_amount <= 0:
            return 300_000  # Án phí không có giá ngạch
        if claim_amount <= 6_000_000:
            return 300_000
        if claim_amount <= 400_000_000:
            return claim_amount * 0.05
        if claim_amount <= 800_000_000:
            return 20_000_000 + (claim_amount - 400_000_000) * 0.04
        if claim_amount <= 2_000_000_000:
            return 36_000_000 + (claim_amount - 800_000_000) * 0.03
        if claim_amount <= 4_000_000_000:
            return 72_000_000 + (claim_amount - 2_000_000_000) * 0.02
        return 112_000_000 + (claim_amount - 4_000_000_000) * 0.001

    @classmethod
    def analyze(cls, text: str) -> CivilDisputeAnalysis:
        """Phân tích nội dung vụ việc tranh chấp dân sự."""
        lower = text.lower()

        # 1. Nhận diện loại tranh chấp
        dispute_type = CivilDisputeType.OTHER_CIVIL
        dispute_name = "Tranh chấp dân sự tổng quát"
        applicable_laws = ["Bộ luật Dân sự 2015", "Bộ luật Tố tụng Dân sự 2015"]

        if any(kw in lower for kw in ["vay", "hợp đồng vay", "cho vay", "giấy vay", "nợ tiền", "khoản vay", "trả nợ", "tiền vay"]):
            dispute_type = CivilDisputeType.CONTRACT_LOAN
            dispute_name = "Tranh chấp Hợp đồng vay tài sản (Điều 463 - 470 BLDS 2015)"
            applicable_laws = [
                "Điều 463 BLDS 2015 (Hợp đồng vay tài sản)",
                "Điều 466 BLDS 2015 (Nghĩa vụ trả nợ của bên vay)",
                "Điều 468 BLDS 2015 (Lãi suất vay tối đa 20%/năm)",
                "Nghị quyết 01/2019/NQ-HĐTP về lãi suất và phạt vi phạm",
            ]
        elif any(kw in lower for kw in ["đặt cọc", "tiền cọc", "hủy cọc", "phạt cọc"]):
            dispute_type = CivilDisputeType.CONTRACT_DEPOSIT
            dispute_name = "Tranh chấp Hợp đồng đặt cọc (Điều 328 BLDS 2015)"
            applicable_laws = [
                "Điều 328 BLDS 2015 (Biện pháp bảo đảm đặt cọc)",
                "Án lệ số 25/2018/AL về phạt cọc khi hợp đồng không thực hiện được",
            ]
        elif any(kw in lower for kw in ["bồi thường thiệt hại ngoài hợp đồng", "tai nạn", "đâm va", "làm hỏng tài sản", "xâm phạm sức khỏe"]):
            dispute_type = CivilDisputeType.TORT_DAMAGE
            dispute_name = "Tranh chấp bồi thường thiệt hại ngoài hợp đồng (Điều 584 - 608 BLDS 2015)"
            applicable_laws = [
                "Điều 584 BLDS 2015 (Căn cứ phát sinh trách nhiệm bồi thường)",
                "Điều 585 BLDS 2015 (Nguyên tắc bồi thường thiệt hại)",
                "Điều 590 BLDS 2015 (Thiệt hại do sức khỏe bị xâm phạm)",
                "Nghị quyết 02/2022/NQ-HĐTP hướng dẫn bồi thường thiệt hại ngoài hợp đồng",
            ]
        elif any(kw in lower for kw in ["thừa kế", "di chúc", "chia di sản", "hàng thừa kế"]):
            dispute_type = CivilDisputeType.INHERITANCE
            dispute_name = "Tranh chấp chia di sản thừa kế (Điều 609 - 662 BLDS 2015)"
            applicable_laws = [
                "Điều 611 BLDS 2015 (Thời điểm, địa điểm mở thừa kế)",
                "Điều 623 BLDS 2015 (Thời hiệu thừa kế: 30 năm BĐS, 10 năm ĐS)",
                "Điều 649 - 651 BLDS 2015 (Thừa kế theo pháp luật và hàng thừa kế)",
            ]
        elif any(kw in lower for kw in ["ranh giới đất", "lấn chiếm đất", "sổ đỏ", "quyền sử dụng đất", "nhà đất"]):
            dispute_type = CivilDisputeType.PROPERTY_LAND
            dispute_name = "Tranh chấp quyền sử dụng đất và tài sản gắn liền với đất"
            applicable_laws = [
                "Điều 158 - 178 BLDS 2015 (Quyền sở hữu và quyền khác đối với tài sản)",
                "Luật Đất đai 2013 / Luật Đất đai 2024",
                "Điều 202, 203 Luật Đất đai (Thủ tục hòa giải bắt buộc tại UBND xã/phường)",
            ]

        # 2. Trích xuất số tiền tranh chấp
        claim_amount = 0.0
        m_money = re.search(r"(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?)\s*(tỷ|triệu|đồng|vnd|vnđ)", lower)
        if m_money:
            num_str = m_money.group(1)
            unit = m_money.group(2)
            if "." in num_str and num_str.count(".") >= 1 and "đồng" in unit:
                val = float(num_str.replace(".", "").replace(",", "."))
            else:
                val = float(num_str.replace(",", "."))

            if "tỷ" in unit:
                claim_amount = val * 1_000_000_000
            elif "triệu" in unit:
                claim_amount = val * 1_000_000
            else:
                claim_amount = val

        # 3. Phân tích lãi suất nếu là hợp đồng vay
        interest_valid = True
        warnings: list[str] = []
        if dispute_type == CivilDisputeType.CONTRACT_LOAN:
            m_rate = re.search(r"(\d+(?:[.,]\d+)?)\s*%\s*(?:/|\s*mỗi\s*)?\s*(?:tháng|năm)?", lower)
            if m_rate:
                rate = float(m_rate.group(1).replace(",", "."))
                # Nếu ghi %/tháng > 1.66% hoặc %/năm > 20%
                if "tháng" in m_rate.group(0) and rate > 1.66:
                    interest_valid = False
                    warnings.append(
                        f"CẢNH BÁO LÃI SUẤT: Mức lãi {rate}%/tháng (~{rate*12}%/năm) vượt quá trần 20%/năm theo Điều 468 BLDS 2015. Phần lãi suất vượt quá sẽ bị Tòa án tuyên vô hiệu."
                    )
                elif rate > 20.0 and "tháng" not in m_rate.group(0):
                    interest_valid = False
                    warnings.append(
                        f"CẢNH BÁO LÃI SUẤT: Mức lãi {rate}%/năm vượt trần 20%/năm theo Khoản 1 Điều 468 BLDS 2015."
                    )

        # 4. Thời hiệu khởi kiện
        statute_note = "Thời hiệu khởi kiện yêu cầu bồi thường/thực hiện hợp đồng là 03 năm kể từ ngày người có quyền yêu cầu biết hoặc phải biết quyền của mình bị xâm phạm (Điều 429, Điều 588 BLDS 2015)."
        if dispute_type == CivilDisputeType.INHERITANCE:
            statute_note = "Thời hiệu yêu cầu chia di sản thừa kế là 30 năm đối với bất động sản, 10 năm đối với động sản kể từ thời điểm mở thừa kế (Điều 623 BLDS 2015)."

        # 5. Các bước giải quyết tranh chấp tối ưu
        suggested_steps = [
            "Bước 1: Gửi văn bản thông báo yêu cầu thực hiện nghĩa vụ / Thông báo vi phạm (đính kèm chứng cứ hợp đồng, giấy tờ chuyển tiền).",
            "Bước 2: Tiến hành Thương lượng trực tiếp hoặc mời bên thứ ba Hòa giải cơ sở.",
            "Bước 3: Tham gia Hòa giải tiền tố tụng tại Trung tâm Hòa giải hoặc tại Tòa án theo Luật Hòa giải, đối thoại tại Tòa án 2020 (tiết kiệm 100% án phí nếu hòa giải thành).",
            "Bước 4: Nộp Đơn khởi kiện tại Tòa án nhân dân cấp huyện nơi Bị đơn cư trú hoặc làm việc (kèm hồ sơ chứng cứ và biên lai nộp tạm ứng án phí).",
            "Bước 5: Tham gia các phiên họp kiểm tra việc giao nộp, tiếp cận, công khai chứng cứ và hòa giải tại Tòa án theo BLTTDS 2015.",
        ]

        if dispute_type == CivilDisputeType.PROPERTY_LAND:
            suggested_steps.insert(
                2,
                "LƯU Ý ĐẤT ĐAI: Bắt buộc phải thông qua thủ tục Hòa giải tại UBND xã/phường/thị trấn nơi có đất tranh chấp trước khi khởi kiện ra Tòa án (Điều 202 Luật Đất đai).",
            )

        court_fee = cls.calculate_civil_court_fee(claim_amount)

        legal_assessment = (
            f"Vụ việc thuộc thẩm quyền giải quyết của Tòa án nhân dân theo thủ tục tố tụng dân sự. "
            f"Bản chất tranh chấp: {dispute_name}. "
            f"Yêu cầu khởi kiện cần đáp ứng điều kiện về tư cách khởi kiện, thời hiệu và nghĩa vụ cung cấp tài liệu, chứng cứ chứng minh theo Điều 91 BLTTDS 2015."
        )

        return CivilDisputeAnalysis(
            dispute_type=dispute_type,
            dispute_name=dispute_name,
            applicable_laws=applicable_laws,
            claim_amount_vnd=claim_amount,
            interest_rate_claim_valid=interest_valid,
            statute_of_limitations_note=statute_note,
            suggested_steps=suggested_steps,
            estimated_court_fee_vnd=court_fee,
            legal_assessment=legal_assessment,
            risk_warnings=warnings,
        )


def analyze_civil_dispute(text: str) -> dict[str, Any]:
    """Hàm tiện ích trả về dict phân tích dân sự chuẩn."""
    res = CivilDisputeResolver.analyze(text)
    return {
        "domain": "civil",
        "domain_name": "Pháp luật Dân sự & Hợp đồng",
        "dispute_type": res.dispute_type.value,
        "dispute_name": res.dispute_name,
        "applicable_laws": res.applicable_laws,
        "claim_amount_vnd": res.claim_amount_vnd,
        "claim_amount_formatted": f"{res.claim_amount_vnd:,.0f} VNĐ" if res.claim_amount_vnd > 0 else "Không xác định rõ giá trị",
        "estimated_court_fee_vnd": res.estimated_court_fee_vnd,
        "estimated_court_fee_formatted": f"{res.estimated_court_fee_vnd:,.0f} VNĐ",
        "statute_of_limitations_note": res.statute_of_limitations_note,
        "suggested_steps": res.suggested_steps,
        "legal_assessment": res.legal_assessment,
        "risk_warnings": res.risk_warnings,
    }
