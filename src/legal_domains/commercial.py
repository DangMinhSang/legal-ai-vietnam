"""Module phân tích và giải quyết tranh chấp Kinh doanh Thương mại & Trọng tài Thương mại.

Căn cứ pháp lý:
1. Luật Thương mại 2005 (LTM 2005)
2. Luật Trọng tài Thương mại 2010 (Luật TTTM 2010)
3. Bộ luật Dân sự 2015 (quy định chung về hợp đồng và nghĩa vụ)
4. Quy tắc Tố tụng Trọng tài của Trung tâm Trọng tài Quốc tế Việt Nam (VIAC)

Các nguyên tắc thương mại cốt lõi:
- Mức phạt vi phạm hợp đồng tối đa KHÔNG QUÁ 8% giá trị phần nghĩa vụ hợp đồng bị vi phạm (Điều 301 LTM 2005).
- Bồi thường thiệt hại bao gồm tổn thất thực tế, trực tiếp và khoản lợi trực tiếp bị bỏ lỡ (Điều 302 LTM 2005).
- Thỏa thuận Trọng tài hợp lệ có hiệu lực loại trừ thẩm quyền giải quyết của Tòa án (Điều 6 Luật TTTM 2010).
- Miễn trách nhiệm vi phạm hợp đồng trong trường hợp Bất khả kháng (Điều 294 LTM 2005).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CommercialDisputeType(str, Enum):
    """Phân loại tranh chấp kinh doanh thương mại."""

    SALE_OF_GOODS = "sale_of_goods"  # Hợp đồng mua bán hàng hóa (giao thiếu, hàng lỗi, chậm giao)
    SERVICE_PROVISION = "service_provision"  # Hợp đồng cung ứng dịch vụ (logistics, gia công, IT, quảng cáo)
    PAYMENT_DEFAULT = "payment_default"  # Vi phạm nghĩa vụ thanh toán, chậm trả tiền hàng
    BREACH_PENALTY_CLAIM = "breach_penalty"  # Tranh chấp về phạt vi phạm hợp đồng và bồi thường thiệt hại
    FORCE_MAJEURE = "force_majeure"  # Tranh chấp về sự kiện bất khả kháng và miễn trách nhiệm
    DISTRIBUTION_AGENCY = "distribution_agency"  # Tranh chấp đại lý, phân phối, nhượng quyền thương mại (franchise)
    OTHER_COMMERCIAL = "other_commercial"


class CommercialRemedyType(str, Enum):
    """Các chế tài trong thương mại theo Điều 292 LTM 2005."""

    SPECIFIC_PERFORMANCE = "buoc_thuc_hien_dung"  # Buộc thực hiện đúng hợp đồng
    PENALTY_8_PERCENT = "phat_vi_pham"  # Phạt vi phạm (tối đa 8%)
    COMPENSATORY_DAMAGES = "boi_thuong_thiet_hai"  # Bồi thường thiệt hại thực tế
    SUSPENSION = "tam_ngung_thuc_hien"  # Tạm ngừng thực hiện hợp đồng
    TERMINATION = "huy_bo_hop_dong"  # Hủy bỏ hợp đồng


@dataclass
class CommercialDisputeAnalysis:
    """Kết quả phân tích tranh chấp kinh doanh thương mại."""

    dispute_type: CommercialDisputeType
    dispute_name: str
    applicable_laws: list[str]
    contract_value_vnd: float = 0.0
    breached_obligation_value_vnd: float = 0.0
    penalty_claim_vnd: float = 0.0
    is_penalty_within_8_percent: bool = True
    max_legal_penalty_vnd: float = 0.0
    actual_damage_claim_vnd: float = 0.0
    arbitration_clause_found: bool = False
    forum_recommendation: str = ""
    remedies_applied: list[dict[str, Any]] = field(default_factory=list)
    suggested_steps: list[str] = field(default_factory=list)
    legal_assessment: str = ""
    risk_warnings: list[str] = field(default_factory=list)


class CommercialDisputeResolver:
    """Động cơ phân tích chế tài và giải quyết tranh chấp kinh doanh thương mại."""

    @classmethod
    def analyze(cls, text: str) -> CommercialDisputeAnalysis:
        """Phân tích hồ sơ tranh chấp hợp đồng thương mại."""
        lower = text.lower()

        # 1. Nhận diện loại tranh chấp
        dispute_type = CommercialDisputeType.SALE_OF_GOODS
        dispute_name = "Tranh chấp Hợp đồng mua bán hàng hóa thương mại"
        applicable_laws = [
            "Luật Thương mại 2005",
            "Bộ luật Dân sự 2015",
            "Luật Trọng tài Thương mại 2010",
        ]

        if any(kw in lower for kw in ["cung ứng dịch vụ", "gia công", "logistics", "vận chuyển hàng hóa", "phần mềm"]):
            dispute_type = CommercialDisputeType.SERVICE_PROVISION
            dispute_name = "Tranh chấp Hợp đồng cung ứng dịch vụ thương mại"
        elif any(kw in lower for kw in ["chậm thanh toán", "quá hạn thanh toán", "nợ tiền hàng", "chưa thanh toán"]):
            dispute_type = CommercialDisputeType.PAYMENT_DEFAULT
            dispute_name = "Tranh chấp vi phạm nghĩa vụ thanh toán trong thương mại"
        elif any(kw in lower for kw in ["phạt vi phạm", "8%", "yêu cầu phạt", "mức phạt"]):
            dispute_type = CommercialDisputeType.BREACH_PENALTY_CLAIM
            dispute_name = "Tranh chấp áp dụng chế tài Phạt vi phạm và Bồi thường thiệt hại"
        elif any(kw in lower for kw in ["bất khả kháng", "dịch bệnh", "thiên tai", "chiến tranh", "miễn trách nhiệm"]):
            dispute_type = CommercialDisputeType.FORCE_MAJEURE
            dispute_name = "Tranh chấp về sự kiện bất khả kháng và miễn trách nhiệm thương mại (Điều 294 LTM)"

        # 2. Trích xuất giá trị hợp đồng và phần nghĩa vụ bị vi phạm
        contract_val = 0.0
        breached_val = 0.0
        penalty_claim = 0.0
        damage_claim = 0.0

        # Regex tìm các con số tài chính
        numbers = re.findall(r"(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?)\s*(tỷ|triệu|đồng|vnd|vnđ)", lower)
        vals_vnd: list[float] = []
        for num_str, unit in numbers:
            if "." in num_str and num_str.count(".") >= 1 and "đồng" in unit:
                raw = float(num_str.replace(".", "").replace(",", "."))
            else:
                raw = float(num_str.replace(",", "."))
            if "tỷ" in unit:
                vals_vnd.append(raw * 1_000_000_000)
            elif "triệu" in unit:
                vals_vnd.append(raw * 1_000_000)
            else:
                vals_vnd.append(raw)

        if len(vals_vnd) == 1:
            contract_val = vals_vnd[0]
            breached_val = contract_val
        elif len(vals_vnd) == 2:
            contract_val = vals_vnd[0]
            breached_val = contract_val
            penalty_claim = vals_vnd[1]
        elif len(vals_vnd) >= 3:
            contract_val = vals_vnd[0]
            breached_val = vals_vnd[1]
            penalty_claim = vals_vnd[2]
            if len(vals_vnd) >= 4:
                damage_claim = vals_vnd[3]

        # Kiểm tra tỷ lệ % phạt vi phạm (ví dụ: 15% hoặc 8%)
        m_pct = re.search(r"(\d+(?:[.,]\d+)?)\s*%", lower)
        if m_pct and penalty_claim == 0.0 and breached_val > 0.0:
            pct = float(m_pct.group(1).replace(",", "."))
            penalty_claim = breached_val * (pct / 100.0)

        # 3. Phân tích trần phạt vi phạm 8% theo Điều 301 LTM 2005
        max_penalty = breached_val * 0.08 if breached_val > 0 else 0.0
        is_penalty_valid = True
        warnings: list[str] = []

        if penalty_claim > 0 and breached_val > 0:
            if penalty_claim > max_penalty:
                is_penalty_valid = False
                warnings.append(
                    f"CẢNH BÁO PHẠT VI PHẠM: Mức phạt yêu cầu ({penalty_claim:,.0f} VNĐ) đã vượt quá trần luật định 8% giá trị phần nghĩa vụ bị vi phạm "
                    f"(Trần tối đa cho phép theo Điều 301 Luật Thương mại 2005 là: {max_penalty:,.0f} VNĐ). Phần vượt quá 8% sẽ không được Tòa án/Trọng tài chấp nhận."
                )

        # 4. Kiểm tra điều khoản Trọng tài (Arbitration Clause)
        has_arbitration = any(kw in lower for kw in ["trọng tài", "viac", "trung tâm trọng tài", "arbitration"])
        if has_arbitration:
            forum = "Giải quyết tại Trung tâm Trọng tài Thương mại (Ví dụ: VIAC) theo thỏa thuận trọng tài hợp lệ của các bên (Điều 6 Luật TTTM 2010)."
        else:
            forum = "Giải quyết tại Tòa án nhân dân cấp có thẩm quyền (Tòa Kinh tế) theo thủ tục Tố tụng Dân sự."

        # 5. Các chế tài thương mại đề xuất
        remedies: list[dict[str, Any]] = [
            {
                "remedy": CommercialRemedyType.SPECIFIC_PERFORMANCE.value,
                "name": "1. Buộc thực hiện đúng hợp đồng (Điều 297 LTM)",
                "description": "Yêu cầu bên vi phạm giao đủ hàng, sửa chữa khuyết tật hoặc thanh toán đúng hạn trong một thời hạn gia hạn hợp lý.",
            },
            {
                "remedy": CommercialRemedyType.PENALTY_8_PERCENT.value,
                "name": "2. Phạt vi phạm hợp đồng (Điều 300 & 301 LTM)",
                "max_allowed_vnd": max_penalty,
                "formatted": f"Tối đa {max_penalty:,.0f} VNĐ (8% phần vi phạm)",
                "note": "Điều kiện áp dụng: Hợp đồng phải có thỏa thuận phạt vi phạm rõ ràng.",
            },
            {
                "remedy": CommercialRemedyType.COMPENSATORY_DAMAGES.value,
                "name": "3. Bồi thường thiệt hại (Điều 302 LTM)",
                "description": "Bồi thường tổn thất thực tế, trực tiếp và lợi nhuận trực tiếp bị mất. Áp dụng ngay cả khi hợp đồng không thỏa thuận trước về bồi thường.",
            },
        ]

        suggested_steps = [
            "Bước 1: Rà soát kỹ Hợp đồng thương mại, Phụ lục và Biên bản giao nhận để xác định có thỏa thuận Phạt vi phạm hay không.",
            "Bước 2: Gửi Công văn Thông báo vi phạm (Notice of Default) và Thông báo áp dụng chế tài trong thời hạn luật định (thời hạn khiếu nại thường là 3 tháng đối với số lượng, 6 tháng đối với chất lượng theo Điều 318 LTM).",
            "Bước 3: Tổ chức phiên Thương lượng trực tiếp giữa đại diện có thẩm quyền của hai doanh nghiệp.",
            f"Bước 4: Nếu thương lượng bất thành, căn cứ vào điều khoản giải quyết tranh chấp: {forum}.",
            "Bước 5: Áp dụng biện pháp khẩn cấp tạm thời (kê biên tài sản, phong tỏa tài khoản ngân hàng) để bảo đảm thi hành phán quyết.",
        ]

        legal_eval = (
            f"Vụ việc xác lập quan hệ hợp đồng thương mại giữa các chủ thể kinh doanh có mục đích sinh lợi. "
            f"Bản chất: {dispute_name}. "
            f"Áp dụng nguyên tắc kết hợp: Bên bị vi phạm có quyền áp dụng đồng thời cả chế tài Phạt vi phạm (tối đa 8%) và Bồi thường thiệt hại thực tế theo quy định tại Điều 307 Luật Thương mại 2005."
        )

        return CommercialDisputeAnalysis(
            dispute_type=dispute_type,
            dispute_name=dispute_name,
            applicable_laws=applicable_laws,
            contract_value_vnd=contract_val,
            breached_obligation_value_vnd=breached_val,
            penalty_claim_vnd=penalty_claim,
            is_penalty_within_8_percent=is_penalty_valid,
            max_legal_penalty_vnd=max_penalty,
            actual_damage_claim_vnd=damage_claim,
            arbitration_clause_found=has_arbitration,
            forum_recommendation=forum,
            remedies_applied=remedies,
            suggested_steps=suggested_steps,
            legal_assessment=legal_eval,
            risk_warnings=warnings,
        )


def analyze_commercial_dispute(text: str) -> dict[str, Any]:
    """Hàm tiện ích phân tích tranh chấp kinh doanh thương mại."""
    res = CommercialDisputeResolver.analyze(text)
    return {
        "domain": "commercial",
        "domain_name": "Pháp luật Kinh doanh Thương mại & Trọng tài",
        "dispute_type": res.dispute_type.value,
        "dispute_name": res.dispute_name,
        "applicable_laws": res.applicable_laws,
        "contract_value_vnd": res.contract_value_vnd,
        "contract_value_formatted": f"{res.contract_value_vnd:,.0f} VNĐ" if res.contract_value_vnd > 0 else "Chưa xác định",
        "breached_obligation_value_vnd": res.breached_obligation_value_vnd,
        "penalty_claim_vnd": res.penalty_claim_vnd,
        "max_legal_penalty_vnd": res.max_legal_penalty_vnd,
        "max_legal_penalty_formatted": f"{res.max_legal_penalty_vnd:,.0f} VNĐ (Trần 8%)",
        "arbitration_clause_found": res.arbitration_clause_found,
        "forum_recommendation": res.forum_recommendation,
        "remedies_applied": res.remedies_applied,
        "suggested_steps": res.suggested_steps,
        "legal_assessment": res.legal_assessment,
        "risk_warnings": res.risk_warnings,
    }
