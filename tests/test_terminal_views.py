"""Kiểm thử tự động cho hệ thống hiển thị Terminal Views đa lĩnh vực và Hệ thống hình phạt Điều 32 BLHS."""

from __future__ import annotations

from rich.console import Console

from src.legal_domains.dispatcher import LegalDomain, LegalDomainDispatcher
from src.orchestration.case_parser import parse_two_inputs
from src.presentation.terminal_views import (
    render_administrative_domain,
    render_banner,
    render_civil_domain,
    render_commercial_domain,
    render_criminal_domain,
    render_disciplinary_domain,
    render_domain_badge,
)


def test_render_banner_and_badge() -> None:
    """Kiểm tra render banner và domain badge không gây exception."""
    console = Console(record=True, width=100)
    render_banner(console)
    render_domain_badge(
        console=console,
        domain_name="Pháp luật Hình sự",
        primary_law="Bộ luật Hình sự 2015",
        domain_scores={"criminal": 0.85, "civil": 0.15},
    )
    output = console.export_text()
    assert "HỆ THỐNG AI" in output
    assert "PHÁP LUẬT HÌNH SỰ" in output


def test_render_criminal_domain() -> None:
    """Kiểm tra render kết quả Hình sự với 7 hình phạt chính & 7 hình phạt bổ sung Điều 32."""
    console = Console(record=True, width=120)

    personal = "- Bị cáo: Nguyễn Văn An (SN 1995)\n- Bị hại: Trần Quốc Bình (SN 1998)"
    case = "Nguyễn Văn An dùng dao bấm gây thương tích 35% cho anh Bình. Bị cáo đã bồi thường 50 triệu và thành khẩn khai báo."

    parsed = parse_two_inputs(personal, case)
    dispatch_res = LegalDomainDispatcher.dispatch(
        text=f"{personal}\n{case}",
        forced_domain=LegalDomain.CRIMINAL,
        personal_info=personal,
        case_info=case,
    )

    render_criminal_domain(
        console=console,
        analysis=dispatch_res.domain_specific_analysis,
        parsed_case=parsed,
        ml_prediction={"predicted_outcome": "guilty", "confidence": 0.95, "predicted_sentence_years": 2.5},
    )

    output = console.export_text()
    assert "HỆ THỐNG 7 HÌNH PHẠT CHÍNH" in output
    assert "HỆ THỐNG 7 HÌNH PHẠT BỔ SUNG" in output
    assert "Tù có thời hạn" in output
    assert "Điều 32" in output or "ĐIỀU 32" in output


def test_render_civil_domain() -> None:
    """Kiểm tra render kết quả Dân sự với trần lãi 20% và Bảng án phí NQ 326."""
    console = Console(record=True, width=120)
    text = "Bà Mai cho ông Hùng vay 800.000.000 đồng lãi 30%/năm nhưng ông Hùng không trả nợ."

    dispatch_res = LegalDomainDispatcher.dispatch(
        text=text,
        forced_domain=LegalDomain.CIVIL,
    )

    render_civil_domain(console=console, analysis=dispatch_res.domain_specific_analysis)
    output = console.export_text()

    assert "TRANH CHẤP DÂN SỰ" in output
    assert "ĐIỀU 468" in output or "468" in output
    assert "326/2016/UBTVQH14" in output


def test_render_administrative_domain() -> None:
    """Kiểm tra render kết quả Hành chính với Chiến lược 2 kênh & BPKCTT."""
    console = Console(record=True, width=120)
    text = "UBND Quận K ban hành quyết định thu hồi đất và cưỡng chế thu hồi đất của hộ ông Nam."

    dispatch_res = LegalDomainDispatcher.dispatch(
        text=text,
        forced_domain=LegalDomain.ADMINISTRATIVE,
    )

    render_administrative_domain(console=console, analysis=dispatch_res.domain_specific_analysis)
    output = console.export_text()

    assert "TRANH CHẤP VỚI CƠ QUAN NHÀ NƯỚC" in output
    assert "KHIẾU NẠI" in output
    assert "KHỞI KIỆN" in output
    assert "BIỆN PHÁP KHẨN CẤP TẠM THỜI" in output


def test_render_commercial_domain() -> None:
    """Kiểm tra render kết quả Thương mại với Trần phạt 8% & Trọng tài VIAC."""
    console = Console(record=True, width=120)
    text = "Hợp đồng mua bán máy móc 2.000.000.000 đồng phạt giao chậm 15% tổng giá trị (300 triệu đồng). Trọng tài VIAC."

    dispatch_res = LegalDomainDispatcher.dispatch(
        text=text,
        forced_domain=LegalDomain.COMMERCIAL,
    )

    render_commercial_domain(console=console, analysis=dispatch_res.domain_specific_analysis)
    output = console.export_text()

    assert "TRANH CHẤP KINH DOANH THƯƠNG MẠI" in output
    assert "8%" in output
    assert "VIAC" in output or "Trọng tài" in output


def test_render_disciplinary_domain() -> None:
    """Kiểm tra render kết quả Kỷ luật với 4 hình thức hợp pháp và điều cấm BLLĐ."""
    console = Console(record=True, width=120)
    text = "Công ty sa thải chị Hương đang mang thai tháng thứ 5 vì nghỉ 3 ngày đi khám thai."

    dispatch_res = LegalDomainDispatcher.dispatch(
        text=text,
        forced_domain=LegalDomain.DISCIPLINARY,
    )

    render_disciplinary_domain(console=console, analysis=dispatch_res.domain_specific_analysis)
    output = console.export_text()

    assert "KỶ LUẬT LAO ĐỘNG" in output
    assert "4 HÌNH THỨC KỶ LUẬT" in output
    assert "ĐIỀU 41" in output or "Bồi thường" in output
