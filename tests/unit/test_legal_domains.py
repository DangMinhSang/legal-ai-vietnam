"""Unit tests cho hệ thống Đa Lĩnh vực Pháp luật & Hình phạt Điều 32 BLHS 2015.

Kiểm thử toàn diện:
1. Hệ thống 7 hình phạt chính & 7 hình phạt bổ sung (Điều 32 BLHS 2015).
2. Phân tích pháp luật hình sự & cá thể hóa hình phạt (Criminal Law).
3. Tranh chấp Dân sự & tính án phí, trần lãi suất 20% (Civil Law).
4. Tranh chấp Hành chính với cơ quan nhà nước & 2 kênh khiếu kiện (Administrative Law).
5. Tranh chấp Thương mại & kiểm soát trần phạt vi phạm 8%, VIAC (Commercial Law).
6. Kỷ luật Lao động & Cán bộ công chức (Disciplinary & Labor Law).
7. Bộ điều phối phân loại đa lĩnh vực (LegalDomainDispatcher).
8. Hàng rào kiểm tra tính nhất quán hình phạt (ConsistencyChecker).
"""

from __future__ import annotations

import pytest

from src.legal_domains.administrative import (
    AdministrativeActType,
    AdministrativeDisputeResolver,
    analyze_administrative_dispute,
)
from src.legal_domains.civil import (
    CivilDisputeResolver,
    CivilDisputeType,
    analyze_civil_dispute,
)
from src.legal_domains.commercial import (
    CommercialDisputeResolver,
    CommercialDisputeType,
    analyze_commercial_dispute,
)
from src.legal_domains.criminal import (
    CriminalPenaltySystem,
    PrincipalPenaltyType,
    SupplementaryPenaltyType,
    JudicialMeasureType,
    analyze_criminal_penalties,
)
from src.legal_domains.disciplinary import (
    CivilServantDisciplineMeasure,
    DisciplinaryResolver,
    LaborDisciplineMeasure,
    analyze_disciplinary_matter,
)
from src.legal_domains.dispatcher import (
    LegalDomain,
    LegalDomainDispatcher,
)
from src.validation.consistency_checker import ConsistencyChecker


# ============================================================================
# 1. TEST ĐIỀU 32 BLHS 2015: 7 HÌNH PHẠT CHÍNH & 7 HÌNH PHẠT BỔ SUNG
# ============================================================================

def test_article_32_principal_penalties():
    """Kiểm tra danh mục đầy đủ 7 hình phạt chính theo Điều 32 Khoản 1 BLHS 2015."""
    principals = CriminalPenaltySystem.get_all_principal_penalties()
    assert len(principals) == 7

    codes = [p["code"] for p in principals]
    expected_codes = [
        "canh_cao",
        "phat_tien",
        "cai_tao_khong_giam_giu",
        "truc_xuat",
        "tu_co_thoi_han",
        "tu_chung_than",
        "tu_hinh",
    ]
    assert codes == expected_codes

    # Kiểm tra từng hình phạt có tên và căn cứ điều luật
    for p in principals:
        assert p["name"]
        assert "Điều" in p["article"]
        assert "BLHS" in p["article"]


def test_article_32_supplementary_penalties():
    """Kiểm tra danh mục đầy đủ 7 hình phạt bổ sung theo Điều 32 Khoản 2 BLHS 2015."""
    supplements = CriminalPenaltySystem.get_all_supplementary_penalties()
    assert len(supplements) == 7

    codes = [s["code"] for s in supplements]
    expected_codes = [
        "cam_chuc_vu_hanh_nghe",
        "cam_cu_tru",
        "quan_che",
        "tuoc_quyen_cong_dan",
        "tich_thu_tai_san",
        "phat_tien_bo_sung",
        "truc_xuat_bo_sung",
    ]
    assert codes == expected_codes

    for s in supplements:
        assert s["name"]
        assert "Điều" in s["article"]


def test_criminal_penalty_suspended_sentence():
    """Kiểm tra điều kiện cho hưởng án treo theo Điều 65 BLHS (mức phạt tù <= 3 năm, nhân thân tốt)."""
    res = analyze_criminal_penalties(
        defendant_name="Nguyễn Văn A",
        crime_name="Cố ý gây thương tích",
        articles=["134"],
        clause=1,
        statutory_range=(0.5, 3.0),
        aggravating_count=0,
        mitigating_count=3,
        has_restitution=True,
        has_cooperation=True,
        is_first_offense=True,
        role_type="người giúp sức",
    )
    principal = res["principal_penalty"]
    assert principal["type"] == PrincipalPenaltyType.TU_CO_THOI_HAN.value
    assert principal["is_suspended"] is True
    assert "Án treo" in principal["name"]
    assert principal["sentence_years"] <= 3.0


def test_criminal_penalty_life_imprisonment():
    """Kiểm tra trường hợp đề xuất tù chung thân khi khung hình phạt rất nặng."""
    res = analyze_criminal_penalties(
        defendant_name="Trần Văn Hung",
        crime_name="Giết người",
        articles=["123"],
        clause=1,
        statutory_range=(12.0, 20.0),
        aggravating_count=3,
        mitigating_count=0,
        has_restitution=False,
        has_cooperation=False,
        is_first_offense=False,
        role_type="người chủ mưu",
    )
    principal = res["principal_penalty"]
    assert principal["type"] == PrincipalPenaltyType.TU_CHUNG_THAN.value
    assert "Tù chung thân" in principal["name"]


def test_criminal_supplementary_penalties_selection():
    """Kiểm tra áp dụng hình phạt bổ sung cho tội phạm kinh tế/chức vụ/làm giả."""
    res = analyze_criminal_penalties(
        defendant_name="Lê Văn H",
        crime_name="Làm giả con dấu, tài liệu của cơ quan, tổ chức",
        articles=["341"],
        clause=2,
        statutory_range=(2.0, 5.0),
        aggravating_count=1,
        mitigating_count=1,
        illicit_profits_vnd=5_000_000,
    )
    sup_types = [s["type"] for s in res["supplementary_penalties"]]
    assert SupplementaryPenaltyType.CAM_CHUC_VU_HANH_NGHE.value in sup_types
    assert SupplementaryPenaltyType.PHAT_TIEN_BO_SUNG.value in sup_types

    # Biện pháp tư pháp: Tịch thu tài sản/tiền thu lợi bất chính
    jud_types = [j["type"] for j in res["judicial_measures"]]
    assert JudicialMeasureType.TICH_THU_VAT_TIEN.value in jud_types


# ============================================================================
# 2. TEST DÂN SỰ (CIVIL LAW & COURT FEES)
# ============================================================================

def test_civil_court_fee_calculation():
    """Kiểm tra bảng tính án phí dân sự sơ thẩm có giá ngạch theo Nghị quyết 326/2016/UBTVQH14."""
    calc = CivilDisputeResolver.calculate_civil_court_fee

    # Dưới 6 triệu -> 300.000 VNĐ
    assert calc(5_000_000) == 300_000

    # 100 triệu (từ 6M đến 400M: 5%) -> 5.000.000 VNĐ
    assert calc(100_000_000) == 5_000_000

    # 500 triệu (từ 400M đến 800M: 20M + 4% phần vượt 400M) -> 20M + 4M = 24.000.000 VNĐ
    assert calc(500_000_000) == 24_000_000

    # 1 tỷ (từ 800M đến 2 tỷ: 36M + 3% phần vượt 800M) -> 36M + 6M = 42.000.000 VNĐ
    assert calc(1_000_000_000) == 42_000_000

    # 3 tỷ (từ 2 tỷ đến 4 tỷ: 72M + 2% phần vượt 2 tỷ) -> 72M + 20M = 92.000.000 VNĐ
    assert calc(3_000_000_000) == 92_000_000

    # 5 tỷ (trên 4 tỷ: 112M + 0.1% phần vượt 4 tỷ) -> 112M + 1M = 113.000.000 VNĐ
    assert calc(5_000_000_000) == 113_000_000


def test_civil_loan_interest_rate_cap():
    """Kiểm tra phân tích hợp đồng vay và kiểm soát trần lãi suất 20%/năm (Điều 468 BLDS)."""
    text_normal = "Ông A cho ông B vay số tiền 500.000.000 đồng, lãi suất thỏa thuận 12%/năm. Đến hạn ông B không trả."
    res_normal = analyze_civil_dispute(text_normal)
    assert res_normal["dispute_type"] == CivilDisputeType.CONTRACT_LOAN.value
    assert res_normal["claim_amount_vnd"] == 500_000_000
    assert len(res_normal["risk_warnings"]) == 0

    text_excessive = "Bà C vay tiền với lãi suất 35%/năm theo giấy vay nợ. Nay bên cho vay yêu cầu trả nợ gốc và lãi."
    res_excessive = analyze_civil_dispute(text_excessive)
    assert any("20%/năm" in w for w in res_excessive["risk_warnings"])


def test_civil_inheritance_analysis():
    """Kiểm tra phân tích tranh chấp thừa kế di sản (Điều 609 - 623 BLDS)."""
    text = "Cha mẹ mất để lại di sản nhà đất chưa có di chúc. Các con yêu cầu chia thừa kế theo pháp luật."
    res = analyze_civil_dispute(text)
    assert res["dispute_type"] == CivilDisputeType.INHERITANCE.value
    assert "30 năm" in res["statute_of_limitations_note"]


# ============================================================================
# 3. TEST HÀNH CHÍNH & TRANH CHẤP VỚI CƠ QUAN NHÀ NƯỚC (ADMINISTRATIVE LAW)
# ============================================================================

def test_administrative_land_recovery_dispute():
    """Kiểm tra tranh chấp quyết định thu hồi đất của UBND và chiến lược 2 kênh."""
    text = "UBND Quận X ban hành quyết định thu hồi đất và cưỡng chế thu hồi đất bồi thường giá thấp trái quy định đối với hộ gia đình ông K."
    res = analyze_administrative_dispute(text)
    assert res["dispute_type"] == AdministrativeActType.ADMIN_DECISION_LAND.value
    assert "UBND" in res["state_agency_named"]
    assert "90 ngày" in res["time_limit_complaint"]
    assert "01 năm" in res["time_limit_court"]
    assert any("biện pháp khẩn cấp tạm thời" in m.lower() for m in res["urgent_temporary_measures"])


def test_administrative_penalty_decision():
    """Kiểm tra khiếu kiện quyết định xử phạt vi phạm hành chính (VPHC)."""
    text = "Chủ tịch UBND tỉnh ban hành quyết định xử phạt vi phạm hành chính số tiền 80.000.000 đồng và tịch thu phương tiện."
    res = analyze_administrative_dispute(text)
    assert res["dispute_type"] == AdministrativeActType.ADMIN_DECISION_PENALTY.value
    assert len(res["action_steps"]) >= 4


# ============================================================================
# 4. TEST THƯƠNG MẠI & TRỌNG TÀI (COMMERCIAL LAW & VIAC)
# ============================================================================

def test_commercial_penalty_ceiling_8_percent():
    """Kiểm tra giới hạn phạt vi phạm 8% theo Điều 301 Luật Thương mại 2005."""
    text = (
        "Công ty A và Công ty B ký hợp đồng mua bán thiết bị trị giá 2.000.000.000 đồng. "
        "Bên B chậm giao hàng. Bên A yêu cầu phạt vi phạm hợp đồng 15% tương đương 300.000.000 đồng."
    )
    res = analyze_commercial_dispute(text)
    assert res["contract_value_vnd"] == 2_000_000_000
    assert res["penalty_claim_vnd"] == 300_000_000
    # Trần 8% của 2 tỷ là 160.000.000
    assert res["max_legal_penalty_vnd"] == 160_000_000
    assert any("vượt quá" in w and "8%" in w for w in res["risk_warnings"])


def test_commercial_arbitration_viac_clause():
    """Kiểm tra thỏa thuận trọng tài VIAC loại trừ thẩm quyền Tòa án (Điều 6 Luật TTTM 2010)."""
    text = "Hợp đồng thương mại quốc tế quy định: Mọi tranh chấp phát sinh sẽ được giải quyết tại Trung tâm Trọng tài Quốc tế Việt Nam (VIAC)."
    res = analyze_commercial_dispute(text)
    assert res["arbitration_clause_found"] is True
    assert "VIAC" in res["forum_recommendation"]


# ============================================================================
# 5. TEST KỶ LUẬT & LAO ĐỘNG (LABOR & DISCIPLINARY LAW)
# ============================================================================

def test_labor_illegal_dismissal_maternity():
    """Kiểm tra xử lý kỷ luật sa thải trái pháp luật đối với lao động nữ mang thai/nuôi con nhỏ (Điều 137 BLLĐ)."""
    text = "Công ty Cổ phần M ra quyết định sa thải chị Nguyễn Thị H với lý do nghỉ việc không báo trước, trong khi chị H đang mang thai tháng thứ 5."
    res = analyze_disciplinary_matter(text)
    assert res["is_discipline_valid"] is False
    assert any("mang thai" in v for v in res["procedural_violations"])
    assert "Điều 41" in str(res["compensation_entitlement"])


def test_labor_illegal_wage_fine():
    """Kiểm tra hành vi phạt tiền, cắt lương vi phạm Điều 127 BLLĐ 2019."""
    text = "Do người lao động làm hỏng sản phẩm, Giám đốc ra quyết định trừ 50% lương tháng để phạt vi phạm kỷ luật."
    res = analyze_disciplinary_matter(text)
    assert res["is_discipline_valid"] is False
    assert any("phạt tiền, cắt lương" in v for v in res["procedural_violations"])


# ============================================================================
# 6. TEST BỘ ĐIỀU PHỐI ĐA LĨNH VỰC (LEGAL DOMAIN DISPATCHER)
# ============================================================================

def test_dispatcher_classification_accuracy():
    """Kiểm tra khả năng phân loại tự động chính xác 5 lĩnh vực pháp luật."""
    # 1. Hình sự
    res_crim = LegalDomainDispatcher.dispatch("Bị cáo Nguyễn Văn A bị Viện kiểm sát truy tố về tội cướp tài sản theo Điều 168 BLHS.")
    assert res_crim.primary_domain == LegalDomain.CRIMINAL

    # 2. Dân sự
    res_civ = LegalDomainDispatcher.dispatch("Tranh chấp giấy vay nợ 500 triệu đồng và chia di chúc thừa kế nhà đất giữa các đồng thừa kế.")
    assert res_civ.primary_domain == LegalDomain.CIVIL

    # 3. Hành chính
    res_adm = LegalDomainDispatcher.dispatch("Khiếu kiện quyết định thu hồi đất và cưỡng chế giải phóng mặt bằng của Chủ tịch UBND quận.")
    assert res_adm.primary_domain == LegalDomain.ADMINISTRATIVE

    # 4. Thương mại
    res_com = LegalDomainDispatcher.dispatch("Tranh chấp hợp đồng kinh tế giữa hai thương nhân, phạt vi phạm giao hàng chậm và khởi kiện tại VIAC.")
    assert res_com.primary_domain == LegalDomain.COMMERCIAL

    # 5. Kỷ luật
    res_disc = LegalDomainDispatcher.dispatch("Người sử dụng lao động ra quyết định sa thải trái pháp luật, vi phạm nội quy lao động và thỏa ước.")
    assert res_disc.primary_domain == LegalDomain.DISCIPLINARY


def test_dispatcher_forced_domain():
    """Kiểm tra cơ chế chỉ định cưỡng bức lĩnh vực (forced_domain)."""
    text = "Hợp đồng chuyển nhượng quyền sử dụng đất."
    res = LegalDomainDispatcher.dispatch(text, forced_domain="civil")
    assert res.primary_domain == LegalDomain.CIVIL


# ============================================================================
# 7. TEST KIỂM TRA TÍNH NHẤT QUÁN HÌNH PHẠT (CONSISTENCY CHECKER)
# ============================================================================

def test_consistency_penalties_duplicate_fine():
    """Kiểm tra cấm phạt tiền vừa là hình phạt chính vừa là hình phạt bổ sung (Điều 32 Khoản 2)."""
    checker = ConsistencyChecker()
    warnings = checker.validate_penalties_consistency(
        principal_penalty_code="phat_tien",
        supplementary_penalty_codes=["phat_tien_bo_sung"],
    )
    assert any("Điều 32 Khoản 2 Điểm e" in w for w in warnings)


def test_consistency_penalties_death_penalty_exceptions():
    """Kiểm tra điều cấm áp dụng tử hình theo Điều 40 BLHS 2015."""
    checker = ConsistencyChecker()

    # Dưới 18 tuổi
    w_minor = checker.validate_penalties_consistency(
        principal_penalty_code="tu_hinh",
        supplementary_penalty_codes=[],
        age=17,
    )
    assert any("dưới 18 tuổi" in w for w in w_minor)

    # Phụ nữ có thai hoặc nuôi con nhỏ < 36 tháng
    w_pregnant = checker.validate_penalties_consistency(
        principal_penalty_code="tu_hinh",
        supplementary_penalty_codes=[],
        age=25,
        is_pregnant_or_nursing=True,
    )
    assert any("phụ nữ có thai" in w for w in w_pregnant)

    # Người từ 75 tuổi trở lên
    w_elderly = checker.validate_penalties_consistency(
        principal_penalty_code="tu_hinh",
        supplementary_penalty_codes=[],
        age=76,
    )
    assert any("75 tuổi trở lên" in w for w in w_elderly)


def test_consistency_penalties_suspended_sentence_cap():
    """Kiểm tra án treo không được vượt quá 3 năm tù (Điều 65 BLHS)."""
    checker = ConsistencyChecker()
    warnings = checker.validate_penalties_consistency(
        principal_penalty_code="tu_co_thoi_han",
        supplementary_penalty_codes=[],
        sentence_years=4.5,
        is_suspended=True,
    )
    assert any("không quá 03 năm" in w for w in warnings)
