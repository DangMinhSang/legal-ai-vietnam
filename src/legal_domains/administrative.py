"""Module phân tích và giải quyết tranh chấp Hành chính & Tranh chấp với cơ quan nhà nước.

Căn cứ pháp lý:
1. Luật Khiếu nại 2011 (Thủ tục khiếu nại hành chính tiền tố tụng).
2. Luật Tố tụng Hành chính 2015 (Khởi kiện vụ án hành chính tại Tòa án nhân dân).
3. Luật Xử lý vi phạm hành chính 2012 (sửa đổi, bổ sung 2020).
4. Luật Tiếp công dân 2013 và Luật Đất đai (về thu hồi đất, bồi thường GPMB).

Đối tượng khởi kiện/khiếu nại:
- Quyết định hành chính: Quyết định xử phạt VPHC, Quyết định thu hồi đất, Quyết định cưỡng chế, Quyết định truy thu thuế...
- Hành vi hành chính: Hành vi chậm trễ cấp GCNQSDĐ, hành vi ngăn cản trái pháp luật, hành vi cưỡng chế phá dỡ tài sản...
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AdministrativeActType(str, Enum):
    """Đối tượng tranh chấp với cơ quan nhà nước."""

    ADMIN_DECISION_LAND = "decision_land"  # QĐ thu hồi đất, bồi thường giải phóng mặt bằng, cưỡng chế
    ADMIN_DECISION_PENALTY = "decision_penalty"  # QĐ xử phạt vi phạm hành chính
    ADMIN_DECISION_TAX = "decision_tax"  # QĐ truy thu thuế, ấn định thuế, xử phạt hải quan
    ADMIN_DECISION_LICENSE = "decision_license"  # QĐ thu hồi giấy phép kinh doanh, xây dựng, môi trường
    ADMIN_ACT_OMISSION = "act_omission"  # Hành vi hành chính không hành động (chậm cấp sổ, không giải quyết khiếu nại)
    ADMIN_ACT_ILLEGAL = "act_illegal"  # Hành vi hành chính trái pháp luật (cưỡng chế khi chưa có quyết định)
    OTHER_ADMIN = "other_admin"


class AdminResolutionStage(str, Enum):
    """Giai đoạn giải quyết tranh chấp hành chính."""

    COMPLAINT_STAGE_1 = "khieu_nai_lan_1"  # Khiếu nại đến người đã ban hành quyết định hành chính
    COMPLAINT_STAGE_2 = "khieu_nai_lan_2"  # Khiếu nại đến thủ trưởng cấp trên trực tiếp
    COURT_LITIGATION = "khoi_kien_toa_an"  # Khởi kiện trực tiếp vụ án hành chính tại TAND có thẩm quyền


@dataclass
class AdministrativeDisputeAnalysis:
    """Kết quả phân tích toàn diện tranh chấp hành chính với cơ quan nhà nước."""

    act_type: AdministrativeActType
    target_description: str
    state_agency_named: str
    applicable_laws: list[str]
    time_limit_complaint: str  # 90 ngày theo Điều 9 Luật Khiếu nại
    time_limit_court: str  # 01 năm theo Điều 116 Luật Tố tụng Hành chính
    recommended_path: str
    two_track_options: dict[str, Any] = field(default_factory=dict)
    urgent_temporary_measures: list[str] = field(default_factory=list)
    action_steps: list[str] = field(default_factory=list)
    legal_evaluation: str = ""
    critical_notes: list[str] = field(default_factory=list)


class AdministrativeDisputeResolver:
    """Động cơ phân tích tranh chấp hành chính và định hướng quyền khiếu nại / khởi kiện."""

    @classmethod
    def analyze(cls, text: str) -> AdministrativeDisputeAnalysis:
        """Phân tích hồ sơ khiếu kiện hành chính."""
        lower = text.lower()

        # 1. Nhận diện cơ quan nhà nước liên quan
        agency = "Cơ quan hành chính nhà nước / Người có thẩm quyền"
        m_agency = re.search(r"(?:ubnd|ủy ban nhân dân|chủ tịch|chi cục|cục thuế|công an|sở|phòng)\s+([^\n.,;]+)", text, re.IGNORECASE)
        if m_agency:
            agency = m_agency.group(0).strip()

        # 2. Nhận diện đối tượng bị khiếu kiện
        act_type = AdministrativeActType.OTHER_ADMIN
        target_desc = "Quyết định hành chính hoặc hành vi hành chính"
        applicable_laws = [
            "Luật Tố tụng Hành chính 2015",
            "Luật Khiếu nại 2011",
        ]

        urgent_measures = [
            "Đề nghị Tòa án áp dụng biện pháp khẩn cấp tạm thời: 'Tạm đình chỉ việc thi hành quyết định hành chính' (Khoản 1 Điều 68 Luật Tố tụng Hành chính 2015) để tránh thiệt hại không thể khắc phục được.",
        ]

        if any(kw in lower for kw in ["thu hồi đất", "giải phóng mặt bằng", "bồi thường đất", "tái định cư", "cưỡng chế đất"]):
            act_type = AdministrativeActType.ADMIN_DECISION_LAND
            target_desc = "Quyết định thu hồi đất / Phương án bồi thường, hỗ trợ, tái định cư / Quyết định cưỡng chế thu hồi đất"
            applicable_laws.extend([
                "Luật Đất đai 2013 / Luật Đất đai 2024",
                "Nghị định 47/2014/NĐ-CP về bồi thường, hỗ trợ, tái định cư khi Nhà nước thu hồi đất",
                "Điều 69, 71 Luật Đất đai (Trình tự, thủ tục thu hồi đất và cưỡng chế thu hồi đất)",
            ])
        elif any(kw in lower for kw in ["xử phạt", "phạt tiền", "tịch thu tang vật", "vi phạm hành chính", "biên bản vi phạm"]):
            act_type = AdministrativeActType.ADMIN_DECISION_PENALTY
            target_desc = "Quyết định xử phạt vi phạm hành chính"
            applicable_laws.extend([
                "Luật Xử lý vi phạm hành chính 2012 (sửa đổi, bổ sung 2020)",
                "Nghị định quy định xử phạt vi phạm hành chính trong lĩnh vực chuyên ngành tương ứng",
            ])
        elif any(kw in lower for kw in ["thuế", "truy thu", "ấn định thuế", "chậm nộp", "hải quan"]):
            act_type = AdministrativeActType.ADMIN_DECISION_TAX
            target_desc = "Quyết định ấn định thuế / Quyết định truy thu thuế hoặc xử phạt thuế"
            applicable_laws.extend([
                "Luật Quản lý thuế 2019",
                "Nghị định 125/2020/NĐ-CP về xử phạt vi phạm hành chính về thuế, hóa đơn",
            ])
        elif any(kw in lower for kw in ["không cấp", "chậm trễ", "không trả lời", "hành vi", "cố tình kéo dài", "từ chối giải quyết"]):
            act_type = AdministrativeActType.ADMIN_ACT_OMISSION
            target_desc = "Hành vi hành chính không thực hiện hoặc chậm trễ thực hiện nhiệm vụ, công vụ"
            applicable_laws.extend([
                "Luật Cán bộ, công chức 2008 (sửa đổi 2019)",
                "Khoản 4 Điều 3 Luật Tố tụng Hành chính 2015 (Hành vi hành chính bị kiện)",
            ])

        # 3. Phân tích thời hiệu kép
        complaint_limit = "90 ngày kể từ ngày nhận được quyết định hành chính hoặc biết được hành vi hành chính (Điều 9 Luật Khiếu nại 2011)."
        court_limit = "01 năm kể từ ngày nhận được hoặc biết được quyết định hành chính, hành vi hành chính (Điểm a Khoản 2 Điều 116 Luật Tố tụng Hành chính 2015)."

        # 4. Định hướng lộ trình giải quyết (Two-Track Approach)
        two_track = {
            "track_1_complaint": {
                "name": "Kênh 1: Khiếu nại hành chính nội bộ (Tiền tố tụng)",
                "step_1": f"Khiếu nại lần 1 đến chính {agency} (thời hạn 90 ngày). Người giải quyết khiếu nại phải thụ lý và ra Quyết định giải quyết khiếu nại trong 30-45 ngày.",
                "step_2": "Nếu không đồng ý với QĐ giải quyết lần 1 hoặc hết hạn mà không giải quyết: Khiếu nại lần 2 lên Thủ trưởng cơ quan cấp trên trực tiếp (trong vòng 30 ngày).",
                "pros": "Không mất án phí, thủ tục linh hoạt, phù hợp khi cơ quan nhận thấy có sai sót về giấy tờ/số liệu.",
                "cons": "Tính khách quan có thể bị hạn chế do người giải quyết là cơ quan ban hành quyết định.",
            },
            "track_2_litigation": {
                "name": "Kênh 2: Khởi kiện trực tiếp ra Tòa án nhân dân (Tố tụng Hành chính)",
                "action": "Người dân/Doanh nghiệp có quyền KHỞI KIỆN TRỰC TIẾP ra TAND có thẩm quyền mà KHÔNG bắt buộc phải trải qua thủ tục khiếu nại trước (Điều 115 Luật Tố tụng Hành chính 2015).",
                "jurisdiction": "TAND cấp tỉnh (nếu kiện QĐ của UBND cấp huyện/cấp tỉnh theo Điều 32 Luật TTHC) hoặc TAND cấp huyện.",
                "pros": "Được xét xử độc lập bởi Hội đồng xét xử, quyền tiếp cận hồ sơ tài liệu đầy đủ, phán quyết có hiệu lực cưỡng chế thi hành.",
                "cons": "Phải chuẩn bị hồ sơ pháp lý chặt chẽ và đóng tạm ứng án phí hành chính sơ thẩm (300.000 VNĐ).",
            },
        }

        action_steps = [
            f"Bước 1: Thu thập đầy đủ bản gốc/bản sao có chứng thực của {target_desc}, biên bản làm việc, thông báo và các chứng cứ chứng minh thiệt hại.",
            "Bước 2: Lập văn bản yêu cầu giải trình hoặc Đơn khiếu nại lần 1 gửi người đứng đầu cơ quan đã ban hành quyết định.",
            "Bước 3: Song song hoặc nếu khiếu nại không thỏa đáng, soạn thảo Đơn khởi kiện vụ án hành chính theo Mẫu số 01-HC ban hành kèm theo Nghị quyết 02/2017/NQ-HĐTP.",
            "Bước 4: Nộp đơn khởi kiện đến Tòa án nhân dân có thẩm quyền kèm Đơn yêu cầu áp dụng biện pháp khẩn cấp tạm thời đình chỉ thi hành quyết định để bảo toàn hiện trạng.",
            "Bước 5: Tham gia phiên đối thoại theo Luật Tố tụng Hành chính và các phiên tranh tụng công khai tại Tòa án.",
        ]

        notes = [
            "QUAN TRỌNG: Theo Luật Tố tụng Hành chính 2015, người dân KHÔNG bắt buộc phải khiếu nại trước, có quyền khởi kiện thẳng ra Tòa án bất kỳ lúc nào trong thời hiệu 01 năm.",
            "Nghĩa vụ chứng minh: Cơ quan nhà nước bị kiện có nghĩa vụ cung cấp tài liệu, chứng cứ làm căn cứ ban hành quyết định hành chính trước Tòa án (Điều 78 Luật TTHC).",
        ]

        legal_eval = (
            f"Vụ việc thể hiện tranh chấp hành chính công giữa cá nhân/tổ chức với {agency}. "
            f"Quyết định/Hành vi bị ảnh hưởng: {target_desc}. "
            f"Người bị ảnh hưởng được pháp luật bảo vệ quyền khởi kiện vụ án hành chính tại Tòa án nhân dân để yêu cầu hủy bỏ một phần hoặc toàn bộ quyết định trái luật và yêu cầu bồi thường thiệt hại theo Luật Trách nhiệm bồi thường của Nhà nước."
        )

        return AdministrativeDisputeAnalysis(
            act_type=act_type,
            target_description=target_desc,
            state_agency_named=agency,
            applicable_laws=applicable_laws,
            time_limit_complaint=complaint_limit,
            time_limit_court=court_limit,
            recommended_path="Khởi kiện vụ án hành chính tại TAND cấp có thẩm quyền kết hợp yêu cầu áp dụng BPKCTT tạm đình chỉ quyết định.",
            two_track_options=two_track,
            urgent_temporary_measures=urgent_measures,
            action_steps=action_steps,
            legal_evaluation=legal_eval,
            critical_notes=notes,
        )


def analyze_administrative_dispute(text: str) -> dict[str, Any]:
    """Hàm tiện ích phân tích tranh chấp hành chính."""
    res = AdministrativeDisputeResolver.analyze(text)
    return {
        "domain": "administrative",
        "domain_name": "Pháp luật Hành chính & Tranh chấp với Cơ quan Nhà nước",
        "act_type": res.act_type.value,
        "dispute_type": res.act_type.value,
        "target_description": res.target_description,
        "state_agency_named": res.state_agency_named,
        "applicable_laws": res.applicable_laws,
        "time_limit_complaint": res.time_limit_complaint,
        "time_limit_court": res.time_limit_court,
        "recommended_path": res.recommended_path,
        "two_track_options": res.two_track_options,
        "urgent_temporary_measures": res.urgent_temporary_measures,
        "action_steps": res.action_steps,
        "legal_evaluation": res.legal_evaluation,
        "critical_notes": res.critical_notes,
    }
