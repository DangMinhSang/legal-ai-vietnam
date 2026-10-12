"""Unit test kiểm thử bộ phân tích 2 khung nhập liệu và nhận diện Điều 341 BLHS."""

from __future__ import annotations

import pytest

from src.orchestration.case_parser import extract_parties, parse_two_inputs


def test_extract_parties_forgery_case() -> None:
    personal_info = (
        "- Bị cáo: N Nữ sinh viên năm cuối ngành Công nghệ thông tin tại TP.HCM, gia đình khó khăn do bạo lực gia đình; "
        "mẹ mắc bệnh loãng xương nặng, em trai bị nhược thị. N làm gia sư để trang trải sinh hoạt, học phí và chi phí chữa bệnh cho mẹ.\n"
        "- Bị cáo: P Người trung gian, môi giới để N liên hệ với đường dây làm giả CCCD.\n"
        "- Bị cáo: Hoàng Người trực tiếp nhận làm giả CCCD, gắn ảnh của N vào thông tin của người khác và yêu cầu thanh toán trước khi giao.\n"
        "- Bị cáo: M Người nhờ N thi hộ chứng chỉ tiếng Anh VSTEP, cung cấp thông tin cá nhân để làm CCCD giả.\n"
        "- Bị cáo: A Người nhờ N thi hộ chứng chỉ tiếng Anh VSTEP, chuyển 1.200.000 đồng phục vụ chi phí làm CCCD giả.\n"
        "- Bị cáo: T Người trực tiếp vận chuyển, giao CCCD giả tại điểm hẹn ở cửa hàng Ministop, Quận 1."
    )

    parties = extract_parties(personal_info)
    assert len(parties) == 6

    names = [p.name for p in parties]
    assert names == ["N", "P", "Hoàng", "M", "A", "T"]

    # Đảm bảo không còn bị bóc tách sai thành cụm từ vô nghĩa
    assert "ành Công" not in names
    assert "ới để" not in names
    assert "Hoàng Người" not in names
    assert "ếng Anh" not in names
    assert "ại điểm" not in names

    # Kiểm tra phân định vai trò chi tiết
    party_dict = {p.name: p for p in parties}
    assert "Làm giả trực tiếp" in party_dict["Hoàng"].role_detail
    assert "môi giới" in party_dict["P"].role_detail.lower()
    assert "vận chuyển" in party_dict["T"].role_detail.lower()
    assert "sử dụng" in party_dict["N"].role_detail.lower()


def test_parse_two_inputs_forgery_case() -> None:
    personal_info = (
        "- Bị cáo: N Nữ sinh viên năm cuối ngành Công nghệ thông tin tại TP.HCM, gia đình khó khăn do bạo lực gia đình; mẹ mắc bệnh loãng xương nặng, em trai bị nhược thị. N làm gia sư để trang trải sinh hoạt, học phí và chi phí chữa bệnh cho mẹ.\n"
        "- Bị cáo: P Người trung gian, môi giới để N liên hệ với đường dây làm giả CCCD.\n"
        "- Bị cáo: Hoàng Người trực tiếp nhận làm giả CCCD, gắn ảnh của N vào thông tin của người khác và yêu cầu thanh toán trước khi giao.\n"
        "- Bị cáo: M Người nhờ N thi hộ chứng chỉ tiếng Anh VSTEP, cung cấp thông tin cá nhân để làm CCCD giả.\n"
        "- Bị cáo: A Người nhờ N thi hộ chứng chỉ tiếng Anh VSTEP, chuyển 1.200.000 đồng phục vụ chi phí làm CCCD giả.\n"
        "- Bị cáo: T Người trực tiếp vận chuyển, giao CCCD giả tại điểm hẹn ở cửa hàng Ministop, Quận 1."
    )

    case_info = (
        "Do hoàn cảnh kinh tế khó khăn, áp lực học tập và nhu cầu trang trải học phí, chi phí chữa bệnh cho mẹ, "
        "N nhận lời thi hộ chứng chỉ tiếng Anh VSTEP cho M và A. Để qua mặt khâu kiểm tra danh tính tại phòng thi, "
        "N thông qua P liên hệ Hoàng (H) làm hai CCCD giả mang thông tin của người nhờ thi nhưng gắn ảnh của N. "
        "N đã thực hiện trót lọt hai lần thi hộ và thu lợi bất chính tổng cộng 3.050.000 đồng; riêng M, N chỉ nhận 800.000 đồng sau khi có kết quả đậu.\n\n"
        "Trưa ngày 19/01/2024, N sử dụng tài khoản Zalo cá nhân hỗ trợ lực lượng chức năng xác minh, liên lạc với P và xác định P đang ở Long An. "
        "N tiếp tục liên lạc, hẹn H giao CCCD giả mang tên A tại cửa hàng Ministop, địa chỉ 41–43 Đinh Tiên Hoàng, Quận 1, TP.HCM. "
        "Theo yêu cầu của H, N sử dụng 1.200.000 đồng do A chuyển và tự bỏ thêm 1.100.000 đồng để thanh toán đủ 2.300.000 đồng. "
        "Đến khoảng 22 giờ cùng ngày, lực lượng chức năng bắt quả tang T khi giao CCCD giả tại điểm hẹn, thu giữ tang vật. "
        "Sau đó, N đã nộp lại toàn bộ số tiền thu lợi bất chính."
    )

    parsed = parse_two_inputs(personal_info, case_info)

    # 1. Tội danh Điều 341, tuyệt đối không gán nhầm Điều 134
    assert "341" in parsed.detected_articles
    assert "134" not in parsed.detected_articles
    assert "Khoản 2 Điều 341" in parsed.detected_crime_name
    assert parsed.detected_clause == "2"

    # 2. Khung hình phạt luật định Khoản 2 Điều 341: 2.0 - 5.0 năm
    assert parsed.primary_statutory_bounds == (2.0, 5.0)

    # 3. Tình tiết tăng nặng
    assert any("có tổ chức" in a.lower() for a in parsed.aggravating_factors)
    assert any("02 lần trở lên" in a.lower() for a in parsed.aggravating_factors)

    # 4. Tình tiết giảm nhẹ
    assert any("nộp lại" in m.lower() for m in parsed.mitigating_factors)
    assert any("hợp tác" in m.lower() for m in parsed.mitigating_factors)
    assert any("hoàn cảnh" in m.lower() for m in parsed.mitigating_factors)

    # 5. Khuyến nghị cá thể hóa hình phạt
    def_dict = {d.name: d for d in parsed.defendants}
    assert "Điều 54" in def_dict["N"].individual_penalty_recommendation or "Án treo" in def_dict["N"].individual_penalty_recommendation
    assert "trực tiếp" in def_dict["Hoàng"].individual_penalty_recommendation.lower()


def test_split_freeform_text_and_single_input() -> None:
    from src.orchestration.case_parser import split_freeform_text

    combined_text = (
        "- Bị cáo: N Nữ sinh viên tại TP.HCM, hoàn cảnh khó khăn.\n"
        "- Bị cáo: Hoàng Người trực tiếp làm giả CCCD.\n"
        "- Bị hại: Trường Đại học S.\n"
        "Vào ngày 19/01/2024, N đã thông qua mạng xã hội nhờ Hoàng làm giả CCCD nhằm thi hộ tiếng Anh VSTEP."
    )

    personal, case = split_freeform_text(combined_text)
    assert "Bị cáo: N" in personal
    assert "Bị cáo: Hoàng" in personal
    assert "Bị hại: Trường" in personal
    assert "thi hộ" in case

    # Kiểm tra phân tích trực tiếp từ full_text (1 khung duy nhất)
    parsed = parse_two_inputs(full_text=combined_text)
    assert len(parsed.defendants) >= 2
    names = [d.name for d in parsed.defendants]
    assert "N" in names
    assert "Hoàng" in names
    assert "341" in parsed.detected_articles

