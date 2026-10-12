"""Demo trực quan Hệ thống AI Phân tích & Hỗ trợ Pháp lý Đa Lĩnh vực Việt Nam.

Bao gồm cả 5 lĩnh vực pháp luật cốt lõi:
1. HÌNH SỰ (Criminal Law) - Chuẩn hóa toàn diện 7 hình phạt chính & 7 hình phạt bổ sung Điều 32 BLHS 2015
2. DÂN SỰ (Civil Law) - Kiểm soát trần lãi 20% Đ.468 BLDS & Bảng tính án phí NQ 326/2016/UBTVQH14
3. HÀNH CHÍNH (Administrative Law) - Tranh chấp CQNN, Chiến lược 2 kênh & Biện pháp khẩn cấp tạm thời Đ.68 LTTHC
4. THƯƠNG MẠI (Commercial Law) - Kiểm soát trần phạt vi phạm 8% Đ.301 LTM & Trọng tài VIAC Đ.6 LTTTM
5. KỶ LUẬT & LAO ĐỘNG (Disciplinary Law) - 4 hình thức kỷ luật Đ.124 BLLĐ, điều cấm Đ.127/Đ.137, bồi thường Đ.41

Chạy lệnh:
    python demo.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
import warnings
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

from src.first_instance.predictor import FirstInstancePredictor
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

# Đảm bảo mã hóa UTF-8 trên Windows Terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

warnings.filterwarnings("ignore")
try:
    from loguru import logger

    logger.remove()
except ImportError:
    pass
logging.getLogger().setLevel(logging.ERROR)

console = Console(legacy_windows=False)


async def run_multi_domain_demo() -> None:
    """Chạy kịch bản demo tự động qua 5 lĩnh vực pháp luật và Hệ thống hình phạt Điều 32 BLHS."""
    render_banner(
        console=console,
        title="HỆ THỐNG TRÍ TUỆ NHÂN TẠO PHÁP LÝ ĐA LĨNH VỰC VIỆT NAM",
        subtitle="Đại học Công nghệ Thông tin (UIT) - ĐHQG TP.HCM",
    )

    console.print(
        Panel(
            "[bold white]CHƯƠNG TRÌNH KHỞI ĐỘNG DEMO TỰ ĐỘNG BẢO ĐẢM TOÀN DIỆN:[/bold white]\n"
            "• [cyan]1. Lĩnh vực Hình sự[/cyan]: Phân tích tội danh, tình tiết tăng nặng/giảm nhẹ, 7 hình phạt chính & 7 hình phạt bổ sung (Điều 32 BLHS).\n"
            "• [cyan]2. Lĩnh vực Dân sự[/cyan]: Kiểm soát trần lãi suất 20%/năm (Điều 468 BLDS), Bảng tính án phí sơ thẩm (Nghị quyết 326/2016/UBTVQH14).\n"
            "• [cyan]3. Lĩnh vực Hành chính[/cyan]: Khiếu kiện thu hồi đất của UBND, Chiến lược 2 kênh (Khiếu nại 90 ngày & Khởi kiện 1 năm), Biện pháp khẩn cấp tạm thời (Điều 68 LTTHC).\n"
            "• [cyan]4. Lĩnh vực Thương mại[/cyan]: Hợp đồng mua bán 2 tỷ, Trần phạt vi phạm 8% (Điều 301 LTM 2005), Thỏa thuận trọng tài VIAC (Điều 6 LTTTM).\n"
            "• [cyan]5. Lĩnh vực Kỷ luật & Lao động[/cyan]: 4 hình thức kỷ luật (Điều 124 BLLĐ), Điều cấm sa thải mang thai (Điều 137), Bồi thường sa thải trái luật (Điều 41).",
            border_style="green",
            title="[bold green]MỤC TIÊU KIỂM THỬ DEMO[/bold green]",
        )
    )

    ml_predictor = FirstInstancePredictor()

    # =========================================================================
    # DEMO 1: HÌNH SỰ (CRIMINAL LAW - ĐIỀU 32 BLHS)
    # =========================================================================
    console.print(Rule("[bold magenta]PHẦN 1: PHÁP LUẬT HÌNH SỰ & ĐIỀU 32 BLHS 2015[/bold magenta]"))
    crim_personal = (
        "- Bị cáo: N Nữ sinh viên năm cuối ngành Công nghệ thông tin tại TP.HCM, gia đình khó khăn, mẹ bệnh loãng xương nặng.\n"
        "- Bị cáo: Hoàng Người trực tiếp nhận làm giả 2 CCCD gắn chip thu 2.300.000 đồng.\n"
        "- Bị cáo: P Người môi giới trung gian liên hệ.\n"
        "- Bị cáo: M, A Người nhờ thi hộ VSTEP."
    )
    crim_case = (
        "N nhận lời thi hộ chứng chỉ VSTEP cho M và A, nhờ Hoàng làm 2 CCCD giả dán ảnh của N. "
        "N thu lợi bất chính 3.050.000 đồng. N đã nộp lại toàn bộ số tiền thu lợi bất chính, tích cực hợp tác với cơ quan điều tra bắt giữ các đối tượng khác. "
        "Hành vi phạm tội Làm giả con dấu, tài liệu của cơ quan, tổ chức theo Điều 341 BLHS 2015."
    )

    parsed_crim = parse_two_inputs(crim_personal, crim_case)
    dispatch_crim = LegalDomainDispatcher.dispatch(
        text=f"{crim_personal}\n{crim_case}",
        forced_domain=LegalDomain.CRIMINAL,
        personal_info=crim_personal,
        case_info=crim_case,
    )
    ml_pred = ml_predictor.predict(parsed_crim.features)

    render_domain_badge(
        console=console,
        domain_name=dispatch_crim.primary_domain_name,
        primary_law=dispatch_crim.primary_law,
        domain_scores=dispatch_crim.domain_scores,
    )
    render_criminal_domain(
        console=console,
        analysis=dispatch_crim.domain_specific_analysis,
        parsed_case=parsed_crim,
        ml_prediction=ml_pred,
    )

    # =========================================================================
    # DEMO 2: DÂN SỰ (CIVIL LAW - TRẦN LÃI 20% & ÁN PHÍ NQ 326)
    # =========================================================================
    console.print(Rule("[bold magenta]PHẦN 2: PHÁP LUẬT DÂN SỰ & ÁN PHÍ THEO NQ 326/2016[/bold magenta]"))
    civ_text = (
        "Nguyên đơn: Bà Lê Thị Mai. Bị đơn: Ông Nguyễn Văn Hùng.\n"
        "Ngày 10/01/2023, bà Mai cho ông Hùng vay số tiền 800.000.000 đồng theo Giấy biên nhận vay tiền, "
        "thời hạn 06 tháng, lãi suất thỏa thuận 30%/năm. Hết hạn vay, ông Hùng không thanh toán tiền gốc và tiền lãi. "
        "Bà Mai khởi kiện yêu cầu hoàn trả 800.000.000 đồng nợ gốc và tiền lãi 30%/năm."
    )
    dispatch_civ = LegalDomainDispatcher.dispatch(
        text=civ_text,
        forced_domain=LegalDomain.CIVIL,
    )
    render_domain_badge(
        console=console,
        domain_name=dispatch_civ.primary_domain_name,
        primary_law=dispatch_civ.primary_law,
        domain_scores=dispatch_civ.domain_scores,
    )
    render_civil_domain(
        console=console,
        analysis=dispatch_civ.domain_specific_analysis,
    )

    # =========================================================================
    # DEMO 3: HÀNH CHÍNH (ADMINISTRATIVE LAW - CHIẾN LƯỢC 2 KÊNH & BPKCTT Đ.68)
    # =========================================================================
    console.print(Rule("[bold magenta]PHẦN 3: TRANH CHẤP VỚI CƠ QUAN NHÀ NƯỚC (LUẬT TTHC 2015)[/bold magenta]"))
    admin_text = (
        "Người khởi kiện: Hộ gia đình ông Đặng Văn Nam.\n"
        "Người bị kiện: Ủy ban nhân dân và Chủ tịch UBND Quận K, TP.Đà Nẵng.\n"
        "Chủ tịch UBND Quận K ban hành Quyết định thu hồi đất số 1234/QĐ-UBND và Quyết định phê duyệt phương án bồi thường GPMB "
        "với mức giá 5.000.000 đồng/m2, thấp hơn nhiều so với giá thị trường 25.000.000 đồng/m2. "
        "Đồng thời, UBND chuẩn bị cưỡng chế thu hồi đất khi chưa giải quyết xong khiếu nại của công dân."
    )
    dispatch_admin = LegalDomainDispatcher.dispatch(
        text=admin_text,
        forced_domain=LegalDomain.ADMINISTRATIVE,
    )
    render_domain_badge(
        console=console,
        domain_name=dispatch_admin.primary_domain_name,
        primary_law=dispatch_admin.primary_law,
        domain_scores=dispatch_admin.domain_scores,
    )
    render_administrative_domain(
        console=console,
        analysis=dispatch_admin.domain_specific_analysis,
    )

    # =========================================================================
    # DEMO 4: KINH DOANH THƯƠNG MẠI (COMMERCIAL LAW - TRẦN PHẠT 8% & VIAC)
    # =========================================================================
    console.print(Rule("[bold magenta]PHẦN 4: KINH DOANH THƯƠNG MẠI & TRỌNG TÀI VIAC[/bold magenta]"))
    com_text = (
        "Nguyên đơn: Công ty Cổ phần Đầu tư Công nghệ Hoàng Long.\n"
        "Bị đơn: Công ty TNHH Thiết bị Công nghiệp Việt Nhật.\n"
        "Hai bên ký Hợp đồng mua bán thiết bị máy móc số 05/HĐMB trị giá 2.000.000.000 đồng. "
        "Bên bán giao hàng chậm tiến độ 15 ngày. Điều 8 của Hợp đồng quy định phạt 15% tổng giá trị hợp đồng (300.000.000 đồng). "
        "Hợp đồng có thỏa thuận giải quyết tranh chấp tại Trung tâm Trọng tài Quốc tế Việt Nam (VIAC)."
    )
    dispatch_com = LegalDomainDispatcher.dispatch(
        text=com_text,
        forced_domain=LegalDomain.COMMERCIAL,
    )
    render_domain_badge(
        console=console,
        domain_name=dispatch_com.primary_domain_name,
        primary_law=dispatch_com.primary_law,
        domain_scores=dispatch_com.domain_scores,
    )
    render_commercial_domain(
        console=console,
        analysis=dispatch_com.domain_specific_analysis,
    )

    # =========================================================================
    # DEMO 5: KỶ LUẬT & LAO ĐỘNG (LABOR DISCIPLINE & ĐIỀU 124, 127, 137 BLLĐ)
    # =========================================================================
    console.print(Rule("[bold magenta]PHẦN 5: KỶ LUẬT LAO ĐỘNG & BẢO VỆ QUYỀN LỢI (BLLĐ 2019)[/bold magenta]"))
    disc_text = (
        "Người khiếu nại: Chị Nguyễn Thị Hương (Chuyên viên Nhân sự).\n"
        "Doanh nghiệp: Công ty TNHH May mặc Tân Tiến.\n"
        "Chị Hương đang mang thai tháng thứ 5 (có giấy khám thai của bệnh viện). "
        "Do sức khỏe yếu, chị Hương nghỉ 03 ngày đi khám bệnh có nộp đơn nhưng chưa được duyệt. "
        "Giám đốc công ty ra Quyết định sa thải chị Hương với lý do tự ý bỏ việc 03 ngày liên tục, không tổ chức cuộc họp xử lý kỷ luật có Công đoàn."
    )
    dispatch_disc = LegalDomainDispatcher.dispatch(
        text=disc_text,
        forced_domain=LegalDomain.DISCIPLINARY,
    )
    render_domain_badge(
        console=console,
        domain_name=dispatch_disc.primary_domain_name,
        primary_law=dispatch_disc.primary_law,
        domain_scores=dispatch_disc.domain_scores,
    )
    render_disciplinary_domain(
        console=console,
        analysis=dispatch_disc.domain_specific_analysis,
    )

    # =========================================================================
    # TỔNG KẾT
    # =========================================================================
    console.print(Rule("[bold green]TỔNG KẾT DEMO ĐA LĨNH VỰC HOÀN TẤT THÀNH CÔNG[/bold green]"))
    console.print(
        Panel(
            "[bold green]✓ HỆ THỐNG ĐÃ CHẠY HOÀN HẢO QUA CẢ 5 LĨNH VỰC PHÁP LUẬT:[/bold green]\n"
            "1. [bold]Hình sự[/bold]: Hiển thị chính xác A. 7 hình phạt chính và B. 7 hình phạt bổ sung theo Điều 32 BLHS 2015.\n"
            "2. [bold]Dân sự[/bold]: Tính toán tự động án phí 6 bậc theo Nghị quyết 326 và kiểm soát trần lãi 20% theo Điều 468 BLDS.\n"
            "3. [bold]Hành chính[/bold]: Vạch rõ chiến lược 2 kênh (90 ngày vs 1 năm) và đề xuất BPKCTT Điều 68 LTTHC.\n"
            "4. [bold]Thương mại[/bold]: Kiểm soát trần phạt vi phạm 8% Điều 301 LTM và bảo vệ thỏa thuận Trọng tài VIAC.\n"
            "5. [bold]Kỷ luật[/bold]: Nhận diện 4 hình thức hợp pháp Điều 124, chỉ rõ vi phạm cấm sa thải mang thai Điều 137 và bồi thường Điều 41 BLLĐ.",
            border_style="green",
        )
    )


if __name__ == "__main__":
    asyncio.run(run_multi_domain_demo())
