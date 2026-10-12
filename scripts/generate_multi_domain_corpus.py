"""Script tổng hợp và xuất tập dữ liệu đa lĩnh vực pháp luật Việt Nam (Multi-Domain Legal Corpus).

Bao quát 5 lĩnh vực pháp luật cốt lõi:
1. HÌNH SỰ (Criminal Law - 7 hình phạt chính & 7 hình phạt bổ sung Điều 32 BLHS 2015).
2. DÂN SỰ (Civil Law - Hợp đồng vay, đặt cọc, bồi thường Đ.584, thừa kế, án phí NQ 326).
3. HÀNH CHÍNH (Administrative Law - Khiếu kiện thu hồi đất, xử phạt VPHC, 2 kênh giải quyết LTTHC).
4. THƯƠNG MẠI (Commercial Law - Trần phạt vi phạm 8% Đ.301 LTM, Trọng tài VIAC, bất khả kháng).
5. KỶ LUẬT & LAO ĐỘNG (Disciplinary & Labor Law - 4 hình thức kỷ luật Đ.124 BLLĐ, sa thải trái luật, Đ.41).

Xuất ra:
- data/multi_domain_corpus.jsonl: Tập dữ liệu ChatML đa nhiệm phục vụ fine-tuning LLM.
- data/multi_domain_benchmark.json: Bộ câu hỏi kiểm thử chuẩn đánh giá mô hình.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Đảm bảo đường dẫn gốc của project có trong sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.legal_domains.dispatcher import LegalDomain

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data"

MULTI_DOMAIN_SAMPLES = [
    # =========================================================================
    # 1. HÌNH SỰ (CRIMINAL LAW - ĐIỀU 32 BLHS)
    # =========================================================================
    {
        "id": "crim-01",
        "domain": "criminal",
        "title": "Làm giả CCCD và tổ chức thi hộ chứng chỉ VSTEP",
        "input": (
            "- Bị cáo: N (Nữ sinh viên năm cuối tại TP.HCM, gia đình hoàn cảnh khó khăn, mẹ bệnh nặng, lần đầu phạm tội).\n"
            "- Bị cáo: Hoàng (Người trực tiếp làm giả 2 CCCD gắn chip thu 2.300.000 đồng).\n"
            "- Bị cáo: P (Môi giới liên hệ giữa N và Hoàng).\n"
            "- Bị cáo: M, A (Người nhờ thi hộ).\n\n"
            "Hành vi: N nhận lời thi hộ VSTEP cho M và A, nhờ Hoàng làm 2 CCCD giả dán ảnh N để vào phòng thi. "
            "N thu lợi bất chính 3.050.000 đồng. N đã nộp lại toàn bộ tiền thu lợi bất chính, tích cực hợp tác với cơ quan công an bắt giữ các đối tượng."
        ),
        "expected_law": "Điều 341 Bộ luật Hình sự 2015 (sửa đổi 2017)",
        "expected_penalties": {
            "principal": "Tù có thời hạn từ 2 đến 3 năm (Xem xét cho hưởng Án treo theo Điều 65 BLHS đối với N)",
            "supplementary": "Phạt tiền bổ sung từ 10.000.000 đến 30.000.000 đồng (Khoản 2 Điều 32 & Khoản 3 Điều 341)",
            "judicial_measure": "Tịch thu tiêu hủy 2 CCCD giả; tịch thu nộp ngân sách 3.050.000 đồng (Điều 47 BLHS)",
        },
    },
    {
        "id": "crim-02",
        "domain": "criminal",
        "title": "Cố ý gây thương tích do mâu thuẫn bộc phát",
        "input": (
            "- Bị cáo: Nguyễn Văn An (SN 1995, chưa có tiền án tiền sự).\n"
            "- Bị hại: Trần Quốc Bình (SN 1998, tổn thương cơ thể 35%).\n\n"
            "Hành vi: Do xích mích tại quán ăn, An dùng dao bấm đâm vào vùng vai của anh Bình gây thương tật 35%. "
            "Sau khi gây án, An đã bồi thường 50.000.000 đồng, thành khẩn khai báo và được bị hại xin giảm nhẹ hình phạt."
        ),
        "expected_law": "Điều 134 Khoản 2 Điểm đ Bộ luật Hình sự 2015",
        "expected_penalties": {
            "principal": "Tù có thời hạn từ 2 đến 3 năm (Xem xét cho hưởng án treo)",
            "supplementary": "Không áp dụng",
            "judicial_measure": "Bồi thường dân sự theo Điều 48 BLHS",
        },
    },
    {
        "id": "crim-03",
        "domain": "criminal",
        "title": "Cướp tài sản có tổ chức và vũ khí nguy hiểm",
        "input": (
            "- Bị cáo 1: Hoàng Văn Nam (SN 1990, có 1 tiền án chưa xóa án tích, tái phạm).\n"
            "- Bị cáo 2: Đỗ Văn Tuấn (SN 1994, đồng phạm giúp sức).\n"
            "- Bị hại: Chị Lê Thị Mai (bị cướp xe máy trị giá 35.000.000 đồng).\n\n"
            "Hành vi: Nam và Tuấn mang theo dao bấm chặn đường vắng, đe dọa dùng vũ lực ngay tức khắc để cướp xe máy."
        ),
        "expected_law": "Điều 168 Khoản 2 Bộ luật Hình sự 2015",
        "expected_penalties": {
            "principal": "Tù có thời hạn từ 7 đến 10 năm tù giam (Nam) và 7 đến 8 năm tù giam (Tuấn)",
            "supplementary": "Phạt tiền bổ sung 10 - 20 triệu đồng; Quản chế 01 năm sau khi chấp hành xong án tù (Điều 43 BLHS)",
            "judicial_measure": "Tịch thu tiêu hủy dao bấm (Điều 47 BLHS)",
        },
    },

    # =========================================================================
    # 2. DÂN SỰ (CIVIL LAW & HỢP ĐỒNG, THỪA KẾ)
    # =========================================================================
    {
        "id": "civ-01",
        "domain": "civil",
        "title": "Tranh chấp hợp đồng vay nợ và kiểm soát lãi suất trần 20%",
        "input": (
            "Nguyên đơn: Bà Lê Thị Mai.\n"
            "Bị đơn: Ông Nguyễn Văn Hùng.\n\n"
            "Nội dung: Ngày 10/01/2023, bà Mai cho ông Hùng vay số tiền 800.000.000 đồng theo Giấy biên nhận vay tiền, "
            "thời hạn vay 06 tháng, lãi suất thỏa thuận 30%/năm. Hết hạn, ông Hùng không trả cả nợ gốc và nợ lãi. "
            "Bà Mai khởi kiện yêu cầu ông Hùng trả toàn bộ 800 triệu đồng gốc và tiền lãi tính theo mức 30%/năm."
        ),
        "expected_law": "Điều 463, Điều 466, Điều 468 Bộ luật Dân sự 2015",
        "dispute_resolution": {
            "interest_cap_rule": "Điều 468 BLDS: Lãi suất trần tối đa 20%/năm. Mức lãi 30%/năm vượt quá 10%/năm, phần lãi vượt trần bị vô hiệu.",
            "court_fee_estimate": "36.000.000 đồng (án phí sơ thẩm có giá ngạch theo Nghị quyết 326/2016/UBTVQH14)",
            "recommended_steps": "Thương lượng -> Hòa giải tiền tố tụng tại Tòa án -> Khởi kiện tại TAND cấp huyện nơi bị đơn cư trú",
        },
    },
    {
        "id": "civ-02",
        "domain": "civil",
        "title": "Tranh chấp chia di sản thừa kế quyền sử dụng đất",
        "input": (
            "Nguyên đơn: Ông Trần Văn A (con trưởng).\n"
            "Bị đơn: Bà Trần Thị B (con thứ).\n\n"
            "Nội dung: Cha mẹ mất năm 2018 không để lại di chúc. Di sản thừa kế là thửa đất diện tích 300m2 tại Huyện C "
            "do cha mẹ đứng tên Giấy chứng nhận quyền sử dụng đất. Bà B tự ý xây nhà và canh tác trên toàn bộ thửa đất, "
            "từ chối phân chia di sản cho các đồng thừa kế khác."
        ),
        "expected_law": "Điều 609, Điều 612, Điều 623, Điều 651 Bộ luật Dân sự 2015",
        "dispute_resolution": {
            "statute_of_limitations": "Thời hiệu khởi kiện chia thừa kế bất động sản là 30 năm kể từ thời điểm mở thừa kế (năm 2018).",
            "recommended_steps": "Hòa giải tại UBND xã/phường (thủ tục hòa giải tranh chấp đất đai) -> Khởi kiện phân chia di sản theo pháp luật tại TAND cấp tỉnh/huyện",
        },
    },

    # =========================================================================
    # 3. HÀNH CHÍNH & TRANH CHẤP CƠ QUAN NHÀ NƯỚC (ADMINISTRATIVE LAW)
    # =========================================================================
    {
        "id": "adm-01",
        "domain": "administrative",
        "title": "Khiếu kiện Quyết định thu hồi đất và bồi thường GPMB của UBND",
        "input": (
            "Người khởi kiện: Hộ gia đình ông Đặng Văn Nam.\n"
            "Người bị kiện: Ủy ban nhân dân và Chủ tịch UBND Quận K, TP.Đà Nẵng.\n\n"
            "Nội dung: Ngày 15/08/2023, Chủ tịch UBND Quận K ban hành Quyết định thu hồi đất số 1234/QĐ-UBND và Quyết định phê duyệt "
            "phương án bồi thường, hỗ trợ tái định cư với mức giá bồi thường 5.000.000 đồng/m2 trong khi giá thị trường là 25.000.000 đồng/m2. "
            "Đồng thời, UBND ban hành Quyết định cưỡng chế thu hồi đất khi chưa giải quyết xong khiếu nại của công dân."
        ),
        "expected_law": "Luật Tố tụng Hành chính 2015, Luật Đất đai, Luật Khiếu nại 2011",
        "dispute_resolution": {
            "two_track_strategy": "Kênh 1: Khiếu nại lần 1 đến Chủ tịch UBND quận (90 ngày) | Kênh 2: Khởi kiện trực tiếp vụ án hành chính tại TAND cấp tỉnh/huyện (01 năm)",
            "urgent_temporary_measure": "Đề nghị Tòa án áp dụng BPKCTT: 'Tạm đình chỉ việc thi hành quyết định cưỡng chế thu hồi đất' (Khoản 1 Điều 68 Luật TTHC 2015)",
        },
    },
    {
        "id": "adm-02",
        "domain": "administrative",
        "title": "Khiếu kiện Quyết định xử phạt vi phạm hành chính vượt thẩm quyền",
        "input": (
            "Người khởi kiện: Công ty Cổ phần Thương mại Alpha.\n"
            "Người bị kiện: Đội trưởng Đội Quản lý thị trường số 3.\n\n"
            "Nội dung: Đội trưởng Đội QLTT số 3 ban hành Quyết định xử phạt vi phạm hành chính số 89/QĐ-XPHC phạt tiền 80.000.000 đồng "
            "và tịch thu toàn bộ lô hàng hóa trị giá 200.000.000 đồng. Công ty Alpha cho rằng mức phạt này vượt quá thẩm quyền xử phạt "
            "của Đội trưởng theo Luật Xử lý vi phạm hành chính (thẩm quyền tối đa của Đội trưởng là 25.000.000 đồng)."
        ),
        "expected_law": "Điều 45 Luật Xử lý vi phạm hành chính 2012 (sửa đổi 2020), Luật TTHC 2015",
        "dispute_resolution": {
            "jurisdiction_violation": "Vi phạm nghiêm trọng về thẩm quyền xử phạt theo Luật XLVPHC. Quyết định hành chính có căn cứ bị tuyên hủy toàn bộ.",
            "action_steps": "Khởi kiện yêu cầu TAND tuyên hủy Quyết định số 89/QĐ-XPHC và bồi thường thiệt hại thực tế do giữ hàng hóa trái luật.",
        },
    },

    # =========================================================================
    # 4. KINH DOANH THƯƠNG MẠI & TRỌNG TÀI (COMMERCIAL LAW & VIAC)
    # =========================================================================
    {
        "id": "com-01",
        "domain": "commercial",
        "title": "Tranh chấp phạt vi phạm vượt mức trần 8% theo Điều 301 Luật Thương mại",
        "input": (
            "Nguyên đơn: Công ty Cổ phần Đầu tư Công nghệ Hoàng Long.\n"
            "Bị đơn: Công ty TNHH Thiết bị Công nghiệp Việt Nhật.\n\n"
            "Nội dung: Hai bên ký Hợp đồng mua bán thiết bị máy móc số 05/HĐMB trị giá 2.000.000.000 đồng. "
            "Bên bán giao hàng chậm tiến độ 15 ngày. Điều 8 của Hợp đồng quy định: 'Bên vi phạm tiến độ giao hàng phải chịu phạt 15% tổng giá trị hợp đồng'. "
            "Bên mua yêu cầu bên bán nộp phạt số tiền 300.000.000 đồng. Hai bên có điều khoản chọn Trọng tài VIAC giải quyết."
        ),
        "expected_law": "Điều 300, Điều 301 Luật Thương mại 2005; Luật Trọng tài Thương mại 2010",
        "dispute_resolution": {
            "statutory_ceiling_rule": "Điều 301 LTM: Mức phạt vi phạm do các bên thỏa thuận nhưng không quá 8% giá trị phần nghĩa vụ hợp đồng bị vi phạm (tương đương tối đa 160.000.000 đồng). Phần yêu cầu 140.000.000 đồng vượt quá 8% là vô hiệu.",
            "arbitration_priority": "Có thỏa thuận trọng tài VIAC có hiệu lực, Tòa án phải từ chối thụ lý theo Điều 6 Luật Trọng tài Thương mại 2010.",
        },
    },
    {
        "id": "com-02",
        "domain": "commercial",
        "title": "Tranh chấp sự kiện bất khả kháng và miễn trách nhiệm thương mại",
        "input": (
            "Nguyên đơn: Công ty Cổ phần Xuất nhập khẩu Thủy sản Biển Đông.\n"
            "Bị đơn: Doanh nghiệp Vận tải Biển Đại Dương.\n\n"
            "Nội dung: Hợp đồng vận chuyển 50 tấn thủy sản đông lạnh từ Cần Thơ đi Hải Phòng. Trên đường vận chuyển, "
            "tàu gặp bão lớn số 5 làm hỏng hệ thống lạnh dẫn đến toàn bộ hàng hóa hư hỏng. Bên vận tải viện dẫn Điều 294 Luật Thương mại "
            "về Sự kiện bất khả kháng để từ chối bồi thường 1.500.000.000 đồng."
        ),
        "expected_law": "Điều 294, Điều 295 Luật Thương mại 2005; Điều 156 Bộ luật Dân sự 2015",
        "dispute_resolution": {
            "force_majeure_assessment": "Bên vi phạm phải thông báo ngay bằng văn bản cho bên kia về trường hợp miễn trách nhiệm và thực hiện mọi biện pháp hợp lý để hạn chế tổn thất (Điều 295 LTM). Nếu không thông báo kịp thời, vẫn phải bồi thường.",
        },
    },

    # =========================================================================
    # 5. KỶ LUẬT & LAO ĐỘNG (LABOR & DISCIPLINARY LAW)
    # =========================================================================
    {
        "id": "disc-01",
        "domain": "disciplinary",
        "title": "Sa thải trái pháp luật đối với lao động nữ đang mang thai",
        "input": (
            "Người khiếu nại: Chị Nguyễn Thị Hương (Chuyên viên Nhân sự).\n"
            "Người bị khiếu nại: Công ty TNHH May mặc Tân Tiến.\n\n"
            "Nội dung: Chị Hương đang mang thai tháng thứ 5 (có giấy khám thai của bệnh viện). Do sức khỏe yếu, "
            "chị Hương có 03 ngày nghỉ việc đi khám bệnh có nộp đơn nhưng chưa được Trưởng phòng duyệt. "
            "Ngày 20/09/2023, Giám đốc công ty ra Quyết định sa thải chị Hương với lý do tự ý bỏ việc 03 ngày liên tục."
        ),
        "expected_law": "Điều 122, Điều 124, Điều 125, Điều 137 Bộ luật Lao động 2019",
        "dispute_resolution": {
            "illegality": "Vi phạm nghiêm trọng Khoản 4 Điều 122 & Khoản 3 Điều 137 BLLĐ: Nghiêm cấm xử lý kỷ luật và sa thải lao động nữ đang mang thai.",
            "compensation_rights": "Áp dụng Điều 41 BLLĐ: Buộc nhận lại làm việc, trả đủ lương những ngày không được làm việc + bồi thường thêm ít nhất 02 tháng tiền lương.",
        },
    },
    {
        "id": "disc-02",
        "domain": "disciplinary",
        "title": "Phạt tiền, trừ 50% lương tháng vi phạm điều cấm Điều 127 BLLĐ",
        "input": (
            "Người lao động: Anh Lê Văn Hùng (Công nhân vận hành máy).\n"
            "Doanh nghiệp: Công ty Cổ phần Cơ khí Chế tạo Máy Việt Hàn.\n\n"
            "Nội dung: Trong ca làm việc ngày 12/07/2023, anh Hùng thao tác sai quy trình làm hỏng linh kiện máy trị giá 3.000.000 đồng. "
            "Giám đốc công ty ban hành Thông báo kỷ luật trừ 50% tiền lương tháng 7/2023 của anh Hùng để phạt vi phạm kỷ luật lao động."
        ),
        "expected_law": "Điều 127, Điều 129 Bộ luật Lao động 2019",
        "dispute_resolution": {
            "statutory_prohibition": "Khoản 2 Điều 127 BLLĐ: Nghiêm cấm dùng hình thức phạt tiền, cắt lương thay việc xử lý kỷ luật lao động. Việc trừ lương phạt vi phạm là hoàn toàn trái luật.",
            "legal_remedy": "Công ty phải hoàn trả lại toàn bộ số tiền lương đã trừ trái phép; nếu có thiệt hại tài sản chỉ được xử lý trách nhiệm vật chất theo Điều 129 BLLĐ (khấu trừ không quá 30% tiền lương tháng sau khi đóng BHXH, thuế).",
        },
    },
]


def generate_chatml_entry(sample: dict[str, Any]) -> dict[str, Any]:
    """Chuyển đổi mẫu hồ sơ thành định dạng ChatML tiêu chuẩn cho SFT."""
    domain_name_vi = {
        "criminal": "Pháp luật Hình sự (Bộ luật Hình sự 2015)",
        "civil": "Pháp luật Dân sự & Hợp đồng (Bộ luật Dân sự 2015)",
        "administrative": "Pháp luật Hành chính & Tranh chấp với CQNN (Luật TTHC 2015)",
        "commercial": "Pháp luật Kinh doanh Thương mại & Trọng tài (Luật Thương mại 2005)",
        "disciplinary": "Pháp luật Kỷ luật & Lao động (Bộ luật Lao động 2019)",
    }.get(sample["domain"], "Pháp luật Việt Nam")

    system_prompt = (
        "Bạn là Trợ lý AI Chuyên gia Pháp lý Tối cao Việt Nam. Nhiệm vụ của bạn là phân tích toàn diện, "
        "xác định quan hệ pháp luật, viện dẫn chính xác văn bản quy phạm pháp luật, đánh giá chế tài "
        "và đề xuất lộ trình giải quyết tranh chấp tối ưu, tuân thủ nghiêm ngặt các nguyên tắc pháp định."
    )

    user_prompt = (
        f"Hãy phân tích vụ việc sau đây trong lĩnh vực {domain_name_vi}:\n\n"
        f"Tiêu đề: {sample['title']}\n"
        f"Nội dung vụ việc:\n{sample['input']}\n\n"
        f"Yêu cầu:\n"
        f"1. Xác định quan hệ pháp luật và điều luật áp dụng chuẩn xác.\n"
        f"2. Đánh giá tính hợp pháp, chế tài hoặc mức hình phạt áp dụng (nếu là hình sự: áp dụng đầy đủ Điều 32 BLHS gồm 7 hình phạt chính và 7 hình phạt bổ sung).\n"
        f"3. Đề xuất lộ trình giải quyết tranh chấp tối ưu từng bước."
    )

    # Xây dựng câu trả lời trợ lý chi tiết
    if sample["domain"] == "criminal":
        assistant_reply = (
            f"### 1. QUAN HỆ PHÁP LUẬT VÀ ĐIỀU LUẬT ÁP DỤNG\n"
            f"- Tội danh và Căn cứ: {sample['expected_law']}\n"
            f"- Phân tích cấu thành: Thỏa mãn đầy đủ khách thể, khách quan, chủ quan và chủ thể tội phạm.\n\n"
            f"### 2. HỆ THỐNG HÌNH PHẠT ÁP DỤNG THEO ĐIỀU 32 BLHS 2015\n"
            f"- **A. Hình phạt chính (Khoản 1 Điều 32)**: {sample['expected_penalties']['principal']}.\n"
            f"- **B. Hình phạt bổ sung (Khoản 2 Điều 32)**: {sample['expected_penalties']['supplementary']}.\n"
            f"- **C. Biện pháp tư pháp (Điều 46 - 48 BLHS)**: {sample['expected_penalties']['judicial_measure']}.\n"
            f"- **Cá thể hóa hình phạt**: Đánh giá nhân thân, vai trò thực hành vs giúp sức, tình tiết giảm nhẹ theo Điều 51 (nộp lại tiền, thành khẩn khai báo) và Điều 54 (dưới mức thấp nhất của khung)."
        )
    else:
        dispute_res = sample.get("dispute_resolution", {})
        assistant_reply = (
            f"### 1. QUAN HỆ PHÁP LUẬT VÀ CĂN CỨ ÁP DỤNG\n"
            f"- Căn cứ pháp luật: {sample['expected_law']}\n"
            f"- Thẩm quyền giải quyết: Tòa án nhân dân hoặc Hội đồng Trọng tài Thương mại.\n\n"
            f"### 2. ĐÁNH GIÁ PHÁP LÝ & QUY TẮC PHÁP ĐỊNH BẮT BUỘC\n"
            + "\n".join([f"- **{k.replace('_', ' ').title()}**: {v}" for k, v in dispute_res.items()]) + "\n\n"
            "### 3. LỘ TRÌNH GIẢI QUYẾT TRANH CHẤP TỐI ƯU\n"
            "- Bước 1: Thu thập toàn bộ chứng cứ tài liệu, hợp đồng, chứng từ thanh toán, quyết định hành chính.\n"
            "- Bước 2: Tiến hành thương lượng, đối thoại hoặc khiếu nại theo thời hiệu luật định.\n"
            "- Bước 3: Nộp đơn yêu cầu giải quyết tại cơ quan tài phán có thẩm quyền và yêu cầu áp dụng các biện pháp bảo vệ quyền lợi hợp pháp."
        )

    return {
        "id": sample["id"],
        "domain": sample["domain"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": assistant_reply},
        ],
    }


def main() -> None:
    """Tạo file corpus và benchmark đa lĩnh vực."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    jsonl_path = OUTPUT_DIR / "multi_domain_corpus.jsonl"
    bench_path = OUTPUT_DIR / "multi_domain_benchmark.json"

    # 1. Ghi file JSONL ChatML
    chatml_records = [generate_chatml_entry(s) for s in MULTI_DOMAIN_SAMPLES]
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for rec in chatml_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # 2. Ghi file Benchmark JSON
    benchmark_data = {
        "version": "1.0.0",
        "description": "Bộ benchmark kiểm thử đa lĩnh vực pháp luật Việt Nam (Criminal, Civil, Administrative, Commercial, Disciplinary)",
        "domains_covered": [d.value for d in LegalDomain],
        "total_cases": len(MULTI_DOMAIN_SAMPLES),
        "cases": MULTI_DOMAIN_SAMPLES,
    }
    with open(bench_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_data, f, ensure_ascii=False, indent=2)

    print(f"Đã xuất thành công {len(MULTI_DOMAIN_SAMPLES)} hồ sơ đa lĩnh vực:")
    print(f" - ChatML Corpus: {jsonl_path}")
    print(f" - Benchmark JSON: {bench_path}")


if __name__ == "__main__":
    main()
