"""Module hiển thị kết quả phân tích đa lĩnh vực pháp luật và Hệ thống hình phạt Điều 32 BLHS trên Terminal Rich."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.legal_domains.criminal import CriminalPenaltySystem


def render_banner(
    console: Console,
    title: str = "HỆ THỐNG AI PHÂN TÍCH & DỰ ĐOÁN PHÁP LUẬT VIỆT NAM",
    subtitle: str = "Đại học Công nghệ Thông tin (UIT) - ĐHQG TP.HCM",
) -> None:
    """Hiển thị banner tiêu đề hệ thống chuẩn UIT."""
    console.print(
        Panel.fit(
            f"[bold cyan]{title}[/bold cyan]\n"
            f"[white]{subtitle}[/white]\n"
            f"[green]Hỗ trợ 5 Lĩnh vực Pháp luật & Chuẩn hóa Hệ thống Hình phạt Điều 32 BLHS 2015[/green]",
            border_style="cyan",
        )
    )


def render_domain_badge(
    console: Console,
    domain_name: str,
    primary_law: str,
    domain_scores: dict[str, float] | None = None,
) -> None:
    """Hiển thị thông tin lĩnh vực pháp luật đã được phân loại."""
    score_desc = ""
    if domain_scores:
        score_desc = " | ".join([f"{k.upper()}: {v*100:.1f}%" for k, v in domain_scores.items()])

    console.print(
        Panel(
            f"[bold yellow]LĨNH VỰC XÁC ĐỊNH:[/bold yellow] [bold white on blue] {domain_name.upper()} [/bold white on blue]\n"
            f"[cyan]Căn cứ pháp lý chủ đạo:[/cyan] [white]{primary_law}[/white]"
            + (f"\n[dim]Phân bố xác suất đa lĩnh vực: {score_desc}[/dim]" if score_desc else ""),
            border_style="blue",
            title="[bold blue]PHÂN LOẠI QUAN HỆ PHÁP LUẬT[/bold blue]",
        )
    )


def render_criminal_domain(
    console: Console,
    analysis: dict[str, Any],
    parsed_case: Any | None = None,
    ml_prediction: dict[str, Any] | None = None,
) -> None:
    """Hiển thị toàn diện phân tích vụ án hình sự và Hệ thống hình phạt Điều 32 BLHS."""
    # 1. Bảng đương sự và vai trò
    t_parties = Table(title="[bold yellow]1. ĐƯƠNG SỰ VÀ PHÂN ĐỊNH VAI TRÒ TỐ TỤNG[/bold yellow]")
    t_parties.add_column("Vai trò", style="magenta", width=12)
    t_parties.add_column("Họ và tên / Mã đương sự", style="white", width=22)
    t_parties.add_column("Phân định vai trò chi tiết", style="cyan")
    t_parties.add_column("Tiền án", style="yellow", justify="center", width=10)

    if parsed_case and hasattr(parsed_case, "parties") and parsed_case.parties:
        for p in parsed_case.parties:
            t_parties.add_row(
                p.role,
                p.name,
                p.role_detail or p.details,
                f"{p.prior_convictions} tiền án" if p.prior_convictions > 0 else "Chưa có",
            )
    else:
        def_name = analysis.get("defendant_name", "Bị cáo chính")
        t_parties.add_row("Bị cáo", def_name, "Bị cáo thực hiện hành vi trong vụ án", "Chưa có")
    console.print(t_parties)

    # 2. Bảng Tình tiết & Tội danh
    t_factors = Table(title="\n[bold yellow]2. ĐỊNH DANH TỘI DANH & TÌNH TIẾT ĐIỀU 51 / ĐIỀU 52 BLHS[/bold yellow]")
    t_factors.add_column("Tiêu chí pháp lý", style="cyan", width=24)
    t_factors.add_column("Nội dung xác định", style="white")

    t_factors.add_row(
        "Tội danh và Điều luật",
        f"[bold red]{analysis.get('crime_name', 'Tội phạm hình sự')}[/bold red] "
        f"(Điều {', '.join(analysis.get('articles', []))} BLHS 2015)",
    )
    t_factors.add_row(
        "Khung hình phạt luật định",
        f"{analysis.get('statutory_range', (1.0, 5.0))[0]:.1f} đến {analysis.get('statutory_range', (1.0, 5.0))[1]:.1f} năm tù",
    )

    agg_count = analysis.get("aggravating_count", 0)
    mit_count = analysis.get("mitigating_count", 0)
    t_factors.add_row("Tình tiết tăng nặng (Đ.52)", f"{agg_count} tình tiết tăng nặng trách nhiệm hình sự")
    t_factors.add_row("Tình tiết giảm nhẹ (Đ.51)", f"{mit_count} tình tiết giảm nhẹ trách nhiệm hình sự")
    console.print(t_factors)

    # 3. BẢNG 7 HÌNH PHẠT CHÍNH (ĐIỀU 32 BLHS)
    p_pen = analysis.get("principal_penalty", {})
    applied_type = p_pen.get("type")

    t_princ = Table(title="\n[bold yellow]3. A. HỆ THỐNG 7 HÌNH PHẠT CHÍNH (KHOẢN 1 ĐIỀU 32 BLHS 2015)[/bold yellow]")
    t_princ.add_column("STT", style="cyan", width=4, justify="center")
    t_princ.add_column("Tên hình phạt chính", style="bold white", width=26)
    t_princ.add_column("Điều luật BLHS", style="magenta", width=14)
    t_princ.add_column("Trạng thái", style="bold", width=16, justify="center")
    t_princ.add_column("Đề xuất cụ thể / Điều kiện áp dụng", style="white")

    all_princs = CriminalPenaltySystem.get_all_principal_penalties()
    for idx, p in enumerate(all_princs, start=1):
        is_applied = (p["code"] == applied_type)
        status_str = "[bold white on green] ĐANG ÁP DỤNG [/bold white on green]" if is_applied else "[dim]KHÔNG ÁP DỤNG[/dim]"
        detail_str = f"[bold green]{p_pen.get('formatted', p['name'])}[/bold green]" if is_applied else f"[dim]{p['conditions']}[/dim]"

        t_princ.add_row(
            str(idx),
            p["name"],
            p["article"],
            status_str,
            detail_str,
        )
    console.print(t_princ)

    # 4. BẢNG 7 HÌNH PHẠT BỔ SUNG (ĐIỀU 32 BLHS)
    sup_pens = analysis.get("supplementary_penalties", [])
    applied_sup_codes = [s.get("type") for s in sup_pens]

    t_sup = Table(title="\n[bold yellow]4. B. HỆ THỐNG 7 HÌNH PHẠT BỔ SUNG (KHOẢN 2 ĐIỀU 32 BLHS 2015)[/bold yellow]")
    t_sup.add_column("STT", style="cyan", width=4, justify="center")
    t_sup.add_column("Tên hình phạt bổ sung", style="bold white", width=36)
    t_sup.add_column("Điều luật BLHS", style="magenta", width=14)
    t_sup.add_column("Trạng thái", style="bold", width=16, justify="center")
    t_sup.add_column("Mức đề xuất / Căn cứ", style="white")

    all_sups = CriminalPenaltySystem.get_all_supplementary_penalties()
    for idx, s in enumerate(all_sups, start=1):
        is_applied = (s["code"] in applied_sup_codes)
        status_str = "[bold white on blue] ĐỀ XUẤT ÁP DỤNG [/bold white on blue]" if is_applied else "[dim]KHÔNG ÁP DỤNG[/dim]"

        applied_item = next((item for item in sup_pens if item.get("type") == s["code"]), None)
        if applied_item:
            amt_or_dur = applied_item.get("amount") or applied_item.get("duration") or "Theo quy định"
            detail_str = f"[bold cyan]{amt_or_dur}[/bold cyan]"
        else:
            detail_str = f"[dim]{s['conditions']}[/dim]"

        t_sup.add_row(
            str(idx),
            s["name"],
            s["article"],
            status_str,
            detail_str,
        )
    console.print(t_sup)

    # 5. Biện pháp tư pháp (Điều 46, 47, 48 BLHS)
    jud_measures = analysis.get("judicial_measures", [])
    if jud_measures:
        t_jud = Table(title="\n[bold yellow]5. BIỆN PHÁP TƯ PHÁP (ĐIỀU 46, 47, 48 BLHS)[/bold yellow]")
        t_jud.add_column("Loại biện pháp", style="cyan", width=28)
        t_jud.add_column("Nội dung quyết định", style="white")
        for jm in jud_measures:
            t_jud.add_row(jm.get("name", "Biện pháp tư pháp"), jm.get("description", "Áp dụng theo luật định"))
        console.print(t_jud)

    # 6. Đề xuất cá thể hóa & Án treo / Điều 54
    can_prob = analysis.get("can_apply_probation", False)
    can_below = analysis.get("can_apply_below_frame", False)
    t_indiv = Table(title="\n[bold yellow]6. CÁ THỂ HÓA HÌNH PHẠT & ĐIỀU KIỆN ÁP DỤNG ĐẶC BIỆT[/bold yellow]")
    t_indiv.add_column("Nguyên tắc cá thể hóa", style="cyan", width=28)
    t_indiv.add_column("Kết luận pháp lý", style="white")

    t_indiv.add_row(
        "Án treo (Điều 65 BLHS)",
        "[bold green]ĐỦ ĐIỀU KIỆN ÁP DỤNG[/bold green] (Án <= 3 năm, nhân thân tốt, >= 2 tình tiết giảm nhẹ)"
        if can_prob else "[yellow]KHÔNG ĐỦ ĐIỀU KIỆN[/yellow] (Vượt quá 3 năm tù hoặc chưa thỏa mãn điều kiện Điều 65)",
    )
    t_indiv.add_row(
        "Quyết định dưới khung (Điều 54 BLHS)",
        "[bold green]ÁP DỤNG ĐƯỢC[/bold green] (Có từ 2 tình tiết giảm nhẹ Khoản 1 Điều 51 trở lên)"
        if can_below else "[dim]Không áp dụng (Chưa đủ điều kiện Khoản 1 Điều 54)[/dim]",
    )
    t_indiv.add_row("Cá thể hóa từng bị cáo", analysis.get("individualization_summary", "Đã cá thể hóa theo vai trò."))
    console.print(t_indiv)

    # 7. Dự đoán của ML Model nếu có
    if ml_prediction:
        t_ml = Table(title="\n[bold yellow]7. KẾT QUẢ DỰ ĐOÁN CỦA MÔ HÌNH HỌC MÁY (ML ENGINE)[/bold yellow]")
        t_ml.add_column("Thuộc tính", style="cyan", width=25)
        t_ml.add_column("Dự đoán", style="bold green")
        t_ml.add_column("Kiểm soát ranh giới", style="yellow")

        out_str = "CÓ TỘI (Guilty)" if ml_prediction.get("predicted_outcome") == "guilty" else "VÔ TỘI (Not Guilty)"
        conf = ml_prediction.get("confidence", 0.0)
        years = ml_prediction.get("predicted_sentence_years", 0.0)
        m_name = ml_prediction.get("model_name", "RandomForestClassifier")

        t_ml.add_row("Phán quyết", out_str, m_name)
        t_ml.add_row("Mức án đề xuất", f"{years:.2f} năm tù", "RandomForestRegressor + Bounded")
        t_ml.add_row("Độ tin cậy", f"{conf * 100:.1f}%", "Hàng rào nhất quán: Không án âm, vô tội = 0 năm")
        console.print(t_ml)


def render_civil_domain(console: Console, analysis: dict[str, Any]) -> None:
    """Hiển thị toàn diện phân tích tranh chấp Dân sự và Tính án phí theo Nghị quyết 326/2016/UBTVQH14."""
    # 1. Bảng quan hệ pháp luật
    t_overview = Table(title="[bold yellow]1. QUAN HỆ TRANH CHẤP DÂN SỰ & CĂN CỨ PHÁP LUẬT[/bold yellow]")
    t_overview.add_column("Thuộc tính", style="cyan", width=25)
    t_overview.add_column("Thông tin xác định", style="white")

    t_overview.add_row("Quan hệ tranh chấp", f"[bold green]{analysis.get('dispute_name', 'Tranh chấp dân sự')}[/bold green]")
    t_overview.add_row("Nguyên đơn", analysis.get("plaintiff", "Nguyên đơn"))
    t_overview.add_row("Bị đơn", analysis.get("defendant", "Bị đơn"))
    t_overview.add_row("Văn bản áp dụng", ", ".join(analysis.get("applicable_laws", ["Bộ luật Dân sự 2015"])))
    t_overview.add_row("Giá trị tranh chấp", f"[bold yellow]{analysis.get('claim_amount_formatted', '0 VNĐ')}[/bold yellow]")
    console.print(t_overview)

    # 2. Bảng kiểm soát trần lãi suất 20%/năm (Điều 468 BLDS)
    t_interest = Table(title="\n[bold yellow]2. KIỂM SOÁT LÃI SUẤT TRẦN THEO ĐIỀU 468 BỘ LUẬT DÂN SỰ 2015[/bold yellow]")
    t_interest.add_column("Tiêu chuẩn kiểm soát", style="cyan", width=30)
    t_interest.add_column("Kết luận pháp lý", style="white")

    interest_valid = analysis.get("interest_rate_claim_valid", True)
    if interest_valid:
        t_interest.add_row("Quy tắc trần lãi suất (Khoản 1 Điều 468)", "[bold green]HỢP PHÁP[/bold green] (Lãi suất thỏa thuận không vượt quá 20%/năm của khoản tiền vay)")
    else:
        t_interest.add_row("Quy tắc trần lãi suất (Khoản 1 Điều 468)", "[bold red]VƯỢT TRẦN PHÁP ĐỊNH[/bold red] (Lãi suất thỏa thuận vượt quá 20%/năm. Phần lãi suất vượt quá 20%/năm KHÔNG CÓ HIỆU LỰC)")
    t_interest.add_row("Đánh giá thời hiệu khởi kiện", analysis.get("statute_of_limitations_note", "Thời hiệu khởi kiện 03 năm theo Điều 429 BLDS"))
    console.print(t_interest)

    # 3. BẢNG TÍNH ÁN PHÍ SƠ THẨM CÓ GIÁ NGẠCH THEO NGHỊ QUYẾT 326/2016/UBTVQH14
    t_fee = Table(title="\n[bold yellow]3. BẢNG TÍNH ÁN PHÍ DÂN SỰ SƠ THẨM (NGHỊ QUYẾT 326/2016/UBTVQH14)[/bold yellow]")
    t_fee.add_column("Bậc giá trị tranh chấp", style="cyan", width=32)
    t_fee.add_column("Công thức tính án phí theo NQ 326", style="magenta")
    t_fee.add_column("Áp dụng cho vụ việc này", style="bold green")

    brackets = [
        ("Bậc 1: Từ 6.000.000 VNĐ trở xuống", "300.000 VNĐ", "Cố định"),
        ("Bậc 2: Từ 6.000.000 đến 400.000.000 VNĐ", "5% giá trị có tranh chấp", "5%"),
        ("Bậc 3: Từ 400.000.000 đến 800.000.000 VNĐ", "20.000.000 VNĐ + 4% của phần vượt 400 triệu", "20 tr + 4% vượt"),
        ("Bậc 4: Từ 800.000.000 đến 2.000.000.000 VNĐ", "36.000.000 VNĐ + 3% của phần vượt 800 triệu", "36 tr + 3% vượt"),
        ("Bậc 5: Từ 2.000.000.000 đến 4.000.000.000 VNĐ", "72.000.000 VNĐ + 2% của phần vượt 2 tỷ", "72 tr + 2% vượt"),
        ("Bậc 6: Từ trên 4.000.000.000 VNĐ", "112.000.000 VNĐ + 0.1% của phần vượt 4 tỷ", "112 tr + 0.1% vượt"),
    ]
    for b_name, b_formula, b_note in brackets:
        t_fee.add_row(b_name, b_formula, b_note)

    t_fee.add_section()
    t_fee.add_row(
        "[bold yellow]TỔNG ÁN PHÍ SƠ THẨM DỰ KIẾN[/bold yellow]",
        "[bold yellow]Nghị quyết số 326/2016/UBTVQH14[/bold yellow]",
        f"[bold white on red] {analysis.get('estimated_court_fee_formatted', '300.000 VNĐ')} [/bold white on red]",
    )
    console.print(t_fee)

    # 4. Lộ trình giải quyết tranh chấp
    steps = analysis.get("suggested_steps", [])
    if steps:
        t_steps = Table(title="\n[bold yellow]4. LỘ TRÌNH GIẢI QUYẾT TRANH CHẤP DÂN SỰ TỐI ƯU[/bold yellow]")
        t_steps.add_column("Bước", style="cyan", width=8, justify="center")
        t_steps.add_column("Hành động pháp lý cụ thể", style="white")
        for i, st in enumerate(steps, start=1):
            t_steps.add_row(f"Bước {i}", st)
        console.print(t_steps)


def render_administrative_domain(console: Console, analysis: dict[str, Any]) -> None:
    """Hiển thị toàn diện phân tích Khiếu kiện Hành chính và Chiến lược 2 kênh song song."""
    # 1. Bảng đối tượng khiếu kiện
    t_admin = Table(title="[bold yellow]1. TRANH CHẤP VỚI CƠ QUAN NHÀ NƯỚC & ĐỐI TƯỢNG KHIẾU KIỆN[/bold yellow]")
    t_admin.add_column("Thuộc tính", style="cyan", width=25)
    t_admin.add_column("Thông tin xác định", style="white")

    t_admin.add_row("Đối tượng khiếu kiện", f"[bold red]{analysis.get('target_description', 'Quyết định hành chính')}[/bold red]")
    t_admin.add_row("Cơ quan bị khiếu kiện", f"[bold yellow]{analysis.get('state_agency_named', 'UBND / Thủ trưởng CQNN')}[/bold yellow]")
    t_admin.add_row("Căn cứ pháp lý chủ đạo", ", ".join(analysis.get("applicable_laws", ["Luật Tố tụng Hành chính 2015"])))
    t_admin.add_row("Định hướng tối ưu", f"[bold green]{analysis.get('recommended_path', 'Khởi kiện TAND')}[/bold green]")
    console.print(t_admin)

    # 2. CHIẾN LƯỢC 2 KÊNH SONG SONG (KHIẾU NẠI VS KHỞI KIỆN)
    t_tracks = Table(title="\n[bold yellow]2. CHIẾN LƯỢC 2 KÊNH BẢO VỆ QUYỀN LỢI (LUẬT KHIẾU NẠI & LUẬT TTHC 2015)[/bold yellow]")
    t_tracks.add_column("Kênh thực thi", style="bold cyan", width=20)
    t_tracks.add_column("Cơ quan có thẩm quyền", style="white", width=25)
    t_tracks.add_column("Thời hiệu luật định", style="magenta", width=16)
    t_tracks.add_column("Ưu điểm & Nhược điểm", style="white")

    t_tracks.add_row(
        "KÊNH 1: KHIẾU NẠI\n(Tiền tố tụng)",
        analysis.get("state_agency_named", "Chủ tịch UBND / Thủ trưởng cấp trên"),
        f"[bold yellow]{analysis.get('time_limit_complaint', '90 ngày')}[/bold yellow]\n(Điều 9 Luật Khiếu nại)",
        "Ưu điểm: Nhanh, không mất án phí.\nNhược điểm: Tỷ lệ tự sửa quyết định thấp.",
    )
    t_tracks.add_row(
        "KÊNH 2: KHỞI KIỆN\n(Tố tụng TAND)",
        "Tòa án nhân dân cấp tỉnh/huyện có thẩm quyền",
        f"[bold green]{analysis.get('time_limit_court', '01 năm')}[/bold green]\n(Điều 116 Luật TTHC 2015)",
        "Ưu điểm: Cơ quan tư pháp độc lập phán quyết, có quyền tuyên hủy QĐHC.\nNhược điểm: Thủ tục tố tụng chặt chẽ.",
    )
    console.print(t_tracks)

    # 3. BIỆN PHÁP KHẨN CẤP TẠM THỜI (ĐIỀU 68 LUẬT TTHC 2015)
    t_urgent = Table(title="\n[bold yellow]3. ĐỀ NGHỊ BIỆN PHÁP KHẨN CẤP TẠM THỜI (ĐIỀU 68 LUẬT TTHC 2015)[/bold yellow]")
    t_urgent.add_column("Biện pháp đề xuất", style="cyan", width=35)
    t_urgent.add_column("Mục đích bảo vệ quyền lợi", style="white")

    urgent_measures = analysis.get("urgent_temporary_measures", [])
    if urgent_measures:
        for m in urgent_measures:
            t_urgent.add_row(m, "Ngăn chặn hậu quả không thể khắc phục được (Điều 68 Luật TTHC 2015)")
    else:
        t_urgent.add_row("Tạm đình chỉ việc thi hành quyết định hành chính", "Tránh việc cưỡng chế gây thiệt hại trước khi Tòa xét xử")
    console.print(t_urgent)

    # 4. Các bước hành động
    actions = analysis.get("action_steps", [])
    if actions:
        t_act = Table(title="\n[bold yellow]4. LỘ TRÌNH THỰC HIỆN TỪNG BƯỚC[/bold yellow]")
        t_act.add_column("Bước", style="cyan", width=8, justify="center")
        t_act.add_column("Nội dung triển khai", style="white")
        for i, a in enumerate(actions, start=1):
            t_act.add_row(f"Bước {i}", a)
        console.print(t_act)


def render_commercial_domain(console: Console, analysis: dict[str, Any]) -> None:
    """Hiển thị toàn diện phân tích Tranh chấp Thương mại, Trần phạt 8% và Trọng tài VIAC."""
    # 1. Bảng tranh chấp thương mại
    t_com = Table(title="[bold yellow]1. TRANH CHẤP KINH DOANH THƯƠNG MẠI & HỢP ĐỒNG[/bold yellow]")
    t_com.add_column("Thuộc tính", style="cyan", width=25)
    t_com.add_column("Thông tin chi tiết", style="white")

    t_com.add_row("Tên tranh chấp", f"[bold green]{analysis.get('dispute_name', 'Tranh chấp hợp đồng thương mại')}[/bold green]")
    t_com.add_row("Giá trị hợp đồng", analysis.get("contract_value_formatted", "2.000.000.000 VNĐ"))
    t_com.add_row("Nghĩa vụ bị vi phạm", analysis.get("breached_obligation_formatted", "2.000.000.000 VNĐ"))
    t_com.add_row("Cơ quan tài phán ưu tiên", f"[bold yellow]{analysis.get('forum_recommendation', 'Trung tâm Trọng tài Quốc tế Việt Nam (VIAC)')}[/bold yellow]")
    console.print(t_com)

    # 2. BẢNG KIỂM SOÁT TRẦN PHẠT VI PHẠM 8% (ĐIỀU 301 LUẬT THƯƠNG MẠI 2005)
    t_pen8 = Table(title="\n[bold yellow]2. KIỂM SOÁT TRẦN PHẠT VI PHẠM THEO ĐIỀU 301 LUẬT THƯƠNG MẠI 2005[/bold yellow]")
    t_pen8.add_column("Chỉ số kiểm soát", style="cyan", width=30)
    t_pen8.add_column("Số tiền tính toán", style="bold", width=25)
    t_pen8.add_column("Căn cứ pháp lý & Cảnh báo", style="white")

    is_within = analysis.get("is_penalty_within_8_percent", True)
    t_pen8.add_row(
        "Mức phạt các bên yêu cầu",
        f"[yellow]{analysis.get('penalty_claim_formatted', '0 VNĐ')}[/yellow]",
        "Theo điều khoản phạt vi phạm trong hợp đồng",
    )
    t_pen8.add_row(
        "Mức phạt tối đa luật định (8%)",
        f"[bold green]{analysis.get('max_legal_penalty_formatted', '0 VNĐ')}[/bold green]",
        "[bold green]Điều 301 Luật Thương mại: Tối đa 8% giá trị phần nghĩa vụ bị vi phạm[/bold green]",
    )

    if not is_within:
        t_pen8.add_row(
            "[bold red]ĐÁNH GIÁ TÍNH HỢP PHÁP[/bold red]",
            "[bold white on red] VƯỢT TRẦN 8% [/bold white on red]",
            "[bold red]CẢNH BÁO: Phần phạt vượt quá 8% BỊ VÔ HIỆU trước Trọng tài/Tòa án. Chỉ được chấp nhận tối đa 8%![/bold red]",
        )
    else:
        t_pen8.add_row(
            "[bold green]ĐÁNH GIÁ TÍNH HỢP PHÁP[/bold green]",
            "[bold white on green] HỢP LỆ (<= 8%) [/bold white on green]",
            "Mức phạt nằm trong hạn mức cho phép của Điều 301 LTM 2005",
        )
    console.print(t_pen8)

    # 3. THỎA THUẬN TRỌNG TÀI & PHÂN ĐỊNH THẨM QUYỀN (ĐIỀU 6 LUẬT TTTM 2010)
    t_arb = Table(title="\n[bold yellow]3. THỎA THUẬN TRỌNG TÀI VIAC (ĐIỀU 6 LUẬT TRỌNG TÀI THƯƠNG MẠI 2010)[/bold yellow]")
    t_arb.add_column("Nội dung thỏa thuận", style="cyan", width=30)
    t_arb.add_column("Kết luận pháp lý", style="white")

    has_arb = analysis.get("arbitration_clause_found", False)
    if has_arb:
        t_arb.add_row(
            "Hiệu lực điều khoản Trọng tài",
            "[bold green]HỢP LỆ VÀ CÓ HIỆU LỰC BẮT BUỘC[/bold green] (Loại trừ thẩm quyền của Tòa án)",
        )
        t_arb.add_row(
            "Thẩm quyền của Tòa án",
            "Nếu một bên khởi kiện tại TAND, Tòa án PHẢI TỪ CHỐI THỤ LÝ theo Điều 6 Luật TTTM 2010",
        )
    else:
        t_arb.add_row("Điều khoản Trọng tài", "Không có thỏa thuận trọng tài. Thẩm quyền thuộc TAND.")
    console.print(t_arb)

    # 4. Lộ trình giải quyết
    steps = analysis.get("suggested_steps", [])
    if steps:
        t_steps = Table(title="\n[bold yellow]4. LỘ TRÌNH GIẢI QUYẾT TRANH CHẤP THƯƠNG MẠI TỐI ƯU[/bold yellow]")
        t_steps.add_column("Bước", style="cyan", width=8, justify="center")
        t_steps.add_column("Nội dung", style="white")
        for i, s in enumerate(steps, start=1):
            t_steps.add_row(f"Bước {i}", s)
        console.print(t_steps)


def render_disciplinary_domain(console: Console, analysis: dict[str, Any]) -> None:
    """Hiển thị toàn diện phân tích Kỷ luật Lao động, 4 Hình thức xử lý và Điều cấm BLLĐ 2019."""
    # 1. Bảng tổng quan kỷ luật
    t_disc = Table(title="[bold yellow]1. KỶ LUẬT LAO ĐỘNG & ĐỐI TƯỢNG BỊ XỬ LÝ (BLLĐ 2019)[/bold yellow]")
    t_disc.add_column("Thuộc tính", style="cyan", width=25)
    t_disc.add_column("Thông tin chi tiết", style="white")

    t_disc.add_row("Hành vi/Sự việc kỷ luật", f"[bold red]{analysis.get('discipline_matter', 'Kỷ luật lao động')}[/bold red]")
    t_disc.add_row("Đối tượng bị xử lý", f"{analysis.get('target_person', 'Người lao động')} ({analysis.get('target_role', 'Người lao động')})")
    t_disc.add_row("Người sử dụng lao động", analysis.get("employer_or_agency", "Doanh nghiệp"))
    t_disc.add_row("Căn cứ pháp lý", ", ".join(analysis.get("applicable_laws", ["Bộ luật Lao động 2019"])))
    console.print(t_disc)

    # 2. 4 HÌNH THỨC KỶ LUẬT LAO ĐỘNG HỢP PHÁP THEO ĐIỀU 124 BLLĐ 2019
    t_4forms = Table(title="\n[bold yellow]2. 4 HÌNH THỨC KỶ LUẬT LAO ĐỘNG HỢP PHÁP (ĐIỀU 124 BLLĐ 2019)[/bold yellow]")
    t_4forms.add_column("STT", style="cyan", width=4, justify="center")
    t_4forms.add_column("Hình thức kỷ luật luật định", style="bold white", width=36)
    t_4forms.add_column("Điều luật BLLĐ", style="magenta", width=14)
    t_4forms.add_column("Điều kiện áp dụng", style="white")

    forms = [
        ("1", "Khiển trách", "Khoản 1 Điều 124", "Vi phạm lần đầu ở mức độ nhẹ"),
        ("2", "Kéo dài thời hạn nâng lương không quá 06 tháng", "Khoản 2 Điều 124", "Tái phạm hoặc vi phạm đã bị khiển trách"),
        ("3", "Cách chức", "Khoản 3 Điều 124", "Áp dụng đối với người lao động giữ chức vụ"),
        ("4", "Sa thải", "Điều 125 BLLĐ", "Trộm cắp, tham ô, tự ý bỏ việc 5 ngày/tháng, tiết lộ bí mật..."),
    ]
    for stt, name, art, cond in forms:
        t_4forms.add_row(stt, name, art, cond)
    console.print(t_4forms)

    # 3. ĐÁNH GIÁ ĐIỀU CẤM & TÍNH HỢP PHÁP
    t_valid = Table(title="\n[bold yellow]3. ĐÁNH GIÁ VI PHẠM ĐIỀU CẤM VÀ TÍNH HỢP PHÁP CỦA KỶ LUẬT[/bold yellow]")
    t_valid.add_column("Nội dung đánh giá", style="cyan", width=30)
    t_valid.add_column("Kết luận pháp lý", style="white")

    is_valid = analysis.get("is_discipline_valid", True)
    if is_valid:
        t_valid.add_row("Tính hợp pháp của Quyết định", "[bold green]HỢP PHÁP[/bold green] (Đúng thẩm quyền và trình tự)")
    else:
        t_valid.add_row(
            "Tính hợp pháp của Quyết định",
            "[bold white on red] TRÁI PHÁP LUẬT NGHIÊM TRỌNG [/bold white on red]",
        )

    violations = analysis.get("procedural_violations", [])
    if violations:
        for v in violations:
            t_valid.add_row("[red]Vi phạm điều cấm[/red]", f"[bold red]• {v}[/bold red]")
    else:
        t_valid.add_row("Vi phạm điều cấm", "Không phát hiện vi phạm điều cấm.")
    console.print(t_valid)

    # 4. QUYỀN LỢI BỒI THƯỜNG THEO ĐIỀU 41 BLLĐ 2019
    t_remedy = Table(title="\n[bold yellow]4. QUYỀN LỢI NGƯỜI LAO ĐỘNG & BỒI THƯỜNG (ĐIỀU 41 BLLĐ 2019)[/bold yellow]")
    t_remedy.add_column("Khoản bồi thường / Khắc phục", style="cyan", width=30)
    t_remedy.add_column("Nội dung bảo đảm quyền lợi", style="bold green")

    t_remedy.add_row(
        "Nhận trở lại làm việc",
        "Buộc người sử dụng lao động phải nhận người lao động trở lại làm việc theo HĐLĐ đã ký",
    )
    t_remedy.add_row(
        "Tiền lương trong thời gian nghỉ",
        "Phải trả đủ tiền lương, đóng BHXH, BHYT, BHTN trong những ngày không được làm việc",
    )
    t_remedy.add_row(
        "Bồi thường thêm ít nhất 02 tháng",
        "Bồi thường thêm cho người lao động một khoản tiền ít nhất bằng 02 tháng tiền lương theo HĐLĐ",
    )
    console.print(t_remedy)
