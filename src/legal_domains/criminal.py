"""Module quản lý và phân tích hệ thống hình phạt hình sự theo Bộ luật Hình sự 2015 (sửa đổi, bổ sung 2017).

Tuân thủ nghiêm ngặt:
A. 7 HÌNH PHẠT CHÍNH (Khoản 1 Điều 32 BLHS):
   1. Cảnh cáo (Điều 34)
   2. Phạt tiền (Điều 35)
   3. Cải tạo không giam giữ (Điều 36)
   4. Trục xuất (Điều 37)
   5. Tù có thời hạn (Điều 38)
   6. Tù chung thân (Điều 39)
   7. Tử hình (Điều 40)

B. 7 HÌNH PHẠT BỔ SUNG (Khoản 2 Điều 32 BLHS):
   1. Cấm đảm nhiệm chức vụ, cấm hành nghề hoặc làm công việc nhất định (Điều 41)
   2. Cấm cư trú (Điều 42)
   3. Quản chế (Điều 43)
   4. Tước một số quyền công dân (Điều 44)
   5. Tịch thu tài sản (Điều 45)
   6. Phạt tiền, khi không áp dụng là hình phạt chính (Điều 35)
   7. Trục xuất, khi không áp dụng là hình phạt chính (Điều 37)

C. BIỆN PHÁP TƯ PHÁP (Điều 46 BLHS):
   1. Tịch thu vật, tiền trực tiếp liên quan đến tội phạm (Điều 47)
   2. Trả lại tài sản, sửa chữa hoặc bồi thường thiệt hại; buộc công khai xin lỗi (Điều 48)
   3. Bắt buộc chữa bệnh (Điều 49)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PrincipalPenaltyType(str, Enum):
    """7 Hình phạt chính theo Khoản 1 Điều 32 Bộ luật Hình sự 2015."""

    CANH_CAO = "canh_cao"  # 1. Cảnh cáo (Điều 34)
    PHAT_TIEN = "phat_tien"  # 2. Phạt tiền (Điều 35)
    CAI_TAO_KHONG_GIAM_GIU = "cai_tao_khong_giam_giu"  # 3. Cải tạo không giam giữ (Điều 36)
    TRUC_XUAT = "truc_xuat"  # 4. Trục xuất (Điều 37)
    TU_CO_THOI_HAN = "tu_co_thoi_han"  # 5. Tù có thời hạn (Điều 38)
    TU_CHUNG_THAN = "tu_chung_than"  # 6. Tù chung thân (Điều 39)
    TU_HINH = "tu_hinh"  # 7. Tử hình (Điều 40)


class SupplementaryPenaltyType(str, Enum):
    """7 Hình phạt bổ sung theo Khoản 2 Điều 32 Bộ luật Hình sự 2015."""

    CAM_CHUC_VU_HANH_NGHE = "cam_chuc_vu_hanh_nghe"  # 1. Cấm đảm nhiệm chức vụ, cấm hành nghề (Điều 41)
    CAM_CU_TRU = "cam_cu_tru"  # 2. Cấm cư trú (Điều 42)
    QUAN_CHE = "quan_che"  # 3. Quản chế (Điều 43)
    TUOC_QUYEN_CONG_DAN = "tuoc_quyen_cong_dan"  # 4. Tước một số quyền công dân (Điều 44)
    TICH_THU_TAI_SAN = "tich_thu_tai_san"  # 5. Tịch thu tài sản (Điều 45)
    PHAT_TIEN_BO_SUNG = "phat_tien_bo_sung"  # 6. Phạt tiền khi không áp dụng là hình phạt chính
    TRUC_XUAT_BO_SUNG = "truc_xuat_bo_sung"  # 7. Trục xuất khi không áp dụng là hình phạt chính


class JudicialMeasureType(str, Enum):
    """Các biện pháp tư pháp theo Điều 46 Bộ luật Hình sự 2015."""

    TICH_THU_VAT_TIEN = "tich_thu_vat_tien"  # Điều 47: Tịch thu vật, tiền trực tiếp liên quan tội phạm
    TRA_LAI_BOI_THUONG = "tra_lai_boi_thuong"  # Điều 48: Trả lại tài sản, bồi thường thiệt hại
    BAT_BUOC_CHUA_BENH = "bat_buoc_chua_benh"  # Điều 49: Bắt buộc chữa bệnh


@dataclass
class PenaltyRuleDetail:
    """Chi tiết quy định của một loại hình phạt."""

    code: str
    name_vi: str
    article: str
    description: str
    min_value: float = 0.0
    max_value: float = 0.0
    unit: str = ""
    conditions: str = ""


# Bảng định nghĩa chi tiết 7 hình phạt chính theo BLHS 2015
PRINCIPAL_PENALTY_REGISTRY: dict[PrincipalPenaltyType, PenaltyRuleDetail] = {
    PrincipalPenaltyType.CANH_CAO: PenaltyRuleDetail(
        code=PrincipalPenaltyType.CANH_CAO.value,
        name_vi="1. Cảnh cáo",
        article="Điều 34 BLHS 2015",
        description="Áp dụng đối với người phạm tội ít nghiêm trọng và có nhiều tình tiết giảm nhẹ, nhưng chưa đến mức miễn hình phạt.",
        conditions="Tội phạm ít nghiêm trọng, có nhiều tình tiết giảm nhẹ.",
    ),
    PrincipalPenaltyType.PHAT_TIEN: PenaltyRuleDetail(
        code=PrincipalPenaltyType.PHAT_TIEN.value,
        name_vi="2. Phạt tiền",
        article="Điều 35 BLHS 2015",
        description="Áp dụng là hình phạt chính đối với tội ít nghiêm trọng, tội nghiêm trọng do BLHS quy định; hoặc tội rất nghiêm trọng xâm phạm trật tự quản lý kinh tế, môi trường...",
        min_value=4_000_000,
        max_value=5_000_000_000,
        unit="VNĐ",
        conditions="Căn cứ vào tính chất mức độ nghiêm trọng và tình hình tài sản của người phạm tội.",
    ),
    PrincipalPenaltyType.CAI_TAO_KHONG_GIAM_GIU: PenaltyRuleDetail(
        code=PrincipalPenaltyType.CAI_TAO_KHONG_GIAM_GIU.value,
        name_vi="3. Cải tạo không giam giữ",
        article="Điều 36 BLHS 2015",
        description="Áp dụng từ 06 tháng đến 03 năm đối với người phạm tội ít nghiêm trọng, tội nghiêm trọng mà có nơi làm việc ổn định hoặc nơi cư trú rõ ràng.",
        min_value=0.5,
        max_value=3.0,
        unit="năm",
        conditions="Tội ít nghiêm trọng/nghiêm trọng, nơi cư trú rõ ràng hoặc việc làm ổn định, khấu trừ thu nhập 5-20%.",
    ),
    PrincipalPenaltyType.TRUC_XUAT: PenaltyRuleDetail(
        code=PrincipalPenaltyType.TRUC_XUAT.value,
        name_vi="4. Trục xuất",
        article="Điều 37 BLHS 2015",
        description="Buộc người nước ngoài bị kết án phải rời khỏi lãnh thổ nước Cộng hòa xã hội chủ nghĩa Việt Nam.",
        conditions="Chỉ áp dụng đối với người phạm tội mang quốc tịch nước ngoài hoặc người không quốc tịch.",
    ),
    PrincipalPenaltyType.TU_CO_THOI_HAN: PenaltyRuleDetail(
        code=PrincipalPenaltyType.TU_CO_THOI_HAN.value,
        name_vi="5. Tù có thời hạn",
        article="Điều 38 BLHS 2015",
        description="Buộc người bị kết án phải chấp hành hình phạt tại cơ sở giam giữ trong một thời hạn nhất định từ 03 tháng đến 20 năm.",
        min_value=0.25,
        max_value=20.0,
        unit="năm",
        conditions="Không áp dụng đối với người lần đầu phạm tội ít nghiêm trọng do vô ý và có nơi cư trú rõ ràng.",
    ),
    PrincipalPenaltyType.TU_CHUNG_THAN: PenaltyRuleDetail(
        code=PrincipalPenaltyType.TU_CHUNG_THAN.value,
        name_vi="6. Tù chung thân",
        article="Điều 39 BLHS 2015",
        description="Hình phạt tù không thời hạn được áp dụng đối với người phạm tội đặc biệt nghiêm trọng, nhưng chưa đến mức bị xử phạt tử hình.",
        conditions="Không áp dụng đối với người dưới 18 tuổi phạm tội.",
    ),
    PrincipalPenaltyType.TU_HINH: PenaltyRuleDetail(
        code=PrincipalPenaltyType.TU_HINH.value,
        name_vi="7. Tử hình",
        article="Điều 40 BLHS 2015",
        description="Hình phạt đặc biệt chỉ áp dụng đối với người phạm tội đặc biệt nghiêm trọng thuộc một trong các nhóm tội xâm phạm an ninh quốc gia, tính mạng con người...",
        conditions="Tuyệt đối không áp dụng đối với: Người dưới 18 tuổi; Phụ nữ có thai; Phụ nữ nuôi con dưới 36 tháng tuổi; Người đủ 75 tuổi trở lên khi phạm tội hoặc khi xét xử.",
    ),
}

# Bảng định nghĩa chi tiết 7 hình phạt bổ sung theo BLHS 2015
SUPPLEMENTARY_PENALTY_REGISTRY: dict[SupplementaryPenaltyType, PenaltyRuleDetail] = {
    SupplementaryPenaltyType.CAM_CHUC_VU_HANH_NGHE: PenaltyRuleDetail(
        code=SupplementaryPenaltyType.CAM_CHUC_VU_HANH_NGHE.value,
        name_vi="1. Cấm đảm nhiệm chức vụ, cấm hành nghề hoặc làm công việc nhất định",
        article="Điều 41 BLHS 2015",
        description="Áp dụng khi xét thấy nếu để người bị kết án đảm nhiệm chức vụ, hành nghề hoặc làm công việc đó thì có thể gây nguy hại cho xã hội. Thời hạn từ 01 năm đến 05 năm.",
        min_value=1.0,
        max_value=5.0,
        unit="năm",
        conditions="Tính từ ngày chấp hành xong hình phạt tù hoặc từ ngày bản án có hiệu lực pháp luật.",
    ),
    SupplementaryPenaltyType.CAM_CU_TRU: PenaltyRuleDetail(
        code=SupplementaryPenaltyType.CAM_CU_TRU.value,
        name_vi="2. Cấm cư trú",
        article="Điều 42 BLHS 2015",
        description="Buộc người bị kết án phạt tù không được tạm trú hoặc thường trú ở một số địa phương nhất định. Thời hạn từ 01 năm đến 05 năm.",
        min_value=1.0,
        max_value=5.0,
        unit="năm",
        conditions="Tính từ ngày chấp hành xong hình phạt tù.",
    ),
    SupplementaryPenaltyType.QUAN_CHE: PenaltyRuleDetail(
        code=SupplementaryPenaltyType.QUAN_CHE.value,
        name_vi="3. Quản chế",
        article="Điều 43 BLHS 2015",
        description="Buộc người bị kết án phạt tù phải cư trú, làm ăn sinh sống và cải tạo ở một địa phương nhất định dưới sự kiểm soát, giáo dục của chính quyền. Thời hạn từ 01 năm đến 05 năm.",
        min_value=1.0,
        max_value=5.0,
        unit="năm",
        conditions="Chỉ áp dụng đối với tội xâm phạm an ninh quốc gia, tái phạm nguy hiểm hoặc tội phạm khác do BLHS quy định.",
    ),
    SupplementaryPenaltyType.TUOC_QUYEN_CONG_DAN: PenaltyRuleDetail(
        code=SupplementaryPenaltyType.TUOC_QUYEN_CONG_DAN.value,
        name_vi="4. Tước một số quyền công dân",
        article="Điều 44 BLHS 2015",
        description="Công dân Việt Nam bị kết án phạt tù về tội xâm phạm an ninh quốc gia hoặc tội phạm khác thì có thể bị tước quyền ứng cử, quyền bầu cử, quyền làm việc trong cơ quan nhà nước. Thời hạn từ 01 năm đến 05 năm.",
        min_value=1.0,
        max_value=5.0,
        unit="năm",
    ),
    SupplementaryPenaltyType.TICH_THU_TAI_SAN: PenaltyRuleDetail(
        code=SupplementaryPenaltyType.TICH_THU_TAI_SAN.value,
        name_vi="5. Tịch thu tài sản",
        article="Điều 45 BLHS 2015",
        description="Tước một phần hoặc toàn bộ tài sản thuộc sở hữu của người bị kết án để nộp vào ngân sách nhà nước. Chỉ áp dụng đối với người bị kết án về tội nghiêm trọng, rất nghiêm trọng hoặc đặc biệt nghiêm trọng.",
        conditions="Vẫn phải để lại cho người bị kết án và gia đình họ có điều kiện sinh sống.",
    ),
    SupplementaryPenaltyType.PHAT_TIEN_BO_SUNG: PenaltyRuleDetail(
        code=SupplementaryPenaltyType.PHAT_TIEN_BO_SUNG.value,
        name_vi="6. Phạt tiền (khi không áp dụng là hình phạt chính)",
        article="Điều 35 BLHS 2015",
        description="Áp dụng là hình phạt bổ sung đối với người phạm tội khi điều luật có quy định nhưng hình phạt chính đã là tù, cảnh cáo hoặc cải tạo không giam giữ.",
        min_value=1_000_000,
        max_value=500_000_000,
        unit="VNĐ",
    ),
    SupplementaryPenaltyType.TRUC_XUAT_BO_SUNG: PenaltyRuleDetail(
        code=SupplementaryPenaltyType.TRUC_XUAT_BO_SUNG.value,
        name_vi="7. Trục xuất (khi không áp dụng là hình phạt chính)",
        article="Điều 37 BLHS 2015",
        description="Áp dụng là hình phạt bổ sung đối với người nước ngoài phạm tội khi hình phạt chính là hình phạt tù hoặc hình phạt khác.",
    ),
}


@dataclass
class CriminalSentencingAnalysis:
    """Kết quả phân tích hình phạt toàn diện cho một vụ án hình sự."""

    defendant_name: str
    crime_name: str
    articles: list[str]
    clause: str
    is_guilty: bool = True
    # A. Hình phạt chính đề xuất
    principal_penalty: PrincipalPenaltyType = PrincipalPenaltyType.TU_CO_THOI_HAN
    principal_penalty_name: str = "Tù có thời hạn (Điều 38 BLHS)"
    sentence_duration_years: float = 2.0
    sentence_formatted: str = "02 năm tù"
    is_suspended_sentence: bool = False  # Án treo (Điều 65 BLHS)
    probation_years: float = 0.0  # Thời gian thử thách án treo
    # B. Danh sách hình phạt bổ sung đề xuất
    supplementary_penalties: list[dict[str, Any]] = field(default_factory=list)
    # C. Biện pháp tư pháp đề xuất
    judicial_measures: list[dict[str, Any]] = field(default_factory=list)
    # D. Căn cứ và lập luận pháp lý
    legal_rationale: str = ""
    prohibitions_applied: list[str] = field(default_factory=list)


class CriminalPenaltySystem:
    """Hệ thống động cơ phân tích và áp dụng hình phạt theo Điều 32 BLHS 2015."""

    @staticmethod
    def get_all_principal_penalties() -> list[dict[str, Any]]:
        """Trả về danh sách chuẩn 7 hình phạt chính."""
        return [
            {
                "id": p.code,
                "code": p.code,
                "name": p.name_vi,
                "article": p.article,
                "description": p.description,
                "conditions": p.conditions,
            }
            for p in PRINCIPAL_PENALTY_REGISTRY.values()
        ]

    @staticmethod
    def get_all_supplementary_penalties() -> list[dict[str, Any]]:
        """Trả về danh sách chuẩn 7 hình phạt bổ sung."""
        return [
            {
                "id": p.code,
                "code": p.code,
                "name": p.name_vi,
                "article": p.article,
                "description": p.description,
                "conditions": p.conditions,
            }
            for p in SUPPLEMENTARY_PENALTY_REGISTRY.values()
        ]

    @staticmethod
    def evaluate_penalties(
        defendant_name: str,
        crime_name: str,
        articles: list[str],
        clause: str = "1",
        age: int = 25,
        is_pregnant_or_nursing: bool = False,
        is_foreigner: bool = False,
        statutory_range: tuple[float, float] = (1.0, 5.0),
        aggravating_count: int = 0,
        mitigating_count: int = 0,
        has_restitution: bool = False,
        has_cooperation: bool = False,
        is_first_offense: bool = True,
        role_type: str = "thực hành",
        illicit_profits_vnd: float = 0.0,
    ) -> CriminalSentencingAnalysis:
        """Đánh giá và cá thể hóa hình phạt toàn diện cho bị cáo."""
        prohibitions: list[str] = []
        sup_penalties: list[dict[str, Any]] = []
        judicial_measures: list[dict[str, Any]] = []

        min_bound, max_bound = statutory_range

        # 1. Kiểm tra các điều cấm tuyệt đối theo luật định
        # Điều 40: Không áp dụng tử hình với người dưới 18 tuổi, phụ nữ có thai/nuôi con nhỏ, người đủ 75 tuổi
        can_apply_capital = True
        can_apply_life = True
        if age < 18:
            can_apply_capital = False
            can_apply_life = False
            prohibitions.append(
                f"Bị cáo {defendant_name} dưới 18 tuổi ({age} tuổi): Tuyệt đối KHÔNG áp dụng Tù chung thân và Tử hình (Điều 98, 99, 100, 101 BLHS)."
            )
        elif is_pregnant_or_nursing:
            can_apply_capital = False
            prohibitions.append(
                f"Bị cáo {defendant_name} đang có thai hoặc nuôi con dưới 36 tháng tuổi: Tuyệt đối KHÔNG áp dụng hình phạt Tử hình (Khoản 2 Điều 40 BLHS)."
            )
        elif age >= 75:
            can_apply_capital = False
            prohibitions.append(
                f"Bị cáo {defendant_name} từ đủ 75 tuổi trở lên: Không áp dụng hình phạt Tử hình (Khoản 2 Điều 40 BLHS)."
            )

        # 2. Xác định Hình phạt chính (Principal Penalty)
        principal_type = PrincipalPenaltyType.TU_CO_THOI_HAN
        principal_name = "5. Tù có thời hạn (Điều 38 BLHS)"
        sentence_years = 0.0
        is_suspended = False
        probation_years = 0.0
        sentence_text = ""

        # Tính toán mức án cơ sở trong khung
        mid_bound = (min_bound + max_bound) / 2.0
        calculated_years = mid_bound + 0.5 * aggravating_count - 0.5 * mitigating_count
        calculated_years = max(min_bound, min(max_bound, calculated_years))

        # Áp dụng Điều 54: Nếu có ít nhất 02 tình tiết giảm nhẹ Khoản 1 Điều 51 và không có tăng nặng
        can_apply_art_54 = (mitigating_count >= 2) and (aggravating_count == 0)
        if can_apply_art_54:
            calculated_years = max(0.5, min_bound * 0.6)  # Quyết định hình phạt dưới mức thấp nhất của khung

        # Phân tích điều kiện Tử hình (Điều 40), Tù chung thân (Điều 39) hoặc Án treo (Điều 65 BLHS)
        if max_bound >= 20.0 and aggravating_count >= 4 and can_apply_capital:
            principal_type = PrincipalPenaltyType.TU_HINH
            principal_name = "7. Tử hình (Điều 40 BLHS)"
            sentence_years = 30.0
            sentence_text = "Tử hình (Điều 40 BLHS)"
        elif max_bound >= 20.0 and aggravating_count >= 3 and can_apply_life:
            principal_type = PrincipalPenaltyType.TU_CHUNG_THAN
            principal_name = "6. Tù chung thân (Điều 39 BLHS)"
            sentence_years = 20.0
            sentence_text = "Tù chung thân (Điều 39 BLHS)"
        elif calculated_years <= 3.0 and is_first_offense and mitigating_count >= 2 and (aggravating_count <= 1):
            is_suspended = True
            sentence_years = round(calculated_years, 1)
            probation_years = min(5.0, max(1.0, sentence_years * 2.0))
            principal_name = "5. Tù có thời hạn (Điều 38 BLHS) - Cho hưởng Án treo (Điều 65 BLHS)"
            sentence_text = f"{sentence_years} năm tù (Cho hưởng Án treo, thời gian thử thách {probation_years} năm)"
        elif max_bound <= 3.0 and mitigating_count >= 3 and is_first_offense and not aggravating_count:
            # Xem xét Cải tạo không giam giữ (Điều 36)
            principal_type = PrincipalPenaltyType.CAI_TAO_KHONG_GIAM_GIU
            principal_name = "3. Cải tạo không giam giữ (Điều 36 BLHS)"
            sentence_years = round(min(3.0, calculated_years), 1)
            sentence_text = f"{sentence_years} năm cải tạo không giam giữ"
        else:
            principal_type = PrincipalPenaltyType.TU_CO_THOI_HAN
            sentence_years = round(calculated_years, 1)
            sentence_text = f"{sentence_years} năm tù giam"

        # Nếu người nước ngoài phạm tội đặc biệt có thể xem xét Trục xuất là hình phạt chính
        if is_foreigner and calculated_years <= 2.0:
            principal_type = PrincipalPenaltyType.TRUC_XUAT
            principal_name = "4. Trục xuất (Điều 37 BLHS)"
            sentence_text = "Trục xuất khỏi lãnh thổ Việt Nam"

        # 3. Xác định Hình phạt bổ sung (Supplementary Penalties - Điều 32 Khoản 2)
        # Điều 41: Cấm đảm nhiệm chức vụ, hành nghề
        if any(kw in crime_name.lower() for kw in ["chức vụ", "tham nhũng", "làm giả", "nghề", "kinh doanh"]):
            sup_penalties.append({
                "type": SupplementaryPenaltyType.CAM_CHUC_VU_HANH_NGHE.value,
                "name": "1. Cấm đảm nhiệm chức vụ, cấm hành nghề hoặc làm công việc nhất định (Điều 41 BLHS)",
                "duration": "02 đến 03 năm",
                "reason": "Ngăn ngừa việc lợi dụng nghề nghiệp, chức vụ tiếp tục thực hiện hành vi vi phạm pháp luật.",
            })

        # Điều 35 Khoản 2: Phạt tiền bổ sung (khi không áp dụng là hình phạt chính)
        if principal_type != PrincipalPenaltyType.PHAT_TIEN:
            if illicit_profits_vnd > 0 or any(kw in crime_name.lower() for kw in ["kinh tế", "làm giả", "chiếm đoạt", "ma túy"]):
                fine_sug = max(5_000_000, min(50_000_000, illicit_profits_vnd * 2)) if illicit_profits_vnd > 0 else 10_000_000
                sup_penalties.append({
                    "type": SupplementaryPenaltyType.PHAT_TIEN_BO_SUNG.value,
                    "name": "6. Phạt tiền bổ sung (Điều 35 & Điều 32 Khoản 2 BLHS)",
                    "amount_vnd": fine_sug,
                    "formatted": f"{fine_sug:,.0f} VNĐ",
                    "reason": "Phạt tiền bổ sung nhằm tước đoạt lợi ích kinh tế phát sinh từ hành vi phạm tội.",
                })

        # Điều 42/43: Quản chế hoặc Cấm cư trú đối với tội nghiêm trọng/tái phạm
        if aggravating_count >= 2:
            sup_penalties.append({
                "type": SupplementaryPenaltyType.QUAN_CHE.value,
                "name": "3. Quản chế (Điều 43 BLHS)",
                "duration": "01 năm đến 02 năm",
                "reason": "Áp dụng sau khi chấp hành xong án tù để quản lý đối tượng có nguy cơ tái phạm.",
            })

        # Điều 37 Khoản 2: Trục xuất bổ sung nếu là người nước ngoài
        if is_foreigner and principal_type != PrincipalPenaltyType.TRUC_XUAT:
            sup_penalties.append({
                "type": SupplementaryPenaltyType.TRUC_XUAT_BO_SUNG.value,
                "name": "7. Trục xuất bổ sung (Điều 37 & Điều 32 Khoản 2 BLHS)",
                "reason": "Trục xuất người nước ngoài sau khi chấp hành xong hình phạt chính tại Việt Nam.",
            })

        # 4. Xác định Biện pháp tư pháp (Điều 46, 47, 48 BLHS)
        if illicit_profits_vnd > 0:
            judicial_measures.append({
                "type": JudicialMeasureType.TICH_THU_VAT_TIEN.value,
                "name": "Tịch thu số tiền thu lợi bất chính sung vào ngân sách nhà nước (Điều 47 BLHS)",
                "value_vnd": illicit_profits_vnd,
                "formatted": f"{illicit_profits_vnd:,.0f} VNĐ",
            })

        if has_restitution:
            judicial_measures.append({
                "type": JudicialMeasureType.TRA_LAI_BOI_THUONG.value,
                "name": "Ghi nhận việc tự nguyện bồi thường thiệt hại, khắc phục hậu quả (Điều 48 BLHS)",
                "details": "Bị cáo đã khắc phục xong hậu quả hoặc hoàn trả tài sản cho người bị hại / nhà nước.",
            })

        # 5. Xây dựng lập luận pháp lý
        rationale = (
            f"Căn cứ Điều 32, Điều 50 BLHS 2015 về nguyên tắc quyết định hình phạt: "
            f"Bị cáo {defendant_name} phạm {crime_name}. "
            f"Về tình tiết tăng nặng: {aggravating_count} tình tiết (Điều 52). "
            f"Về tình tiết giảm nhẹ: {mitigating_count} tình tiết (Điều 51). "
        )
        if can_apply_art_54:
            rationale += "Áp dụng Điều 54 BLHS quyết định mức hình phạt dưới mức thấp nhất của khung luật định. "
        if is_suspended:
            rationale += f"Đủ điều kiện cho hưởng Án treo theo Điều 65 BLHS (mức án {sentence_years} năm <= 3 năm, nhân thân tốt, nhiều tình tiết giảm nhẹ). "
        else:
            rationale += f"Mức án {sentence_text} tương xứng với tính chất, mức độ nguy hiểm của hành vi. "

        return CriminalSentencingAnalysis(
            defendant_name=defendant_name,
            crime_name=crime_name,
            articles=articles,
            clause=clause,
            is_guilty=True,
            principal_penalty=principal_type,
            principal_penalty_name=principal_name,
            sentence_duration_years=sentence_years,
            sentence_formatted=sentence_text,
            is_suspended_sentence=is_suspended,
            probation_years=probation_years,
            supplementary_penalties=sup_penalties,
            judicial_measures=judicial_measures,
            legal_rationale=rationale,
            prohibitions_applied=prohibitions,
        )


def analyze_criminal_penalties(
    defendant_name: str,
    crime_name: str,
    articles: list[str],
    clause: str = "1",
    age: int = 25,
    is_pregnant_or_nursing: bool = False,
    is_foreigner: bool = False,
    statutory_range: tuple[float, float] = (1.0, 5.0),
    aggravating_count: int = 0,
    mitigating_count: int = 0,
    has_restitution: bool = False,
    has_cooperation: bool = False,
    is_first_offense: bool = True,
    role_type: str = "thực hành",
    illicit_profits_vnd: float = 0.0,
) -> dict[str, Any]:
    """Hàm tiện ích phân tích hình phạt trả về dict chuẩn JSON."""
    analysis = CriminalPenaltySystem.evaluate_penalties(
        defendant_name=defendant_name,
        crime_name=crime_name,
        articles=articles,
        clause=clause,
        age=age,
        is_pregnant_or_nursing=is_pregnant_or_nursing,
        is_foreigner=is_foreigner,
        statutory_range=statutory_range,
        aggravating_count=aggravating_count,
        mitigating_count=mitigating_count,
        has_restitution=has_restitution,
        has_cooperation=has_cooperation,
        is_first_offense=is_first_offense,
        role_type=role_type,
        illicit_profits_vnd=illicit_profits_vnd,
    )

    return {
        "defendant_name": analysis.defendant_name,
        "crime_name": analysis.crime_name,
        "articles": analysis.articles,
        "clause": analysis.clause,
        "is_guilty": analysis.is_guilty,
        "principal_penalty": {
            "type": analysis.principal_penalty.value,
            "name": analysis.principal_penalty_name,
            "sentence_years": analysis.sentence_duration_years,
            "formatted": analysis.sentence_formatted,
            "is_suspended": analysis.is_suspended_sentence,
            "probation_years": analysis.probation_years,
        },
        "supplementary_penalties": analysis.supplementary_penalties,
        "judicial_measures": analysis.judicial_measures,
        "legal_rationale": analysis.legal_rationale,
        "prohibitions_applied": analysis.prohibitions_applied,
        "system_reference": {
            "title": "Hệ thống Hình phạt theo Điều 32 Bộ luật Hình sự 2015",
            "principal_penalties_7": [p.name_vi for p in PRINCIPAL_PENALTY_REGISTRY.values()],
            "supplementary_penalties_7": [p.name_vi for p in SUPPLEMENTARY_PENALTY_REGISTRY.values()],
        },
    }
