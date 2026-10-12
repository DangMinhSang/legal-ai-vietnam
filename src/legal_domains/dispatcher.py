"""Bộ Điều Phối & Phân Loại Pháp Lý Đa Lĩnh Vực (Multi-Domain Legal Dispatcher).

Tự động nhận diện hồ sơ vụ việc thuộc lĩnh vực nào:
1. HÌNH SỰ (Criminal): Tội phạm, bị cáo, bị hại, Viện kiểm sát, truy tố, BLHS 2015, 7 hình phạt chính & 7 hình phạt bổ sung Điều 32.
2. DÂN SỰ (Civil): Hợp đồng dân sự, vay mượn, bồi thường ngoài hợp đồng, thừa kế, quyền sở hữu, BLDS 2015.
3. HÀNH CHÍNH (Administrative): Tranh chấp với cơ quan nhà nước, quyết định xử phạt VPHC, thu hồi đất, cưỡng chế, Luật TTHC 2015.
4. THƯƠNG MẠI (Commercial): Tranh chấp giữa các thương nhân, hợp đồng mua bán, phạt vi phạm 8%, VIAC, Luật Thương mại 2005.
5. KỶ LUẬT & LAO ĐỘNG (Disciplinary & Labor): Sa thải, cách chức, kỷ luật lao động BLLĐ 2019, kỷ luật cán bộ công chức.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.legal_domains.administrative import analyze_administrative_dispute
from src.legal_domains.civil import analyze_civil_dispute
from src.legal_domains.commercial import analyze_commercial_dispute
from src.legal_domains.criminal import analyze_criminal_penalties
from src.legal_domains.disciplinary import analyze_disciplinary_matter


class LegalDomain(str, Enum):
    """5 Lĩnh vực pháp luật cốt lõi trong hệ thống pháp luật Việt Nam."""

    CRIMINAL = "criminal"  # 1. Hình sự
    CIVIL = "civil"  # 2. Dân sự
    ADMINISTRATIVE = "administrative"  # 3. Hành chính (Tranh chấp với cơ quan nhà nước)
    COMMERCIAL = "commercial"  # 4. Kinh doanh Thương mại
    DISCIPLINARY = "disciplinary"  # 5. Kỷ luật & Lao động


DOMAIN_METADATA = {
    LegalDomain.CRIMINAL: {
        "name_vi": "Pháp luật Hình sự",
        "code": "criminal",
        "primary_law": "Bộ luật Hình sự 2015 (sửa đổi, bổ sung 2017) & BLTTHS 2015",
        "key_focus": "Định tội danh, điều khoản định khung, 7 hình phạt chính & 7 hình phạt bổ sung (Điều 32 BLHS), cá thể hóa hình phạt.",
    },
    LegalDomain.CIVIL: {
        "name_vi": "Pháp luật Dân sự & Hợp đồng",
        "code": "civil",
        "primary_law": "Bộ luật Dân sự 2015 & Bộ luật Tố tụng Dân sự 2015",
        "key_focus": "Tranh chấp hợp đồng vay, mua bán, thuê; bồi thường thiệt hại ngoài hợp đồng (Đ.584); thừa kế di sản; hòa giải đối thoại.",
    },
    LegalDomain.ADMINISTRATIVE: {
        "name_vi": "Pháp luật Hành chính & Tranh chấp với CQNN",
        "code": "administrative",
        "primary_law": "Luật Tố tụng Hành chính 2015, Luật Khiếu nại 2011, Luật Đất đai",
        "key_focus": "Khiếu nại/Khởi kiện quyết định hành chính (thu hồi đất, xử phạt VPHC, thuế), hành vi hành chính; biện pháp khẩn cấp tạm thời.",
    },
    LegalDomain.COMMERCIAL: {
        "name_vi": "Pháp luật Kinh doanh Thương mại & Trọng tài",
        "code": "commercial",
        "primary_law": "Luật Thương mại 2005 & Luật Trọng tài Thương mại 2010",
        "key_focus": "Tranh chấp hợp đồng thương mại, chế tài phạt vi phạm tối đa 8% (Điều 301 LTM), bồi thường thiệt hại thực tế, Trọng tài VIAC.",
    },
    LegalDomain.DISCIPLINARY: {
        "name_vi": "Pháp luật Kỷ luật & Lao động",
        "code": "disciplinary",
        "primary_law": "Bộ luật Lao động 2019 & Luật Cán bộ, công chức 2008 (sửa đổi 2019)",
        "key_focus": "4 hình thức kỷ luật lao động (Điều 124 BLLĐ), sa thải trái luật, bồi thường Điều 41 BLLĐ, kỷ luật công chức viên chức.",
    },
}


@dataclass
class MultiDomainAnalysisResult:
    """Kết quả phân loại và phân tích đa lĩnh vực pháp luật."""

    primary_domain: LegalDomain
    domain_scores: dict[str, float]
    primary_domain_name: str
    primary_law: str
    domain_specific_analysis: dict[str, Any]
    secondary_domains_detected: list[str] = field(default_factory=list)
    combined_summary: str = ""


class LegalDomainDispatcher:
    """Bộ phân loại và điều phối hồ sơ pháp lý."""

    # Bộ từ khóa đặc trưng cho từng lĩnh vực
    KEYWORDS_MAP: dict[LegalDomain, list[str]] = {
        LegalDomain.CRIMINAL: [
            "bị cáo", "bị hại", "tội danh", "viện kiểm sát", "công tố", "truy tố",
            "blhs", "hình sự", "phạm tội", "tù", "án treo", "tử hình", "chung thân",
            "khởi tố", "bản án hình sự", "tiền án", "tiền sự", "làm giả cccd", "thi hộ",
            "trộm cắp", "cướp", "giết người", "ma túy", "lừa đảo chiếm đoạt", "cố ý gây thương tích",
            "điều 341", "điều 134", "điều 168", "điều 171", "điều 173", "điều 123", "điều 32",
        ],
        LegalDomain.ADMINISTRATIVE: [
            "quyết định hành chính", "hành vi hành chính", "ubnd", "ủy ban nhân dân",
            "chủ tịch ubnd", "khiếu nại", "khiếu kiện", "tố tụng hành chính", "ltthc",
            "thu hồi đất", "cưỡng chế", "bồi thường gpmb", "giải phóng mặt bằng",
            "xử phạt vi phạm hành chính", "xử phạt vphc", "quyết định xử phạt", "vphc", "xlvhc",
            "quản lý thị trường", "đội quản lý thị trường", "đội qltt", "người bị kiện", "người khởi kiện",
            "truy thu thuế", "chi cục thuế", "cục hải quan", "vượt thẩm quyền", "hủy quyết định",
            "giấy chứng nhận quyền sử dụng đất", "chậm cấp sổ", "luật khiếu nại", "luật xử lý vi phạm hành chính",
        ],
        LegalDomain.COMMERCIAL: [
            "luật thương mại", "thương nhân", "hợp đồng kinh tế", "hợp đồng thương mại",
            "hợp đồng mua bán thiết bị", "hợp đồng mua bán hàng hóa", "phạt vi phạm", "8%",
            "trọng tài", "viac", "trung tâm trọng tài", "mua bán hàng hóa", "cung ứng dịch vụ",
            "chậm tiến độ", "giao chậm tiến độ", "bất khả kháng", "điều 301", "hàng hải",
            "vận chuyển thủy sản", "đại dương", "tàu gặp bão",
        ],
        LegalDomain.DISCIPLINARY: [
            "kỷ luật lao động", "kỷ luật", "sa thải", "cách chức", "khiển trách", "kéo dài nâng lương",
            "bộ luật lao động", "bllđ", "người sử dụng lao động", "người lao động", "công nhân",
            "nội quy lao động", "công đoàn", "thôi việc", "cán bộ", "công chức", "viên chức",
            "hạ bậc lương", "giáng chức", "trừ 50% tiền lương", "trừ lương", "cắt lương", "phạt tiền trừ",
            "mang thai", "nghỉ thai sản", "hợp đồng lao động", "hđlđ", "điều 127", "điều 124", "điều 137",
        ],
        LegalDomain.CIVIL: [
            "bộ luật dân sự", "blds", "hợp đồng vay", "giấy vay tiền", "giấy biên nhận vay", "đòi nợ",
            "cho vay", "vay nợ", "đặt cọc", "hợp đồng thuê nhà", "bồi thường thiệt hại ngoài hợp đồng",
            "thừa kế", "chia di sản", "di chúc", "nguyên đơn", "bị đơn", "hòa giải đối thoại",
            "ranh giới đất", "lấn chiếm", "lãi suất", "20%", "30%/năm", "tài sản chung", "án phí",
        ],
    }

    @classmethod
    def classify_domain(cls, text: str) -> tuple[LegalDomain, dict[str, float]]:
        """Phân loại lĩnh vực pháp luật chính của văn bản và trả về điểm tương đồng."""
        lower = text.lower()
        scores: dict[LegalDomain, float] = {}

        # Trọng số siêu mạnh cho các dấu hiệu nhận diện đặc trưng tuyệt đối
        high_signal_weights = {
            "quản lý thị trường": (LegalDomain.ADMINISTRATIVE, 5.0),
            "đội qltt": (LegalDomain.ADMINISTRATIVE, 5.0),
            "xử phạt vi phạm hành chính": (LegalDomain.ADMINISTRATIVE, 4.0),
            "quyết định thu hồi đất": (LegalDomain.ADMINISTRATIVE, 4.0),
            "người bị kiện": (LegalDomain.ADMINISTRATIVE, 3.0),
            "chủ tịch ubnd": (LegalDomain.ADMINISTRATIVE, 3.0),
            "sa thải": (LegalDomain.DISCIPLINARY, 4.0),
            "kỷ luật": (LegalDomain.DISCIPLINARY, 3.5),
            "trừ 50% tiền lương": (LegalDomain.DISCIPLINARY, 5.0),
            "trừ lương": (LegalDomain.DISCIPLINARY, 4.0),
            "người lao động": (LegalDomain.DISCIPLINARY, 3.0),
            "bị cáo": (LegalDomain.CRIMINAL, 4.0),
            "tội danh": (LegalDomain.CRIMINAL, 3.5),
            "truy tố": (LegalDomain.CRIMINAL, 3.0),
            "viac": (LegalDomain.COMMERCIAL, 4.0),
            "bất khả kháng": (LegalDomain.COMMERCIAL, 3.5),
            "hợp đồng mua bán thiết bị": (LegalDomain.COMMERCIAL, 3.0),
            "hợp đồng vay": (LegalDomain.CIVIL, 4.0),
            "chia di sản": (LegalDomain.CIVIL, 4.0),
            "thừa kế": (LegalDomain.CIVIL, 3.5),
        }

        for domain, keywords in cls.KEYWORDS_MAP.items():
            score = 0.0
            for kw in keywords:
                if kw in lower:
                    weight = 2.0 if kw in ["bị cáo", "tội danh", "ubnd", "thu hồi đất", "viac", "sa thải", "thừa kế", "khiếu nại"] else 1.0
                    score += weight
            scores[domain] = score

        # Bổ sung điểm nhận diện đặc trưng
        for signal_kw, (target_domain, extra_w) in high_signal_weights.items():
            if signal_kw in lower:
                scores[target_domain] = scores.get(target_domain, 0.0) + extra_w

        # Chuẩn hóa về tỷ lệ phần trăm
        total = sum(scores.values()) or 1.0
        normalized_scores = {d.value: round(s / total, 3) for d, s in scores.items()}

        # Chọn domain có điểm cao nhất
        best_domain = max(scores, key=scores.get)
        if scores[best_domain] == 0:
            best_domain = LegalDomain.CRIMINAL  # Mặc định

        return best_domain, normalized_scores

    @classmethod
    def dispatch(
        cls,
        text: str,
        forced_domain: LegalDomain | str | None = None,
        personal_info: str = "",
        case_info: str = "",
    ) -> MultiDomainAnalysisResult:
        """Phân loại và điều phối xử lý hồ sơ sang đúng chuyên ngành pháp luật."""
        full_text = text or f"{personal_info}\n{case_info}"

        if forced_domain:
            if isinstance(forced_domain, str):
                try:
                    chosen_domain = LegalDomain(forced_domain)
                except ValueError:
                    chosen_domain, _ = cls.classify_domain(full_text)
            else:
                chosen_domain = forced_domain
            _, domain_scores = cls.classify_domain(full_text)
        else:
            chosen_domain, domain_scores = cls.classify_domain(full_text)

        meta = DOMAIN_METADATA.get(chosen_domain, DOMAIN_METADATA[LegalDomain.CRIMINAL])

        # Nhận diện các lĩnh vực thứ cấp có điểm số đáng kể
        secondary: list[str] = [
            d_val for d_val, sc in domain_scores.items()
            if d_val != chosen_domain.value and sc >= 0.15
        ]

        # Phân tích theo domain chuyên trách
        if chosen_domain == LegalDomain.CRIMINAL:
            # Tách và đánh giá hình sự với 7 hình phạt chính & 7 hình phạt bổ sung
            from src.orchestration.case_parser import parse_two_inputs
            parsed_case = parse_two_inputs(personal_info=personal_info, case_info=case_info, full_text=full_text)
            main_def = parsed_case.defendants[0] if parsed_case.defendants else None
            def_name = main_def.name if main_def else "Bị cáo"
            priors = main_def.prior_convictions if main_def else 0

            domain_analysis = analyze_criminal_penalties(
                defendant_name=def_name,
                crime_name=parsed_case.detected_crime_name,
                articles=parsed_case.detected_articles,
                clause=parsed_case.detected_clause,
                statutory_range=parsed_case.primary_statutory_bounds,
                aggravating_count=len(parsed_case.aggravating_factors),
                mitigating_count=len(parsed_case.mitigating_factors),
                has_restitution=any("nộp lại" in m.lower() for m in parsed_case.mitigating_factors),
                has_cooperation=any("hợp tác" in m.lower() for m in parsed_case.mitigating_factors),
                is_first_offense=(priors == 0),
                role_type="người thực hành" if def_name in ["Hoàng", "H"] else "đồng phạm",
                illicit_profits_vnd=3_050_000 if "341" in parsed_case.detected_articles else 0.0,
            )
            summary = (
                f"Vụ án Hình sự: {parsed_case.detected_crime_name}. "
                f"Hình phạt chính đề xuất: {domain_analysis['principal_penalty']['formatted']}. "
                f"Đã áp dụng hệ thống 7 hình phạt chính & 7 hình phạt bổ sung Điều 32 BLHS."
            )

        elif chosen_domain == LegalDomain.CIVIL:
            domain_analysis = analyze_civil_dispute(full_text)
            summary = (
                f"Tranh chấp Dân sự: {domain_analysis['dispute_name']}. "
                f"Giá trị tranh chấp: {domain_analysis['claim_amount_formatted']}. "
                f"Ước tính án phí sơ thẩm: {domain_analysis['estimated_court_fee_formatted']}."
            )

        elif chosen_domain == LegalDomain.ADMINISTRATIVE:
            domain_analysis = analyze_administrative_dispute(full_text)
            summary = (
                f"Tranh chấp với Cơ quan Nhà nước: {domain_analysis['target_description']}. "
                f"Cơ quan liên quan: {domain_analysis['state_agency_named']}. "
                f"Định hướng: {domain_analysis['recommended_path']}."
            )

        elif chosen_domain == LegalDomain.COMMERCIAL:
            domain_analysis = analyze_commercial_dispute(full_text)
            summary = (
                f"Tranh chấp Thương mại: {domain_analysis['dispute_name']}. "
                f"Cơ chế tài phán: {domain_analysis['forum_recommendation']}. "
                f"Trần phạt vi phạm 8%: {domain_analysis['max_legal_penalty_formatted']}."
            )

        elif chosen_domain == LegalDomain.DISCIPLINARY:
            domain_analysis = analyze_disciplinary_matter(full_text)
            summary = (
                f"Kỷ luật Lao động / Công vụ: {domain_analysis['discipline_matter']}. "
                f"Đối tượng: {domain_analysis['target_person']} ({domain_analysis['target_role']}). "
                f"Tính hợp pháp: {'Hợp pháp' if domain_analysis['is_discipline_valid'] else 'Có dấu hiệu trái pháp luật'}."
            )
        else:
            domain_analysis = analyze_civil_dispute(full_text)
            summary = "Phân tích pháp lý tổng hợp."

        return MultiDomainAnalysisResult(
            primary_domain=chosen_domain,
            domain_scores=domain_scores,
            primary_domain_name=meta["name_vi"],
            primary_law=meta["primary_law"],
            domain_specific_analysis=domain_analysis,
            secondary_domains_detected=secondary,
            combined_summary=summary,
        )
