"""Giao diện Tương tác Dòng lệnh (CLI Terminal) Phân tích Pháp lý Đa Lĩnh vực Việt Nam.

Hỗ trợ:
- Cả 5 lĩnh vực pháp luật: Hình sự, Dân sự, Hành chính, Thương mại, Kỷ luật & Lao động.
- Chuẩn hóa đầy đủ Hệ thống Hình phạt Điều 32 BLHS: 7 hình phạt chính & 7 hình phạt bổ sung.
- 11 Hồ sơ mẫu thực tế 1-click hoặc Tự nhập liệu tự do bằng 2 Khung.
- Tự động phân loại quan hệ pháp luật hoặc chỉ định lĩnh vực theo yêu cầu.

Chạy lệnh:
    python interactive.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
import warnings
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table

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

# Đảm bảo UTF-8 trên Windows Terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Tắt các log nền để giữ màn hình terminal sạch đẹp
warnings.filterwarnings("ignore")
try:
    from loguru import logger

    logger.remove()
except ImportError:
    pass
logging.getLogger().setLevel(logging.ERROR)

console = Console(legacy_windows=False)

# Danh sách 11 hồ sơ mẫu đại diện cho cả 5 lĩnh vực pháp luật
CLI_PRESETS = {
    "1": {
        "title": "Hình sự: Làm giả CCCD và tổ chức thi hộ VSTEP (Điều 341 BLHS)",
        "domain": LegalDomain.CRIMINAL,
        "personal": (
            "- Bị cáo: N Nữ sinh viên năm cuối tại TP.HCM, gia đình khó khăn, mẹ bệnh nặng, lần đầu phạm tội.\n"
            "- Bị cáo: Hoàng Người trực tiếp làm giả 2 CCCD gắn chip thu 2.300.000 đồng.\n"
            "- Bị cáo: P Người môi giới trung gian.\n"
            "- Bị cáo: M, A Người nhờ thi hộ VSTEP."
        ),
        "case": (
            "N nhận lời thi hộ VSTEP cho M và A, nhờ Hoàng làm 2 CCCD giả dán ảnh N để vào phòng thi. "
            "N thu lợi bất chính 3.050.000 đồng. N đã nộp lại toàn bộ tiền thu lợi bất chính, tích cực hợp tác với cơ quan công an. "
            "Các bị cáo bị truy tố về tội Làm giả con dấu, tài liệu của cơ quan, tổ chức theo Điều 341 BLHS 2015."
        ),
    },
    "2": {
        "title": "Hình sự: Cố ý gây thương tích do mâu thuẫn bộc phát (Điều 134 BLHS)",
        "domain": LegalDomain.CRIMINAL,
        "personal": (
            "- Bị cáo: Nguyễn Văn An (SN 1995, chưa có tiền án tiền sự).\n"
            "- Bị hại: Trần Quốc Bình (SN 1998, tổn thương sức khỏe 35%)."
        ),
        "case": (
            "Khoảng 21 giờ ngày 15/04/2023, do mâu thuẫn tại quán ăn, Nguyễn Văn An dùng dao bấm (hung khí nguy hiểm) "
            "đâm vào ngực anh Bình gây tổn hại 35% sức khỏe. Sau khi gây án, An thành khẩn khai báo, tự nguyện bồi thường 50.000.000 đồng "
            "và được gia đình bị hại xin giảm nhẹ hình phạt. Bị truy tố theo Khoản 2 Điều 134 BLHS."
        ),
    },
    "3": {
        "title": "Hình sự: Cướp tài sản có vũ khí và tái phạm (Điều 168 BLHS)",
        "domain": LegalDomain.CRIMINAL,
        "personal": (
            "- Bị cáo 1: Hoàng Văn Nam (SN 1990, có 1 tiền án trộm cắp tài sản, chưa xóa án tích).\n"
            "- Bị cáo 2: Đỗ Văn Tuấn (SN 1994, đồng phạm giúp sức).\n"
            "- Bị hại: Chị Lê Thị Mai (bị cướp xe máy trị giá 35.000.000 đồng)."
        ),
        "case": (
            "Nam và Tuấn mang dao bấm khống chế chị Mai tại đoạn đường vắng, đe dọa vũ lực ngay tức khắc để cướp xe máy. "
            "Bị truy tố theo Khoản 2 Điều 168 BLHS (hình phạt từ 7 đến 15 năm tù)."
        ),
    },
    "4": {
        "title": "Hình sự: Cáo trạng truy tố tham ô nhưng chứng cứ hợp lệ (Tuyên Vô tội)",
        "domain": LegalDomain.CRIMINAL,
        "personal": (
            "- Bị cáo: Vũ Trọng Hưng (SN 1988, thủ quỹ công ty).\n"
            "- Đơn vị liên quan: Công ty TNHH Thương mại X."
        ),
        "case": (
            "Cáo trạng truy tố bị cáo Vũ Trọng Hưng về hành vi tham ô tài sản 200 triệu đồng. Tại tòa, giám định tài chính xác định "
            "toàn bộ số tiền trên đã được nhập quỹ đúng quy định, có chữ ký kế toán trưởng. Không có thiệt hại xảy ra và không có ý thức chiếm đoạt."
        ),
    },
    "5": {
        "title": "Dân sự: Tranh chấp hợp đồng vay nợ & Kiểm soát trần lãi 20% (Điều 468 BLDS)",
        "domain": LegalDomain.CIVIL,
        "personal": (
            "Nguyên đơn: Bà Lê Thị Mai (Bên cho vay)\n"
            "Bị đơn: Ông Nguyễn Văn Hùng (Bên vay nợ)"
        ),
        "case": (
            "Ngày 10/01/2023, bà Mai cho ông Hùng vay 800.000.000 đồng, thời hạn 6 tháng, lãi suất thỏa thuận 30%/năm. "
            "Hết hạn vay, ông Hùng không thanh toán tiền gốc và lãi. Bà Mai khởi kiện yêu cầu ông Hùng trả 800 triệu đồng gốc và lãi suất 30%/năm."
        ),
    },
    "6": {
        "title": "Dân sự: Tranh chấp phân chia di sản thừa kế quyền sử dụng đất (Điều 609 BLDS)",
        "domain": LegalDomain.CIVIL,
        "personal": (
            "Nguyên đơn: Ông Trần Văn A (con trưởng)\n"
            "Bị đơn: Bà Trần Thị B (con thứ)"
        ),
        "case": (
            "Cha mẹ mất năm 2018 không để lại di chúc. Di sản là thửa đất 300m2 tại Huyện C có Giấy chứng nhận QSDĐ. "
            "Bà B tự ý chiếm giữ và xây nhà trên toàn bộ thửa đất, từ chối chia di sản cho các đồng thừa kế khác."
        ),
    },
    "7": {
        "title": "Hành chính: Khiếu kiện Quyết định thu hồi đất & Cưỡng chế của UBND (Luật TTHC)",
        "domain": LegalDomain.ADMINISTRATIVE,
        "personal": (
            "Người khởi kiện: Hộ gia đình ông Đặng Văn Nam\n"
            "Người bị kiện: Ủy ban nhân dân và Chủ tịch UBND Quận K, TP.Đà Nẵng"
        ),
        "case": (
            "Chủ tịch UBND Quận K ban hành Quyết định thu hồi đất và phương án bồi thường GPMB giá 5.000.000 đ/m2 (giá thị trường 25.000.000 đ/m2). "
            "Đồng thời UBND ban hành Quyết định cưỡng chế khi chưa giải quyết xong khiếu nại của công dân."
        ),
    },
    "8": {
        "title": "Hành chính: Khiếu kiện Quyết định xử phạt VPHC vượt thẩm quyền của Đội QLTT",
        "domain": LegalDomain.ADMINISTRATIVE,
        "personal": (
            "Người khởi kiện: Công ty Cổ phần Thương mại Alpha\n"
            "Người bị kiện: Đội trưởng Đội Quản lý thị trường số 3"
        ),
        "case": (
            "Đội trưởng Đội QLTT số 3 ban hành Quyết định xử phạt vi phạm hành chính 80.000.000 đồng và tịch thu lô hàng 200.000.000 đồng. "
            "Mức phạt này vượt quá thẩm quyền tối đa 25.000.000 đồng theo Luật Xử lý vi phạm hành chính."
        ),
    },
    "9": {
        "title": "Thương mại: Tranh chấp phạt vi phạm vượt mức trần 8% theo Điều 301 LTM & VIAC",
        "domain": LegalDomain.COMMERCIAL,
        "personal": (
            "Nguyên đơn: Công ty Cổ phần Đầu tư Công nghệ Hoàng Long\n"
            "Bị đơn: Công ty TNHH Thiết bị Công nghiệp Việt Nhật"
        ),
        "case": (
            "Hợp đồng mua bán thiết bị máy móc trị giá 2.000.000.000 đồng. Bên bán giao chậm tiến độ 15 ngày. "
            "Điều 8 Hợp đồng quy định phạt vi phạm 15% tổng giá trị (300.000.000 đồng). Hai bên có thỏa thuận trọng tài VIAC."
        ),
    },
    "10": {
        "title": "Kỷ luật: Sa thải trái pháp luật đối với lao động nữ mang thai (Điều 137 BLLĐ)",
        "domain": LegalDomain.DISCIPLINARY,
        "personal": (
            "Người khiếu nại: Chị Nguyễn Thị Hương (Chuyên viên Nhân sự)\n"
            "Người sử dụng lao động: Công ty TNHH May mặc Tân Tiến"
        ),
        "case": (
            "Chị Hương đang mang thai tháng thứ 5. Do sức khỏe yếu, chị Hương nghỉ 03 ngày đi khám bệnh có nộp đơn nhưng chưa được duyệt. "
            "Giám đốc công ty ra Quyết định sa thải chị Hương với lý do tự ý bỏ việc 03 ngày liên tục, không có Công đoàn tham gia."
        ),
    },
    "11": {
        "title": "Kỷ luật: Phạt tiền trừ 50% lương tháng vi phạm điều cấm Điều 127 BLLĐ",
        "domain": LegalDomain.DISCIPLINARY,
        "personal": (
            "Người lao động: Anh Lê Văn Hùng (Công nhân vận hành máy)\n"
            "Doanh nghiệp: Công ty Cổ phần Cơ khí Chế tạo Máy Việt Hàn"
        ),
        "case": (
            "Trong ca làm việc ngày 12/07/2023, anh Hùng làm hỏng linh kiện máy trị giá 3.000.000 đồng. "
            "Giám đốc công ty ban hành Thông báo kỷ luật trừ 50% tiền lương tháng 7/2023 của anh Hùng để phạt vi phạm kỷ luật."
        ),
    },
}


def print_preset_menu() -> None:
    """In danh sách 11 hồ sơ mẫu ra màn hình theo nhóm lĩnh vực."""
    t_menu = Table(title="[bold yellow]DANH SÁCH 11 HỒ SƠ MẪU ĐA LĨNH VỰC PHÁP LUẬT[/bold yellow]")
    t_menu.add_column("Phím số", style="bold cyan", width=8, justify="center")
    t_menu.add_column("Lĩnh vực", style="bold magenta", width=14)
    t_menu.add_column("Tiêu đề hồ sơ vụ việc", style="white")

    domain_names = {
        LegalDomain.CRIMINAL: "Hình sự",
        LegalDomain.CIVIL: "Dân sự",
        LegalDomain.ADMINISTRATIVE: "Hành chính",
        LegalDomain.COMMERCIAL: "Thương mại",
        LegalDomain.DISCIPLINARY: "Kỷ luật / LĐ",
    }

    for key, p in CLI_PRESETS.items():
        t_menu.add_row(f"[{key}]", domain_names.get(p["domain"], "Pháp luật"), p["title"])
    console.print(t_menu)


async def execute_case_analysis(
    personal_info: str,
    case_info: str,
    forced_domain: LegalDomain | None = None,
    ml_predictor: FirstInstancePredictor | None = None,
) -> None:
    """Thực thi phân tích hồ sơ và hiển thị kết quả trực quan trên console."""
    full_text = f"{personal_info}\n\n{case_info}"

    console.print("\n[bold magenta]⚖️ Đang kích hoạt Bộ máy Phân tích Pháp lý Đa Lĩnh vực...[/bold magenta]")

    # 1. Dispatcher phân loại lĩnh vực
    dispatch_res = LegalDomainDispatcher.dispatch(
        text=full_text,
        forced_domain=forced_domain,
        personal_info=personal_info,
        case_info=case_info,
    )

    # 2. Hiển thị Huy hiệu lĩnh vực
    render_domain_badge(
        console=console,
        domain_name=dispatch_res.primary_domain_name,
        primary_law=dispatch_res.primary_law,
        domain_scores=dispatch_res.domain_scores,
    )

    chosen_domain = dispatch_res.primary_domain

    # 3. Hiển thị bảng chuyên biệt theo từng lĩnh vực
    if chosen_domain == LegalDomain.CRIMINAL:
        parsed_crim = parse_two_inputs(personal_info, case_info)
        ml_pred = ml_predictor.predict(parsed_crim.features) if ml_predictor else None
        render_criminal_domain(
            console=console,
            analysis=dispatch_res.domain_specific_analysis,
            parsed_case=parsed_crim,
            ml_prediction=ml_pred,
        )

    elif chosen_domain == LegalDomain.CIVIL:
        render_civil_domain(
            console=console,
            analysis=dispatch_res.domain_specific_analysis,
        )

    elif chosen_domain == LegalDomain.ADMINISTRATIVE:
        render_administrative_domain(
            console=console,
            analysis=dispatch_res.domain_specific_analysis,
        )

    elif chosen_domain == LegalDomain.COMMERCIAL:
        render_commercial_domain(
            console=console,
            analysis=dispatch_res.domain_specific_analysis,
        )

    elif chosen_domain == LegalDomain.DISCIPLINARY:
        render_disciplinary_domain(
            console=console,
            analysis=dispatch_res.domain_specific_analysis,
        )

    console.print(f"\n[bold green]✓ Phân tích hoàn tất: {dispatch_res.combined_summary}[/bold green]\n")


async def main() -> None:
    """Vòng lặp chính của giao diện tương tác CLI."""
    render_banner(console=console)

    ml_predictor = FirstInstancePredictor()

    while True:
        console.print(Rule("[bold cyan]MENU LỰA CHỌN THAO TÁC[/bold cyan]"))
        console.print(
            "[bold white]1. [1-11][/bold white] : Chạy ngay 1 trong 11 hồ sơ mẫu thực tế (5 lĩnh vực).\n"
            "[bold white]2. [c][/bold white]    : Tự nhập liệu bằng 2 Khung (Khung 1: Đương sự; Khung 2: Tình tiết).\n"
            "[bold white]3. [s][/bold white]    : Tự nhập liệu bằng 1 Khung văn bản tự do duy nhất.\n"
            "[bold white]4. [q][/bold white]    : Thoát chương trình."
        )

        choice = Prompt.ask("\n[bold green]Nhập lựa chọn của bạn[/bold green] (1-11, c, s, q)", default="1").strip().lower()

        if choice in ["q", "exit", "quit"]:
            console.print("[yellow]Tạm biệt! Cảm ơn bạn đã sử dụng Hệ thống Legal AI Vietnam.[/yellow]\n")
            break

        if choice in CLI_PRESETS:
            preset = CLI_PRESETS[choice]
            console.print(Panel(f"[bold cyan]ĐANG NẠP HỒ SƠ MẪU SỐ {choice}:[/bold cyan] [yellow]{preset['title']}[/yellow]", border_style="cyan"))
            await execute_case_analysis(
                personal_info=preset["personal"],
                case_info=preset["case"],
                forced_domain=preset["domain"],
                ml_predictor=ml_predictor,
            )

        elif choice in ["c", "custom", "2"]:
            console.print(Panel("[bold cyan]CHẾ ĐỘ TỰ NHẬP LIỆU BẰNG 2 KHUNG[/bold cyan]", border_style="cyan"))
            console.print("[dim]Nhập thông tin đương sự (bị cáo, bị hại, nguyên đơn, bị đơn, người khiếu nại...):[/dim]")
            personal = Prompt.ask("[bold green]Khung 1 - Đương sự[/bold green]").strip()

            console.print("\n[dim]Nhập nội dung tình tiết, hành vi, quan hệ pháp luật, yêu cầu giải quyết:[/dim]")
            case = Prompt.ask("[bold green]Khung 2 - Tình tiết vụ việc[/bold green]").strip()

            if not personal and not case:
                console.print("[red]Vui lòng không để trống cả 2 khung nhập liệu![/red]")
                continue

            console.print("\n[dim]Chọn lĩnh vực (Enter để hệ thống tự động nhận diện bằng Multi-Domain Dispatcher):[/dim]")
            dom_choice = Prompt.ask(
                "Chỉ định lĩnh vực [auto/crim/civ/adm/com/disc]",
                choices=["auto", "crim", "civ", "adm", "com", "disc"],
                default="auto",
            )
            forced_domain = None
            if dom_choice == "crim":
                forced_domain = LegalDomain.CRIMINAL
            elif dom_choice == "civ":
                forced_domain = LegalDomain.CIVIL
            elif dom_choice == "adm":
                forced_domain = LegalDomain.ADMINISTRATIVE
            elif dom_choice == "com":
                forced_domain = LegalDomain.COMMERCIAL
            elif dom_choice == "disc":
                forced_domain = LegalDomain.DISCIPLINARY

            await execute_case_analysis(
                personal_info=personal or "Đương sự trong vụ việc",
                case_info=case or "Tình tiết vụ việc",
                forced_domain=forced_domain,
                ml_predictor=ml_predictor,
            )

        elif choice in ["s", "single", "3"]:
            console.print(Panel("[bold cyan]CHẾ ĐỘ TỰ NHẬP LIỆU 1 KHUNG VĂN BẢN TỰ DO[/bold cyan]", border_style="cyan"))
            freeform = Prompt.ask("[bold green]Nhập hoặc dán toàn bộ văn bản vụ việc[/bold green]").strip()
            if not freeform:
                console.print("[red]Nội dung văn bản không được để trống![/red]")
                continue

            await execute_case_analysis(
                personal_info="",
                case_info=freeform,
                forced_domain=None,
                ml_predictor=ml_predictor,
            )

        else:
            console.print("[red]Lựa chọn không hợp lệ, vui lòng thử lại![/red]")


if __name__ == "__main__":
    asyncio.run(main())
