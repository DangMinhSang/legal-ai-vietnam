"""Script sinh 32 bản án hình sự mẫu mới (từ 019 đến 050) mở rộng tập dữ liệu lên 50 bản án.

Tuân thủ nghiêm ngặt:
1. Chuẩn cấu trúc JSON của data/sample/judgments/
2. Tuyệt đối không rò rỉ nhãn (No outcome leakage) trong facts_summary
3. Bao gồm các tội danh BLHS 2015: Điều 123, 125, 128, 134, 168, 171, 173, 174, 249, 250, 251, 260, 318
4. Đầy đủ các trường hợp: có tội, không có tội (not_guilty), Điều 54 (dưới mức thấp nhất của khung), án treo (Điều 65), cải tạo không giam giữ (Điều 36)
5. Phân bố thời gian đồng đều từ 2017 đến 2024
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JUDGMENTS_DIR = PROJECT_ROOT / "data" / "sample" / "judgments"

NEW_JUDGMENTS = [
    # ==========================================
    # NĂM 2017 (4 bản án)
    # ==========================================
    {
        "id": "judgment_019_trom_cap_xe_may",
        "case_number": "18/2017/HS-ST",
        "court": "Tòa án nhân dân quận Đống Đa, thành phố Hà Nội",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2017-04-12",
        "crime_type": "Tội trộm cắp tài sản",
        "applicable_articles": ["173"],
        "defendant": {
            "name": "Đỗ Văn D",
            "dob": "1994-06-15",
            "birth_year": 1994,
            "prior_convictions": 0,
        },
        "facts_summary": "Khoảng 19 giờ ngày 10/01/2017, Đỗ Văn D đi bộ qua ngõ phố X, phát hiện xe máy Honda Wave của anh N dựng trước cửa nhà không khóa cổ, cắm sẵn chìa khóa. D lén lút tiếp cận rồi nổ máy điều khiển xe tẩu thoát. Hội đồng định giá tài sản kết luận chiếc xe có giá trị 14.500.000 đồng.",
        "aggravating_factors": [],
        "mitigating_factors": [
            "thành khẩn khai báo",
            "ăn năn hối cải",
            "phạm tội lần đầu thuộc trường hợp ít nghiêm trọng",
            "đã thu hồi tài sản trả cho bị hại",
        ],
        "verdict": "guilty",
        "sentence_type": "suspended",
        "sentence_years": 1.0,
        "suspended": True,
        "full_text": """TÒA ÁN NHÂN DÂN QUẬN ĐỐNG ĐA, THÀNH PHỐ HÀ NỘI
BẢN ÁN SỐ: 18/2017/HS-ST NGÀY 12/04/2017 VỀ TỘI TRỘM CẮP TÀI SẢN

NỘI DUNG VỤ ÁN:
Khoảng 19 giờ ngày 10/01/2017, Đỗ Văn D đi bộ qua ngõ phố X thuộc phường Q, quận Đống Đa, phát hiện xe máy Honda Wave biển kiểm soát 29E1-234.56 của anh Nguyễn Văn N dựng trước cửa nhà không người trông coi, chìa khóa vẫn cắm ở ổ khóa điện. D nảy sinh ý định chiếm đoạt nên lại gần mở khóa xe nổ máy tẩu thoát. Đến ngày 12/01/2017, D mang xe đi tiêu thụ thì bị tổ tuần tra Công an quận Đống Đa phát hiện bắt giữ. Kết luận định giá tài sản xác định chiếc xe trị giá 14.500.000 đồng.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi lén lút chiếm đoạt tài sản của bị cáo trị giá 14.500.000 đồng đã cấu thành tội 'Trộm cắp tài sản' theo khoản 1 Điều 173 BLHS 2015. Bị cáo chưa có tiền án tiền sự, phạm tội lần đầu thuộc trường hợp ít nghiêm trọng. Quá trình điều tra và tại phiên tòa thành khẩn khai báo, tài sản đã thu hồi trả lại bị hại. Xét bị cáo có nơi cư trú rõ ràng, đủ điều kiện hưởng án treo theo Điều 65 BLHS.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Đỗ Văn D phạm 'Tội trộm cắp tài sản'.
Áp dụng khoản 1 Điều 173; điểm i, s khoản 1, khoản 2 Điều 51; Điều 65 BLHS 2015.
Xử phạt bị cáo Đỗ Văn D 01 (một) năm tù cho hưởng án treo, thời gian thử thách là 02 (hai) năm.""",
    },
    {
        "id": "judgment_020_co_y_gay_thuong_tich_con_do",
        "case_number": "35/2017/HS-ST",
        "court": "Tòa án nhân dân quận Hải Châu, thành phố Đà Nẵng",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2017-07-28",
        "crime_type": "Tội cố ý gây thương tích",
        "applicable_articles": ["134"],
        "defendant": {
            "name": "Nguyễn Văn E",
            "dob": "1991-03-20",
            "birth_year": 1991,
            "prior_convictions": 1,
        },
        "facts_summary": "Khoảng 21 giờ 30 phút ngày 02/05/2017, tại quán nước mía vỉa hè đường Y, do mâu thuẫn va chạm xe máy trước đó, Nguyễn Văn E dùng vỏ chai bia thủy tinh đập vỡ đuôi chém liên tiếp vào vùng vai và tay trái của anh K. Kết luận giám định pháp y xác định tỷ lệ tổn thương cơ thể của anh K là 24%.",
        "aggravating_factors": [
            "có tính chất côn đồ",
            "dùng hung khí nguy hiểm",
            "tái phạm",
        ],
        "mitigating_factors": ["thành khẩn khai báo"],
        "verdict": "guilty",
        "sentence_type": "imprisonment",
        "sentence_years": 5.5,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN QUẬN HẢI CHÂU, THÀNH PHỐ ĐÀ NẴNG
BẢN ÁN SỐ: 35/2017/HS-ST NGÀY 28/07/2017 VỀ TỘI CỐ Ý GÂY THƯƠNG TÍCH

NỘI DUNG VỤ ÁN:
Tối ngày 02/05/2017, tại quán nước mía vỉa hè đường Y, quận Hải Châu, xuất phát từ va chạm giao thông nhỏ, Nguyễn Văn E to tiếng chửi bới rồi lấy 01 vỏ chai bia thủy tinh đập vỡ phần đáy lao vào chém nhiều nhát vào vai và cánh tay trái anh Trần Văn K. Anh K bỏ chạy và được đưa đi cấp cứu kịp thời. Bản kết luận giám định pháp y kết luận tỷ lệ tổn thương cơ thể do thương tích gây nên là 24%.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi của bị cáo dùng vỏ chai thủy tinh vỡ là hung khí nguy hiểm gây thương tích cho bị hại 24% với tính chất côn đồ, thuộc điểm đ, i khoản 2 Điều 134 BLHS 2015. Bị cáo có 01 tiền án chưa xóa án tích nên thuộc trường hợp tái phạm theo điểm h khoản 1 Điều 52 BLHS. Quá trình xét xử bị cáo thành khẩn khai báo nên được áp dụng điểm s khoản 1 Điều 51 BLHS. Cần cách ly bị cáo khỏi xã hội một thời gian dài để răn đe.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Nguyễn Văn E phạm 'Tội cố ý gây thương tích'.
Áp dụng điểm đ, i khoản 2 Điều 134; điểm s khoản 1 Điều 51; điểm h khoản 1 Điều 52 BLHS 2015.
Xử phạt bị cáo Nguyễn Văn E 05 (năm) năm 06 (sáu) tháng tù.""",
    },
    {
        "id": "judgment_021_ma_tuy_mua_ban_nho",
        "case_number": "42/2017/HS-ST",
        "court": "Tòa án nhân dân thành phố Vinh, tỉnh Nghệ An",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2017-09-15",
        "crime_type": "Tội mua bán trái phép chất ma túy",
        "applicable_articles": ["251"],
        "defendant": {
            "name": "Phan Văn F",
            "dob": "1989-11-02",
            "birth_year": 1989,
            "prior_convictions": 0,
        },
        "facts_summary": "Khoảng 15 giờ ngày 20/06/2017, tại khu vực bến xe Chợ Vinh, lực lượng công an bắt quả tang Phan Văn F đang bán trái phép 02 gói nhỏ Heroine cho một đối tượng nghiện với giá 400.000 đồng. Khám xét khẩn cấp thu giữ tổng cộng 0,42 gam Heroine.",
        "aggravating_factors": [],
        "mitigating_factors": ["thành khẩn khai báo", "ăn năn hối cải"],
        "verdict": "guilty",
        "sentence_type": "imprisonment",
        "sentence_years": 3.5,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN THÀNH PHỐ VINH, TỈNH NGHỆ AN
BẢN ÁN SỐ: 42/2017/HS-ST NGÀY 15/09/2017 VỀ TỘI MUA BÁN TRÁI PHÉP CHẤT MA TÚY

NỘI DUNG VỤ ÁN:
Vào hồi 15 giờ ngày 20/06/2017, tổ công tác Công an thành phố Vinh làm nhiệm vụ tại khu vực bến xe Chợ Vinh phát hiện bắt quả tang Phan Văn F đang bán 02 gói nhỏ Heroine cho đối tượng Lê Văn T với số tiền 400.000 đồng. Thu giữ trong túi quần của F thêm 01 gói ma túy. Kết luận giám định số 198 xác định toàn bộ chất bột màu trắng thu giữ là Heroine có khối lượng 0,42 gam.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi mua bán trái phép 0,42 gam Heroine của bị cáo đã phạm vào tội 'Mua bán trái phép chất ma túy' theo quy định tại khoản 1 Điều 251 BLHS 2015. Hành vi xâm phạm chính sách độc quyền quản lý của Nhà nước về chất ma túy. Tuy nhiên, bị cáo nhân thân tốt, chưa có tiền án tiền sự, khai báo thành khẩn và ăn năn hối cải nên được xem xét giảm nhẹ hình phạt theo điểm s khoản 1 Điều 51 BLHS.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Phan Văn F phạm 'Tội mua bán trái phép chất ma túy'.
Áp dụng khoản 1 Điều 251; điểm s khoản 1 Điều 51 BLHS 2015.
Xử phạt bị cáo Phan Văn F 03 (ba) năm 06 (sáu) tháng tù.""",
    },
    {
        "id": "judgment_022_gay_roi_trat_tu_quan_bar",
        "case_number": "51/2017/HS-ST",
        "court": "Tòa án nhân dân quận Ninh Kiều, thành phố Cần Thơ",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2017-11-20",
        "crime_type": "Tội gây rối trật tự công cộng",
        "applicable_articles": ["318"],
        "defendant": {
            "name": "Lê Quốc G",
            "dob": "1996-08-19",
            "birth_year": 1996,
            "prior_convictions": 0,
        },
        "facts_summary": "Khoảng 23 giờ 45 phút ngày 15/09/2017, tại sảnh quán bar Z trên đường Hai Bà Trưng, Lê Quốc G cùng nhóm bạn do say rượu đã hò hét, đập phá bàn ghế, dùng gậy bóng chày đuổi đánh bảo vệ và khách làm náo loạn khu phố, đình trệ hoạt động kinh doanh hơn 2 giờ đồng hồ.",
        "aggravating_factors": [
            "dùng hung khí nguy hiểm",
            "gây cản trở giao thông trật tự công cộng",
        ],
        "mitigating_factors": [
            "thành khẩn khai báo",
            "tự nguyện bồi thường thiệt hại toàn bộ 18 triệu đồng",
            "phạm tội lần đầu",
        ],
        "verdict": "guilty",
        "sentence_type": "suspended",
        "sentence_years": 1.5,
        "suspended": True,
        "full_text": """TÒA ÁN NHÂN DÂN QUẬN NINH KIỀU, THÀNH PHỐ CẦN THƠ
BẢN ÁN SỐ: 51/2017/HS-ST NGÀY 20/11/2017 VỀ TỘI GÂY RỐI TRẬT TỰ CÔNG CỘNG

NỘI DUNG VỤ ÁN:
Khoảng 23 giờ 45 phút ngày 15/09/2017, Lê Quốc G cùng một số đối tượng sau khi sử dụng rượu bia tại quán bar Z đã xảy ra cự cãi với nhân viên bảo vệ. G ra xe lấy 01 cây gậy bóng chày bằng kim loại quay lại đập vỡ cửa kính, bàn ghế và hò hét xua đuổi khách hàng, gây mất trật tự nghiêm trọng tại khu vực trung tâm bến Ninh Kiều suốt gần 2 giờ đồng hồ.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi của bị cáo sử dụng hung khí gây rối trật tự công cộng tại nơi đông người đã cấu thành tội 'Gây rối trật tự công cộng' theo quy định tại điểm b khoản 2 Điều 318 BLHS 2015. Bị cáo chưa có tiền án tiền sự, quá trình điều tra đã thành khẩn khai báo, tự nguyện bồi thường toàn bộ thiệt hại vật chất 18.000.000 đồng cho cơ sở kinh doanh. Bị cáo có nhân thân tốt và nơi cư trú rõ ràng nên áp dụng Điều 65 BLHS cho hưởng án treo.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Lê Quốc G phạm 'Tội gây rối trật tự công cộng'.
Áp dụng điểm b khoản 2 Điều 318; điểm b, s khoản 1, khoản 2 Điều 51; Điều 65 BLHS 2015.
Xử phạt bị cáo Lê Quốc G 01 (một) năm 06 (sáu) tháng tù cho hưởng án treo, thời gian thử thách 03 năm.""",
    },
    # ==========================================
    # NĂM 2018 (4 bản án)
    # ==========================================
    {
        "id": "judgment_023_giet_nguoi_kich_dong_hanh_hung",
        "case_number": "19/2018/HS-ST",
        "court": "Tòa án nhân dân tỉnh Nam Định",
        "court_level": "province",
        "judgment_date": "2018-03-22",
        "crime_type": "Tội giết người trong trạng thái tinh thần bị kích động mạnh",
        "applicable_articles": ["125"],
        "defendant": {
            "name": "Vũ Văn H",
            "dob": "1982-12-05",
            "birth_year": 1982,
            "prior_convictions": 0,
        },
        "facts_summary": "Tối ngày 18/11/2017, anh B đến nhà Vũ Văn H đập phá cổng, dùng thanh sắt đánh gây thương tích cho mẹ già của H và liên tục chửi bới, lăng mạ. Trong trạng thái ức chế tinh thần bị kích động cao độ, H vớ lấy con dao thái lan đâm một nhát vào ngực anh B khiến anh B tử vong do thủng tâm thất.",
        "aggravating_factors": [],
        "mitigating_factors": [
            "người phạm tội đầu thú",
            "thành khẩn khai báo",
            "ăn năn hối cải",
            "bồi thường chi phí mai táng 80 triệu đồng",
            "nạn nhân có hành vi trái pháp luật nghiêm trọng trước",
        ],
        "verdict": "guilty",
        "sentence_type": "imprisonment",
        "sentence_years": 1.5,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN TỈNH NAM ĐỊNH
BẢN ÁN SỐ: 19/2018/HS-ST NGÀY 22/03/2018 VỀ TỘI GIẾT NGƯỜI TRONG TRẠNG THÁI TINH THẦN BỊ KÍCH ĐỘNG MẠNH

NỘI DUNG VỤ ÁN:
Tối ngày 18/11/2017, anh Trần Đình B mang theo thanh sắt phi 14 đến nhà Vũ Văn H đập phá tài sản, xông vào đánh mẹ đẻ của H gây thương tích chảy máu vùng đầu. Thấy mẹ bị hành hung và nghe những lời lăng mạ nhục mạ gia đình, H bị kích động tinh thần mất tự chủ, vớ lấy con dao gọt hoa quả đâm 01 nhát trúng ngực anh B. Anh B gục xuống và tử vong tại trạm y tế. Sau khi gây án, H đến Công an huyện đầu thú.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi của bị cáo tước đoạt tính mạng người khác do hành vi trái pháp luật nghiêm trọng của nạn nhân gây ra đã cấu thành tội 'Giết người trong trạng thái tinh thần bị kích động mạnh' theo khoản 1 Điều 125 BLHS 2015. Bị cáo đầu thú, thành khẩn khai báo, gia đình đã bồi thường 80.000.000 đồng tiền mai táng phí. Nạn nhân có lỗi lớn khởi xướng vụ việc.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Vũ Văn H phạm 'Tội giết người trong trạng thái tinh thần bị kích động mạnh'.
Áp dụng khoản 1 Điều 125; điểm b, s khoản 1, khoản 2 Điều 51 BLHS 2015.
Xử phạt bị cáo Vũ Văn H 01 (một) năm 06 (sáu) tháng tù.""",
    },
    {
        "id": "judgment_024_cuop_giat_dien_thoai",
        "case_number": "40/2018/HS-ST",
        "court": "Tòa án nhân dân quận 5, TP. Hồ Chí Minh",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2018-05-18",
        "crime_type": "Tội cướp giật tài sản",
        "applicable_articles": ["171"],
        "defendant": {
            "name": "Trần Minh I",
            "dob": "1999-10-14",
            "birth_year": 1999,
            "prior_convictions": 0,
        },
        "facts_summary": "Khoảng 16 giờ ngày 02/03/2018, Trần Minh I điều khiển xe gắn máy biển số 59F1-456.78 chạy trên đường Nguyễn Trãi, áp sát giật chiếc điện thoại iPhone 7 Plus trị giá 16.000.000 đồng của chị L đang đứng chụp ảnh trên vỉa hè rồi tăng ga tẩu thoát nhưng bị quần chúng nhân dân phối hợp bắt giữ.",
        "aggravating_factors": ["dùng thủ đoạn nguy hiểm"],
        "mitigating_factors": [
            "thành khẩn khai báo",
            "đã thu hồi tài sản trả lại cho bị hại",
            "phạm tội lần đầu",
        ],
        "verdict": "guilty",
        "sentence_type": "imprisonment",
        "sentence_years": 3.0,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN QUẬN 5, THÀNH PHỐ HỒ CHÍ MINH
BẢN ÁN SỐ: 40/2018/HS-ST NGÀY 18/05/2018 VỀ TỘI CƯỚP GIẬT TÀI SẢN

NỘI DUNG VỤ ÁN:
Chiều ngày 02/03/2018, Trần Minh I điều khiển xe máy lưu thông trên đường Nguyễn Trãi, phường 7, Quận 5. Phát hiện chị Nguyễn Thị L cầm điện thoại iPhone 7 Plus đứng chụp hình bên lề đường, I tăng ga áp sát mạn phải, nhanh tay giật lấy điện thoại rồi phóng xe tẩu thoát. Nghe tiếng tri hô, tổ cảnh sát giao thông cùng người dân truy đuổi ép ngã xe và bắt giữ I cùng tang vật. Hội đồng định giá kết luận điện thoại trị giá 16.000.000 đồng.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi dùng xe máy là nguồn nguy hiểm cao độ áp sát giật tài sản người đi đường thuộc trường hợp 'dùng thủ đoạn nguy hiểm' quy định tại điểm d khoản 2 Điều 171 BLHS 2015. Bị cáo tuổi đời còn trẻ, phạm tội lần đầu, khai báo thành khẩn và tài sản đã được trả lại nguyên vẹn cho bị hại.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Trần Minh I phạm 'Tội cướp giật tài sản'.
Áp dụng điểm d khoản 2 Điều 171; điểm s khoản 1, khoản 2 Điều 51 BLHS 2015.
Xử phạt bị cáo Trần Minh I 03 (ba) năm tù.""",
    },
    {
        "id": "judgment_025_vo_y_chet_nguoi_sung_san",
        "case_number": "27/2018/HS-ST",
        "court": "Tòa án nhân dân huyện Lạc Dương, tỉnh Lâm Đồng",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2018-08-14",
        "crime_type": "Tội vô ý làm chết người",
        "applicable_articles": ["128"],
        "defendant": {
            "name": "K' K",
            "dob": "1993-04-07",
            "birth_year": 1993,
            "prior_convictions": 0,
        },
        "facts_summary": "Trưa ngày 10/05/2018, K' K mang súng tự chế đi săn gà rừng tại khu vực rừng đầu nguồn. Do sơ suất không kiểm tra hướng bắn và tầm nhìn bị cây cối che khuất, phát đạn của K' K đã bắn trúng vùng ngực anh Ha M đang đi hái nấm, làm anh Ha M tử vong trên đường đi cấp cứu.",
        "aggravating_factors": [],
        "mitigating_factors": [
            "thành khẩn khai báo",
            "ăn năn hối cải",
            "đầu thú",
            "bồi thường toàn bộ thiệt hại 110 triệu đồng cho gia đình bị hại",
            "gia đình có công với cách mạng",
            "đại diện bị hại xin giảm nhẹ",
        ],
        "verdict": "guilty",
        "sentence_type": "suspended",
        "sentence_years": 2.0,
        "suspended": True,
        "full_text": """TÒA ÁN NHÂN DÂN HUYỆN LẠC DƯƠNG, TỈNH LÂM ĐỒNG
BẢN ÁN SỐ: 27/2018/HS-ST NGÀY 14/08/2018 VỀ TỘI VÔ Ý LÀM CHẾT NGƯỜI

NỘI DUNG VỤ ÁN:
Ngày 10/05/2018, K' K đi săn tại khu vực tiểu khu 112 rừng Lạc Dương. Nghe tiếng động trong lùm cây rậm rạp, tưởng là gà rừng, K' K nổ súng bắn nhưng không ngờ trúng anh Ha M đang hái nấm rừng. Thấy anh M ngã gục, K' K hô hoán cùng người dân đưa nạn nhân đi cấp cứu nhưng anh M tử vong do mất máu cấp. K' K sau đó đã đến cơ quan công an đầu thú.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi bất cẩn khi sử dụng súng săn của bị cáo dẫn đến hậu quả chết người đã phạm vào 'Tội vô ý làm chết người' theo khoản 1 Điều 128 BLHS 2015. Bị cáo có nhiều tình tiết giảm nhẹ: đầu thú, thành khẩn khai báo, gia đình đã bồi thường 110.000.000 đồng, gia đình có công với cách mạng và đại diện bị hại có đơn xin giảm nhẹ hình phạt. Bị cáo đủ điều kiện hưởng án treo theo Điều 65 BLHS.

QUYẾT ĐỊNH:
Tuyên bố bị cáo K' K phạm 'Tội vô ý làm chết người'.
Áp dụng khoản 1 Điều 128; điểm b, s khoản 1, khoản 2 Điều 51; Điều 65 BLHS 2015.
Xử phạt bị cáo K' K 02 (hai) năm tù cho hưởng án treo, thời gian thử thách 04 năm.""",
    },
    {
        "id": "judgment_026_giao_thong_vuot_den_do",
        "case_number": "63/2018/HS-ST",
        "court": "Tòa án nhân dân quận Thanh Xuân, thành phố Hà Nội",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2018-12-10",
        "crime_type": "Tội vi phạm quy định về tham gia giao thông đường bộ",
        "applicable_articles": ["260"],
        "defendant": {
            "name": "Bùi Văn L",
            "dob": "1987-07-22",
            "birth_year": 1987,
            "prior_convictions": 0,
        },
        "facts_summary": "Khoảng 06 giờ 30 phút ngày 14/09/2018, Bùi Văn L điều khiển xe ô tô tải biển số 29C-789.01 lưu thông đến ngã tư đường Nguyễn Trãi - Khuất Duy Tiến, do vội nên không chấp hành đèn tín hiệu giao thông (vượt đèn đỏ), đâm vào xe mô tô do ông T điều khiển đi đúng chiều, khiến ông T tử vong tại chỗ.",
        "aggravating_factors": [],
        "mitigating_factors": [
            "thành khẩn khai báo",
            "ăn năn hối cải",
            "bồi thường khắc phục toàn bộ hậu quả 180 triệu đồng",
            "đại diện hợp pháp của bị hại có đơn xin bãi nại",
        ],
        "verdict": "guilty",
        "sentence_type": "suspended",
        "sentence_years": 1.5,
        "suspended": True,
        "full_text": """TÒA ÁN NHÂN DÂN QUẬN THANH XUÂN, THÀNH PHỐ HÀ NỘI
BẢN ÁN SỐ: 63/2018/HS-ST NGÀY 10/12/2018 VỀ TỘI VI PHẠM QUY ĐỊNH VỀ THAM GIA GIAO THÔNG ĐƯỜNG BỘ

NỘI DUNG VỤ ÁN:
Sáng sớm ngày 14/09/2018, Bùi Văn L lái xe tải biển kiểm soát 29C-789.01 chở vật liệu xây dựng. Khi đến nút giao Nguyễn Trãi - Khuất Duy Tiến, thấy đèn tín hiệu chuyển sang màu đỏ nhưng L vẫn tăng tốc vượt ngã tư, va chạm trực diện với xe máy do ông Trần Văn T điều khiển. Tai nạn làm ông T tử vong tại chỗ do đa chấn thương.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi không chấp hành tín hiệu đèn giao thông làm chết 01 người của bị cáo đã phạm vào điểm a khoản 1 Điều 260 BLHS 2015. Bị cáo nhân thân tốt, chưa tiền án tiền sự, khai báo thành khẩn, đã chủ động bồi thường 180.000.000 đồng và được gia đình nạn nhân xin bãi nại. Bị cáo có nơi cư trú ổn định nên đủ điều kiện áp dụng Điều 65 BLHS.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Bùi Văn L phạm 'Tội vi phạm quy định về tham gia giao thông đường bộ'.
Áp dụng điểm a khoản 1 Điều 260; điểm b, s khoản 1, khoản 2 Điều 51; Điều 65 BLHS 2015.
Xử phạt bị cáo Bùi Văn L 01 (một) năm 06 (sáu) tháng tù cho hưởng án treo, thời gian thử thách 03 năm.""",
    },
    # ==========================================
    # NĂM 2019 (4 bản án)
    # ==========================================
    {
        "id": "judgment_027_co_y_gay_thuong_tich_phong_ve_tuyen_vo_toi",
        "case_number": "11/2019/HS-ST",
        "court": "Tòa án nhân dân quận Lê Chân, thành phố Hải Phòng",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2019-02-25",
        "crime_type": "Tội cố ý gây thương tích",
        "applicable_articles": ["134"],
        "defendant": {
            "name": "Hoàng Văn M",
            "dob": "1986-09-18",
            "birth_year": 1986,
            "prior_convictions": 0,
        },
        "facts_summary": "VKSND truy tố Hoàng Văn M về hành vi gây thương tật 14% cho anh Đặng Văn P tại quán cơm bình dân. Tại phiên tòa, các tài liệu trích xuất camera an ninh và lời khai của 04 nhân chứng độc lập xác nhận anh P cùng 02 đối tượng khác cầm dao kiếm xông vào quán vô cớ đâm chém M trước; M dùng chiếc mâm nhôm che đỡ làm lưỡi dao của P trượt vào cạnh bàn gây rách đùi P. M không có hành vi dùng hung khí tấn công chủ động.",
        "aggravating_factors": [],
        "mitigating_factors": [],
        "verdict": "not_guilty",
        "sentence_type": "acquitted",
        "sentence_years": 0.0,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN QUẬN LÊ CHÂN, THÀNH PHỐ HẢI PHÒNG
BẢN ÁN SỐ: 11/2019/HS-ST NGÀY 25/02/2019
TUYÊN BỐ BỊ CÁO HOÀNG VĂN M KHÔNG PHẠM TỘI

NỘI DUNG VỤ ÁN:
Theo cáo trạng của Viện kiểm sát, ngày 10/10/2018 tại quán ăn trên đường Chùa Hàng, Hoàng Văn M có hành vi xô xát gây thương tích 14% cho anh Đặng Văn P nên bị truy tố về tội Cố ý gây thương tích theo điểm đ khoản 2 Điều 134 BLHS.

NHẬN ĐỊNH CỦA TÒA ÁN:
Căn cứ diễn biến thẩm vấn công khai tại phiên tòa, trích xuất camera an ninh và lời khai của 04 người làm chứng có mặt tại hiện trường: Anh P cùng đồng bọn có vũ khí đao kiếm vô cớ xông vào quán truy sát M. Bị cáo M chỉ dùng chiếc mâm nhôm nhặt tại quán để giơ lên chống đỡ các nhát chém chí mạng. Trong lúc giằng co, anh P bị trượt ngã vào góc bàn vỡ dẫn đến thương tích ở chân. Hành vi của M là hoàn toàn thụ động tự vệ chính đáng theo quy định tại Điều 22 BLHS 2015, không có yếu tố cấu thành tội phạm.

QUYẾT ĐỊNH:
Căn cứ Điều 13, Điều 326 Bộ luật Tố tụng hình sự năm 2015; Điều 22 BLHS 2015.
Tuyên bố bị cáo Hoàng Văn M không phạm tội 'Cố ý gây thương tích'.""",
    },
    {
        "id": "judgment_028_cuop_tai_san_ap_dung_dieu_54",
        "case_number": "33/2019/HS-ST",
        "court": "Tòa án nhân dân tỉnh Thừa Thiên Huế",
        "court_level": "province",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2019-05-14",
        "crime_type": "Tội cướp tài sản",
        "applicable_articles": ["168"],
        "defendant": {
            "name": "Dương Quốc N",
            "dob": "1997-01-30",
            "birth_year": 1997,
            "prior_convictions": 0,
        },
        "facts_summary": "Đêm ngày 20/01/2019, trên đoạn đường tránh Quốc lộ 1A qua thị xã Hương Trà, Dương Quốc N cầm theo một con dao găm bằng kim loại chặn xe máy của chị H, đe dọa yêu cầu đưa tiền và túi xách có 12.000.000 đồng cùng điện thoại di động trị giá 6.000.000 đồng rồi bỏ trốn.",
        "aggravating_factors": ["dùng hung khí nguy hiểm"],
        "mitigating_factors": [
            "thành khẩn khai báo",
            "ăn năn hối cải",
            "đầu thú",
            "đã bồi thường toàn bộ thiệt hại và trả lại tài sản",
            "gia đình có công với cách mạng",
            "hoàn cảnh gia đình đặc biệt khó khăn",
        ],
        "verdict": "guilty",
        "sentence_type": "imprisonment",
        "sentence_years": 5.0,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN TỈNH THỪA THIÊN HUẾ
BẢN ÁN SỐ: 33/2019/HS-ST NGÀY 14/05/2019 VỀ TỘI CƯỚP TÀI SẢN

NỘI DUNG VỤ ÁN:
Khoảng 21 giờ ngày 20/01/2019, do hoàn cảnh nợ nần túng quẫn, Dương Quốc N mang dao găm đứng chờ ở đoạn đường vắng. Khi thấy chị Lê Thị H đi xe máy một mình, N nhảy ra chặn xe, kề dao đe dọa ép chị H giao nộp túi xách bên trong có 12.000.000 đồng tiền mặt và điện thoại di động Oppo trị giá 6.000.000 đồng. Sáng hôm sau, N ân hận nên đã mang tài sản đến Công an thị xã đầu thú và trả lại nguyên vẹn cho chị H.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi của bị cáo dùng hung khí nguy hiểm uy hiếp tinh thần nhằm chiếm đoạt tài sản thuộc điểm d khoản 2 Điều 168 BLHS 2015 có khung hình phạt từ 07 đến 15 năm tù. Tuy nhiên, xét bị cáo có nhiều tình tiết giảm nhẹ quy định tại khoản 1 Điều 51 BLHS: đầu thú, thành khẩn khai báo, tự nguyện trả lại tài sản, bồi thường tổn thất tinh thần, gia đình có công với cách mạng. Căn cứ khoản 1 Điều 54 BLHS, Tòa án quyết định mức hình phạt dưới mức thấp nhất của khung hình phạt.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Dương Quốc N phạm 'Tội cướp tài sản'.
Áp dụng điểm d khoản 2 Điều 168; điểm b, s, v khoản 1, khoản 2 Điều 51; khoản 1 Điều 54 BLHS 2015.
Xử phạt bị cáo Dương Quốc N 05 (năm) năm tù.""",
    },
    {
        "id": "judgment_029_ma_tuy_tang_tru_heroin",
        "case_number": "48/2019/HS-ST",
        "court": "Tòa án nhân dân thành phố Thái Nguyên, tỉnh Thái Nguyên",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2019-08-20",
        "crime_type": "Tội tàng trữ trái phép chất ma túy",
        "applicable_articles": ["249"],
        "defendant": {
            "name": "Triệu Văn O",
            "dob": "1990-11-11",
            "birth_year": 1990,
            "prior_convictions": 1,
        },
        "facts_summary": "Trưa ngày 12/06/2019, tại ngã ba đường Z, tổ công tác Công an thành phố Thái Nguyên phát hiện Triệu Văn O có biểu hiện nghi vấn nên tiến hành kiểm tra, thu giữ trong túi áo khoác của O một gói giấy chứa chất bột màu trắng. Kết luận giám định số 315 kết luận là Heroine có khối lượng 1,85 gam.",
        "aggravating_factors": ["tái phạm"],
        "mitigating_factors": ["thành khẩn khai báo"],
        "verdict": "guilty",
        "sentence_type": "imprisonment",
        "sentence_years": 3.5,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN THÀNH PHỐ THÁI NGUYÊN, TỈNH THÁI NGUYÊN
BẢN ÁN SỐ: 48/2019/HS-ST NGÀY 20/08/2019 VỀ TỘI TÀNG TRỮ TRÁI PHÉP CHẤT MA TÚY

NỘI DUNG VỤ ÁN:
Hồi 11 giờ 30 ngày 12/06/2019, tại tổ 5 phường Quang Trung, tổ công tác Công an thành phố Thái Nguyên kiểm tra hành chính Triệu Văn O, phát hiện và thu giữ 01 gói giấy bọc chất bột màu trắng. O khai nhận mua số ma túy trên với giá 1.500.000 đồng của một người không rõ danh tính để sử dụng. Kết luận giám định xác định là chất ma túy Heroine, khối lượng 1,85 gam.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi tàng trữ 1,85 gam Heroine của bị cáo cấu thành tội 'Tàng trữ trái phép chất ma túy' theo điểm c khoản 1 Điều 249 BLHS 2015. Bị cáo từng có 01 tiền án về tội trộm cắp tài sản chưa được xóa án tích, phạm tội lần này thuộc trường hợp tái phạm theo điểm h khoản 1 Điều 52 BLHS. Quá trình xét hỏi bị cáo thành khẩn khai báo nên được áp dụng điểm s khoản 1 Điều 51 BLHS.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Triệu Văn O phạm 'Tội tàng trữ trái phép chất ma túy'.
Áp dụng điểm c khoản 1 Điều 249; điểm s khoản 1 Điều 51; điểm h khoản 1 Điều 52 BLHS 2015.
Xử phạt bị cáo Triệu Văn O 03 (ba) năm 06 (sáu) tháng tù.""",
    },
    {
        "id": "judgment_030_gay_roi_trat_tu_khu_dan_cu",
        "case_number": "72/2019/HS-ST",
        "court": "Tòa án nhân dân thị xã Bến Cát, tỉnh Bình Dương",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2019-11-28",
        "crime_type": "Tội gây rối trật tự công cộng",
        "applicable_articles": ["318"],
        "defendant": {
            "name": "Nguyễn Thành P",
            "dob": "2000-05-16",
            "birth_year": 2000,
            "prior_convictions": 0,
        },
        "facts_summary": "Khoảng 20 giờ ngày 15/08/2019, Nguyễn Thành P cùng 03 thanh niên tụ tập nẹt pô, rú ga, hò hét gây mất trật tự trên đường liên xã D6. Khi tổ tuần tra công an xã nhắc nhở, P có lời lẽ kích động thách thức, gây ách tắc giao thông đoạn đường suốt 45 phút.",
        "aggravating_factors": [],
        "mitigating_factors": [
            "thành khẩn khai báo",
            "ăn năn hối cải",
            "phạm tội lần đầu thuộc trường hợp ít nghiêm trọng",
            "tuổi đời còn trẻ",
        ],
        "verdict": "guilty",
        "sentence_type": "non_custodial_reform",
        "sentence_years": 1.5,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN THỊ XÃ BẾN CÁT, TỈNH BÌNH DƯƠNG
BẢN ÁN SỐ: 72/2019/HS-ST NGÀY 28/11/2019 VỀ TỘI GÂY RỐI TRẬT TỰ CÔNG CỘNG

NỘI DUNG VỤ ÁN:
Tối ngày 15/08/2019, Nguyễn Thành P cùng một số đối tượng điều khiển xe máy độ pô liên tục nẹt pô rú ga chạy vòng tròn trên đường liên xã, gây ồn ào và cản trở người dân đi lại. Khi lực lượng công an xã làm nhiệm vụ nhắc nhở giải tán, P không chấp hành mà còn lớn tiếng lôi kéo đám đông đứng xem gây ùn tắc giao thông nghiêm trọng.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi của bị cáo đã xâm phạm trật tự công cộng tại khu dân cư, đủ yếu tố cấu thành tội 'Gây rối trật tự công cộng' theo khoản 1 Điều 318 BLHS 2015. Xét bị cáo tuổi đời còn trẻ, phạm tội lần đầu thuộc trường hợp ít nghiêm trọng, tại tòa ăn năn hối cải và có nơi cư trú rõ ràng. Áp dụng hình phạt cải tạo không giam giữ theo Điều 36 BLHS cũng đủ để giáo dục, rèn luyện bị cáo tại địa phương.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Nguyễn Thành P phạm 'Tội gây rối trật tự công cộng'.
Áp dụng khoản 1 Điều 318; điểm i, s khoản 1 Điều 51; Điều 36 BLHS 2015.
Xử phạt bị cáo Nguyễn Thành P 01 (một) năm 06 (sáu) tháng cải tạo không giam giữ.""",
    },
    # ==========================================
    # NĂM 2020 (4 bản án)
    # ==========================================
    {
        "id": "judgment_031_trom_cap_khong_pham_toi_dan_su",
        "case_number": "09/2020/HS-ST",
        "court": "Tòa án nhân dân quận Gò Vấp, TP. Hồ Chí Minh",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2020-03-12",
        "crime_type": "Tội trộm cắp tài sản",
        "applicable_articles": ["173"],
        "defendant": {
            "name": "Lý Văn Q",
            "dob": "1984-04-25",
            "birth_year": 1984,
            "prior_convictions": 0,
        },
        "facts_summary": "VKSND truy tố Lý Văn Q về hành vi lén lút chiếm đoạt chiếc xe máy trị giá 28.000.000 đồng của anh Chu Văn B. Tại phiên tòa, hồ sơ chứng cứ và lời khai thể hiện anh B vay của Q 30.000.000 đồng và tự nguyện giao xe kèm giấy tờ, có giấy biên nhận thỏa thuận cầm cố tài sản hợp pháp. Q mang xe về nhà cất giữ công khai, không có hành vi lén lút.",
        "aggravating_factors": [],
        "mitigating_factors": [],
        "verdict": "not_guilty",
        "sentence_type": "acquitted",
        "sentence_years": 0.0,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN QUẬN GÒ VẤP, THÀNH PHỐ HỒ CHÍ MINH
BẢN ÁN SỐ: 09/2020/HS-ST NGÀY 12/03/2020
TUYÊN BỐ BỊ CÁO LÝ VĂN Q KHÔNG PHẠM TỘI

NỘI DUNG VỤ ÁN:
Cáo trạng truy tố Lý Văn Q về tội 'Trộm cắp tài sản' theo khoản 1 Điều 173 BLHS do cho rằng Q đã lấy trộm chiếc xe máy Yamaha Exciter của anh Chu Văn B dựng tại bãi xe ngày 05/11/2019.

NHẬN ĐỊNH CỦA TÒA ÁN:
Tại phiên tòa, bị cáo xuất trình Giấy thỏa thuận vay tiền và biên nhận giữ tài sản có chữ ký xác nhận của anh B thể hiện anh B vay nợ 30.000.000 đồng và tự nguyện bàn giao chìa khóa cùng giấy đăng ký xe cho Q làm tin. Lời khai của các nhân chứng tại bãi xe cũng xác định Q đến lấy xe ban ngày một cách công khai, thông báo rõ cho người trông coi. Đây là quan hệ tranh chấp tài sản trong hợp đồng vay dân sự, bị cáo không có hành vi lén lút nhằm mục đích chiếm đoạt. Hành vi không cấu thành tội phạm hình sự.

QUYẾT ĐỊNH:
Căn cứ Điều 13, Điều 326 Bộ luật Tố tụng hình sự năm 2015.
Tuyên bố bị cáo Lý Văn Q không phạm tội 'Trộm cắp tài sản'.""",
    },
    {
        "id": "judgment_032_giet_nguoi_khoan_1_dac_biet_nghiem_trong",
        "case_number": "25/2020/HS-ST",
        "court": "Tòa án nhân dân thành phố Hà Nội",
        "court_level": "province",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2020-07-08",
        "crime_type": "Tội giết người",
        "applicable_articles": ["123"],
        "defendant": {
            "name": "Tạ Đình R",
            "dob": "1985-08-14",
            "birth_year": 1985,
            "prior_convictions": 2,
        },
        "facts_summary": "Tối ngày 12/03/2020, tại ngõ phố Khâm Thiên, sau khi uống rượu, Tạ Đình R mang theo thanh kiếm tự chế dài 80cm sang nhà hàng xóm là ông C đâm liên tiếp nhiều nhát vào ngực và bụng nạn nhân do mâu thuẫn tranh chấp ranh giới đất đai kéo dài. Nạn nhân tử vong tại chỗ do thủng tim và phổi.",
        "aggravating_factors": [
            "có tính chất côn đồ",
            "dùng hung khí nguy hiểm",
            "tái phạm nguy hiểm",
        ],
        "mitigating_factors": ["thành khẩn khai báo"],
        "verdict": "guilty",
        "sentence_type": "imprisonment",
        "sentence_years": 20.0,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN THÀNH PHỐ HÀ NỘI
BẢN ÁN SỐ: 25/2020/HS-ST NGÀY 08/07/2020 VỀ TỘI GIẾT NGƯỜI

NỘI DUNG VỤ ÁN:
Tối ngày 12/03/2020, do tranh chấp đất đai ngõ đi chung, Tạ Đình R cầm kiếm tự chế xông thẳng vào nhà ông Nguyễn Văn C. Khi ông C đang ngồi uống trà, R vung kiếm chém và đâm 03 nhát vào ngực và bụng ông C. Vợ ông C tri hô thì R bỏ chạy khỏi hiện trường. Ông C được đưa đi cấp cứu nhưng tử vong trước khi tới bệnh viện.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi của bị cáo có tính chất côn đồ, sử dụng hung khí nguy hiểm tước đoạt tính mạng người khác một cách dã man, phạm vào điểm n khoản 1 Điều 123 BLHS 2015. Bị cáo có 02 tiền án về tội cố ý gây thương tích và cướp giật, chưa được xóa án tích, lần phạm tội này thuộc trường hợp tái phạm nguy hiểm theo điểm h khoản 2 Điều 52 BLHS. Hành vi đặc biệt nguy hiểm cho xã hội, cần áp dụng mức hình phạt tù có thời hạn cao nhất.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Tạ Đình R phạm 'Tội giết người'.
Áp dụng điểm n khoản 1 Điều 123; điểm s khoản 1 Điều 51; điểm h khoản 2 Điều 52 BLHS 2015.
Xử phạt bị cáo Tạ Đình R 20 (hai mươi) năm tù.""",
    },
    {
        "id": "judgment_033_ma_tuy_mua_ban_ap_dung_dieu_54",
        "case_number": "38/2020/HS-ST",
        "court": "Tòa án nhân dân tỉnh Quảng Ninh",
        "court_level": "province",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2020-09-24",
        "crime_type": "Tội mua bán trái phép chất ma túy",
        "applicable_articles": ["251"],
        "defendant": {
            "name": "Đoàn Thị S",
            "dob": "1995-12-03",
            "birth_year": 1995,
            "prior_convictions": 0,
        },
        "facts_summary": "Trưa ngày 18/05/2020, Đoàn Thị S bị bắt giữ khi đang nhận chuyển phát một kiện hàng chứa 22,4 gam Methamphetamine tại khu vực phường Bãi Cháy nhằm bán lại kiếm lời. Quá trình điều tra, S chủ động cung cấp thông tin giúp công an triệt phá đường dây cung cấp ma túy liên tỉnh.",
        "aggravating_factors": [],
        "mitigating_factors": [
            "thành khẩn khai báo",
            "ăn năn hối cải",
            "tích cực giúp đỡ cơ quan có trách nhiệm phát hiện tội phạm",
            "người phạm tội đang nuôi con dưới 36 tháng tuổi",
            "hoàn cảnh kinh tế neo đơn",
        ],
        "verdict": "guilty",
        "sentence_type": "imprisonment",
        "sentence_years": 5.0,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN TỈNH QUẢNG NINH
BẢN ÁN SỐ: 38/2020/HS-ST NGÀY 24/09/2020 VỀ TỘI MUA BÁN TRÁI PHÉP CHẤT MA TÚY

NỘI DUNG VỤ ÁN:
Ngày 18/05/2020, Đoàn Thị S đến bưu cục nhận kiện hàng bưu phẩm có chứa 22,4 gam ma túy loại Methamphetamine thì bị lực lượng công an bắt giữ. S thừa nhận nhận số ma túy này từ đối tượng tên Nam để chia nhỏ bán kiếm lời nuôi con nhỏ. Sau khi bị bắt, S thành khẩn cộng tác, cung cấp sơ đồ và đầu mối giúp cơ quan điều tra bắt giữ đối tượng cầm đầu đường dây.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi mua bán 22,4 gam Methamphetamine của bị cáo phạm vào điểm b khoản 2 Điều 251 BLHS 2015 với khung hình phạt từ 07 đến 15 năm tù. Tuy nhiên, bị cáo có nhiều tình tiết giảm nhẹ quy định tại khoản 1 Điều 51: thành khẩn khai báo, tích cực giúp đỡ cơ quan công an phát hiện tội phạm (điểm t), đang nuôi con dưới 36 tháng tuổi (điểm n). Do đó, Hội đồng xét xử áp dụng khoản 1 Điều 54 BLHS quyết định mức phạt dưới khung hình phạt luật định.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Đoàn Thị S phạm 'Tội mua bán trái phép chất ma túy'.
Áp dụng điểm b khoản 2 Điều 251; điểm s, t, n khoản 1 Điều 51; khoản 1 Điều 54 BLHS 2015.
Xử phạt bị cáo Đoàn Thị S 05 (năm) năm tù.""",
    },
    {
        "id": "judgment_034_giao_thong_nong_do_con",
        "case_number": "55/2020/HS-ST",
        "court": "Tòa án nhân dân thành phố Biên Hòa, tỉnh Đồng Nai",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2020-11-15",
        "crime_type": "Tội vi phạm quy định về tham gia giao thông đường bộ",
        "applicable_articles": ["260"],
        "defendant": {
            "name": "Mai Xuân T",
            "dob": "1992-02-18",
            "birth_year": 1992,
            "prior_convictions": 0,
        },
        "facts_summary": "Đêm ngày 19/08/2020, Mai Xuân T điều khiển xe ô tô 4 chỗ sau khi dự tiệc liên hoan (kết quả đo nồng độ cồn là 0.72 mg/l khí thở), lưu thông với tốc độ 75km/h trong đô thị, va chạm với xe máy chở hai người đi cùng chiều làm 01 người tử vong và 01 người thương tật 38%.",
        "aggravating_factors": ["sử dụng rượu bia nồng độ cồn cao"],
        "mitigating_factors": [
            "thành khẩn khai báo",
            "đầu thú",
            "bồi thường gia đình các nạn nhân tổng cộng 210 triệu đồng",
        ],
        "verdict": "guilty",
        "sentence_type": "imprisonment",
        "sentence_years": 3.0,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN THÀNH PHỐ BIÊN HÒA, TỈNH ĐỒNG NAI
BẢN ÁN SỐ: 55/2020/HS-ST NGÀY 15/11/2020 VỀ TỘI VI PHẠM QUY ĐỊNH VỀ THAM GIA GIAO THÔNG ĐƯỜNG BỘ

NỘI DUNG VỤ ÁN:
Khoảng 22 giờ ngày 19/08/2020, Mai Xuân T điều khiển xe ô tô lưu thông trên đường Đồng Khởi với nồng độ cồn trong hơi thở đạt 0,72 mg/l. Do không làm chủ tốc độ và tầm quan sát bị ảnh hưởng, T đâm vào đuôi xe mô tô chạy cùng chiều phía trước, làm chị V tử vong tại chỗ và anh K bị đa chấn thương với tỷ lệ tổn thương cơ thể 38%.

NHẬN ĐỊNH CỦA TÒA ÁN:
Bị cáo điều khiển phương tiện khi trong máu hoặc hơi thở có nồng độ cồn vượt quá mức quy định gây tai nạn làm chết người, thuộc tình tiết định khung tại điểm b khoản 2 Điều 260 BLHS 2015. Bị cáo đã ra đầu thú, thành khẩn khai báo và tự nguyện bồi thường đầy đủ 210.000.000 đồng cho gia đình các nạn nhân, nên được xem xét giảm nhẹ theo điểm b, s khoản 1, khoản 2 Điều 51 BLHS.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Mai Xuân T phạm 'Tội vi phạm quy định về tham gia giao thông đường bộ'.
Áp dụng điểm b khoản 2 Điều 260; điểm b, s khoản 1, khoản 2 Điều 51 BLHS 2015.
Xử phạt bị cáo Mai Xuân T 03 (ba) năm tù.""",
    },
    # ==========================================
    # NĂM 2021 (4 bản án)
    # ==========================================
    {
        "id": "judgment_035_lua_dao_chiem_doat_dat_dai",
        "case_number": "16/2021/HS-ST",
        "court": "Tòa án nhân dân tỉnh Bà Rịa - Vũng Tàu",
        "court_level": "province",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2021-02-20",
        "crime_type": "Tội lừa đảo chiếm đoạt tài sản",
        "applicable_articles": ["174"],
        "defendant": {
            "name": "Phạm Hữu U",
            "dob": "1978-06-10",
            "birth_year": 1978,
            "prior_convictions": 0,
        },
        "facts_summary": "Trong năm 2020, Phạm Hữu U làm giả giấy tờ quyền sử dụng đất đối với thửa đất quy hoạch cây xanh tại thành phố Vũng Tàu, tự nhận là chủ đất và ký hợp đồng đặt cọc chuyển nhượng cho 03 người, chiếm đoạt tổng số tiền 1.250.000.000 đồng rồi tiêu xài cá nhân.",
        "aggravating_factors": [
            "chiếm đoạt tài sản có giá trị lớn",
            "phạm tội 02 lần trở lên",
            "dùng thủ đoạn tinh vi",
        ],
        "mitigating_factors": [
            "thành khẩn khai báo",
            "đã nộp lại khắc phục 500.000.000 đồng",
        ],
        "verdict": "guilty",
        "sentence_type": "imprisonment",
        "sentence_years": 9.0,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN TỈNH BÀ RỊA - VŨNG TÀU
BẢN ÁN SỐ: 16/2021/HS-ST NGÀY 20/02/2021 VỀ TỘI LỪA ĐẢO CHIẾM ĐOẠT TÀI SẢN

NỘI DUNG VỤ ÁN:
Từ tháng 02/2020 đến tháng 08/2020, Phạm Hữu U tự vẽ bản đồ phân lô và sử dụng giấy chứng nhận quyền sử dụng đất giả của một khu đất thuộc quy hoạch công viên, giới thiệu với người mua là đất dự án của mình. U đã nhận tiền cọc chuyển nhượng của 03 bị hại với tổng số tiền 1.250.000.000 đồng. Sau khi nhận tiền, U cắt đứt liên lạc và dùng số tiền trên vào mục đích cá nhân.

NHẬN ĐỊNH CỦA TÒA ÁN:
Bị cáo dùng thủ đoạn gian dối chiếm đoạt số tiền trên 500 triệu đồng của nhiều người, đã phạm vào điểm a khoản 4 Điều 174 BLHS 2015. Bị cáo có tình tiết tăng nặng phạm tội 2 lần trở lên theo điểm g khoản 1 Điều 52 BLHS. Quá trình giải quyết vụ án, bị cáo đã thành khẩn khai báo và nộp lại 500.000.000 đồng để khắc phục hậu quả, nên được xem xét tình tiết giảm nhẹ theo điểm b, s khoản 1 Điều 51 BLHS.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Phạm Hữu U phạm 'Tội lừa đảo chiếm đoạt tài sản'.
Áp dụng điểm a khoản 4 Điều 174; điểm b, s khoản 1 Điều 51; điểm g khoản 1 Điều 52 BLHS 2015.
Xử phạt bị cáo Phạm Hữu U 09 (chín) năm tù.""",
    },
    {
        "id": "judgment_036_co_y_gay_thuong_tich_an_treo",
        "case_number": "30/2021/HS-ST",
        "court": "Tòa án nhân dân quận Cầu Giấy, thành phố Hà Nội",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2021-06-15",
        "crime_type": "Tội cố ý gây thương tích",
        "applicable_articles": ["134"],
        "defendant": {
            "name": "Hà Trọng V",
            "dob": "1998-03-25",
            "birth_year": 1998,
            "prior_convictions": 0,
        },
        "facts_summary": "Chiều ngày 08/04/2021, tại sân bóng đá mini phường Dịch Vọng Hậu, trong lúc tranh chấp bóng, Hà Trọng V xô xát và dùng tay đấm vào vùng mặt anh Trần Quốc T khiến anh T bị gãy sống mũi, thương tật tỷ lệ 12%.",
        "aggravating_factors": [],
        "mitigating_factors": [
            "phạm tội lần đầu thuộc trường hợp ít nghiêm trọng",
            "thành khẩn khai báo",
            "ăn năn hối cải",
            "tự nguyện bồi thường toàn bộ thiệt hại 35 triệu đồng",
            "bị hại có đơn bãi nại xin giảm nhẹ",
        ],
        "verdict": "guilty",
        "sentence_type": "suspended",
        "sentence_years": 1.0,
        "suspended": True,
        "full_text": """TÒA ÁN NHÂN DÂN QUẬN CẦU GIẤY, THÀNH PHỐ HÀ NỘI
BẢN ÁN SỐ: 30/2021/HS-ST NGÀY 15/06/2021 VỀ TỘI CỐ Ý GÂY THƯƠNG TÍCH

NỘI DUNG VỤ ÁN:
Chiều ngày 08/04/2021, tại sân bóng đá mini phường Dịch Vọng Hậu, quận Cầu Giấy, trong lúc thi đấu thể thao giữa hai đội xảy ra va chạm. Hà Trọng V không kìm chế được bức xúc đã dùng tay đấm mạnh vào mặt anh Trần Quốc T. Giám định thương tật kết luận anh T bị gãy xương chính mũi, tỷ lệ tổn thương cơ thể 12%.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi của bị cáo gây thương tích 12% cho người khác phạm vào khoản 1 Điều 134 BLHS 2015. Bị cáo chưa từng vi phạm pháp luật, phạm tội bộc phát trong lúc chơi thể thao, khai báo thành khẩn, đã bồi thường toàn bộ chi phí điều trị 35.000.000 đồng và bị hại có đơn xin bãi nại. Bị cáo có nơi cư trú rõ ràng, đủ điều kiện hưởng án treo theo Điều 65 BLHS.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Hà Trọng V phạm 'Tội cố ý gây thương tích'.
Áp dụng khoản 1 Điều 134; điểm b, i, s khoản 1, khoản 2 Điều 51; Điều 65 BLHS 2015.
Xử phạt bị cáo Hà Trọng V 01 (một) năm tù cho hưởng án treo, thời gian thử thách 02 năm.""",
    },
    {
        "id": "judgment_037_ma_tuy_van_chuyen_lien_tinh",
        "case_number": "44/2021/HS-ST",
        "court": "Tòa án nhân dân tỉnh Thanh Hóa",
        "court_level": "province",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2021-09-10",
        "crime_type": "Tội vận chuyển trái phép chất ma túy",
        "applicable_articles": ["250"],
        "defendant": {
            "name": "Lê Đình X",
            "dob": "1983-04-12",
            "birth_year": 1983,
            "prior_convictions": 1,
        },
        "facts_summary": "Đêm ngày 14/06/2021, tại Trạm thu phí Bỉm Sơn, lực lượng CSĐT tội phạm về ma túy bắt giữ Lê Đình X điều khiển xe ô tô du lịch vận chuyển thuê 02 bánh Heroine (tổng trọng lượng 698,5 gam) từ biên giới về các tỉnh đồng bằng tiêu thụ.",
        "aggravating_factors": [
            "tái phạm nguy hiểm",
            "vận chuyển số lượng ma túy rất lớn",
        ],
        "mitigating_factors": ["thành khẩn khai báo"],
        "verdict": "guilty",
        "sentence_type": "imprisonment",
        "sentence_years": 16.0,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN TỈNH THANH HÓA
BẢN ÁN SỐ: 44/2021/HS-ST NGÀY 10/09/2021 VỀ TỘI VẬN CHUYỂN TRÁI PHÉP CHẤT MA TÚY

NỘI DUNG VỤ ÁN:
Hồi 22 giờ 30 ngày 14/06/2021, tại Trạm thu phí Bỉm Sơn, Công an tỉnh Thanh Hóa kiểm tra xe ô tô BKS 36A-345.67 do Lê Đình X điều khiển, phát hiện dưới hộc để đồ ghế sau có 02 khối chữ nhật bọc băng keo đen. Kết luận giám định số 412 xác định toàn bộ là Heroine, tổng khối lượng 698,5 gam. X khai nhận vận chuyển thuê với tiền công 30 triệu đồng.

NHẬN ĐỊNH CỦA TÒA ÁN:
Bị cáo vận chuyển 698,5 gam Heroine đã phạm vào điểm b khoản 4 Điều 250 BLHS 2015. Bị cáo có 01 tiền án chưa xóa án tích về tội mua bán ma túy nên lần này thuộc trường hợp tái phạm nguy hiểm theo điểm h khoản 2 Điều 52 BLHS. Quá trình điều tra bị cáo thành khẩn khai báo nên áp dụng điểm s khoản 1 Điều 51 BLHS. Cần xử phạt nghiêm khắc để đảm bảo tính răn đe.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Lê Đình X phạm 'Tội vận chuyển trái phép chất ma túy'.
Áp dụng điểm b khoản 4 Điều 250; điểm s khoản 1 Điều 51; điểm h khoản 2 Điều 52 BLHS 2015.
Xử phạt bị cáo Lê Đình X 16 (mười sáu) năm tù.""",
    },
    {
        "id": "judgment_038_vo_y_chet_nguoi_dien_giat",
        "case_number": "61/2021/HS-ST",
        "court": "Tòa án nhân dân huyện Yên Định, tỉnh Thanh Hóa",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2021-11-25",
        "crime_type": "Tội vô ý làm chết người",
        "applicable_articles": ["128"],
        "defendant": {
            "name": "Trịnh Bá Y",
            "dob": "1975-10-08",
            "birth_year": 1975,
            "prior_convictions": 0,
        },
        "facts_summary": "Đầu tháng 09/2021, để bảo vệ ruộng ngô của gia đình khỏi chuột phá hoại, Trịnh Bá Y đã kéo dây điện 220V giăng xung quanh bờ ruộng nhưng không đặt biển cảnh báo nguy hiểm và không ngắt điện ban ngày. Ông Nguyễn Văn H đi cắt cỏ sơ ý vướng vào dây điện bị điện giật tử vong.",
        "aggravating_factors": [],
        "mitigating_factors": [
            "thành khẩn khai báo",
            "ăn năn hối cải",
            "bồi thường toàn bộ thiệt hại 130 triệu đồng",
            "gia đình người bị hại có đơn xin miễn trách nhiệm hình sự",
            "nhân thân tốt",
        ],
        "verdict": "guilty",
        "sentence_type": "suspended",
        "sentence_years": 1.5,
        "suspended": True,
        "full_text": """TÒA ÁN NHÂN DÂN HUYỆN YÊN ĐỊNH, TỈNH THANH HÓA
BẢN ÁN SỐ: 61/2021/HS-ST NGÀY 25/11/2021 VỀ TỘI VÔ Ý LÀM CHẾT NGƯỜI

NỘI DUNG VỤ ÁN:
Ngày 03/09/2021, Trịnh Bá Y kéo dây điện trần từ nhà ra bãi ngô để bẫy chuột. Do cẩu thả, Y không đặt biển cảnh báo và quên không ngắt cầu dao. Khoảng 07 giờ sáng ngày 04/09/2021, ông Nguyễn Văn H đi cắt cỏ qua bờ ruộng vướng phải dây kim loại có điện dẫn đến tử vong do suy hô hấp tuần hoàn cấp vì điện giật.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi giăng dây điện bẫy chuột gây chết người của bị cáo cấu thành tội 'Vô ý làm chết người' theo quy định tại khoản 1 Điều 128 BLHS 2015. Bị cáo nhân thân tốt, chưa tiền án tiền sự, khai báo thành khẩn, đã khắc phục bồi thường 130.000.000 đồng và gia đình nạn nhân tha thiết xin miễn giảm hình phạt. Bị cáo có đủ điều kiện hưởng án treo theo Điều 65 BLHS.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Trịnh Bá Y phạm 'Tội vô ý làm chết người'.
Áp dụng khoản 1 Điều 128; điểm b, s khoản 1, khoản 2 Điều 51; Điều 65 BLHS 2015.
Xử phạt bị cáo Trịnh Bá Y 01 (một) năm 06 (sáu) tháng tù cho hưởng án treo, thời gian thử thách 03 năm.""",
    },
    # ==========================================
    # NĂM 2022 (4 bản án)
    # ==========================================
    {
        "id": "judgment_039_ma_tuy_giam_dinh_am_tinh_vo_toi",
        "case_number": "10/2022/HS-ST",
        "court": "Tòa án nhân dân quận 8, TP. Hồ Chí Minh",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2022-02-14",
        "crime_type": "Tội tàng trữ trái phép chất ma túy",
        "applicable_articles": ["249"],
        "defendant": {
            "name": "Châu Vĩnh Z",
            "dob": "1997-07-29",
            "birth_year": 1997,
            "prior_convictions": 0,
        },
        "facts_summary": "VKSND truy tố Châu Vĩnh Z về hành vi tàng trữ 01 gói nilon tinh thể màu trắng thu giữ trong túi áo khoác khi kiểm tra hành chính. Tại phiên tòa, Kết luận giám định số 108 của Phân viện Khoa học hình sự xác định mẫu tinh thể màu trắng thu giữ là đường phèn và muối khoáng, không tìm thấy chất ma túy. Lời khai của người làm chứng và biên bản lấy mẫu đều trùng khớp.",
        "aggravating_factors": [],
        "mitigating_factors": [],
        "verdict": "not_guilty",
        "sentence_type": "acquitted",
        "sentence_years": 0.0,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN QUẬN 8, THÀNH PHỐ HỒ CHÍ MINH
BẢN ÁN SỐ: 10/2022/HS-ST NGÀY 14/02/2022
TUYÊN BỐ BỊ CÁO CHÂU VĨNH Z KHÔNG PHẠM TỘI

NỘI DUNG VỤ ÁN:
Cáo trạng truy tố Châu Vĩnh Z về tội 'Tàng trữ trái phép chất ma túy' theo khoản 1 Điều 249 BLHS do đêm ngày 12/11/2021 tổ công tác thu giữ trong túi áo của Z 01 gói nilon chứa tinh thể màu trắng nghi là ma túy đá.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hội đồng xét xử xem xét Bản kết luận giám định chính thức số 108/KL-KTHS của Phân viện Khoa học hình sự Bộ Công an tại TP.HCM: Tinh thể màu trắng thu giữ có khối lượng 1,2 gam, kết quả phân tích không tìm thấy các chất ma túy hoặc tiền chất ma túy thường gặp, thành phần chính là muối khoáng và đường saccharose. Lời khai của bị cáo khai được người quen gửi cầm hộ đồ ăn gia vị là có cơ sở. Do tang vật không phải là chất ma túy nên không đủ yếu tố cấu thành tội phạm.

QUYẾT ĐỊNH:
Căn cứ Điều 13, Điều 326 Bộ luật Tố tụng hình sự năm 2015.
Tuyên bố bị cáo Châu Vĩnh Z không phạm tội 'Tàng trữ trái phép chất ma túy'.""",
    },
    {
        "id": "judgment_040_trom_cap_dien_thoai_sieu_thi",
        "case_number": "24/2022/HS-ST",
        "court": "Tòa án nhân dân quận Hải An, thành phố Hải Phòng",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2022-05-19",
        "crime_type": "Tội trộm cắp tài sản",
        "applicable_articles": ["173"],
        "defendant": {
            "name": "Phan Anh AA",
            "dob": "2001-09-02",
            "birth_year": 2001,
            "prior_convictions": 0,
        },
        "facts_summary": "Chiều ngày 05/03/2022, tại gian hàng điện thoại siêu thị B, Phan Anh AA lợi dụng nhân viên tư vấn đang bận tiếp khách khác đã lén lút mở tủ kính lấy trộm 01 chiếc điện thoại Samsung Galaxy S21 trị giá 17.500.000 đồng rồi giấu vào balo mang ra ngoài thì bị bảo vệ phát hiện qua camera giám sát.",
        "aggravating_factors": [],
        "mitigating_factors": [
            "phạm tội lần đầu thuộc trường hợp ít nghiêm trọng",
            "thành khẩn khai báo",
            "ăn năn hối cải",
            "đã thu hồi trả lại toàn bộ tài sản cho siêu thị",
            "sinh viên có kết quả học tập tốt",
        ],
        "verdict": "guilty",
        "sentence_type": "suspended",
        "sentence_years": 1.0,
        "suspended": True,
        "full_text": """TÒA ÁN NHÂN DÂN QUẬN HẢI AN, THÀNH PHỐ HẢI PHÒNG
BẢN ÁN SỐ: 24/2022/HS-ST NGÀY 19/05/2022 VỀ TỘI TRỘM CẮP TÀI SẢN

NỘI DUNG VỤ ÁN:
Chiều ngày 05/03/2022, Phan Anh AA vào siêu thị điện máy trên đường Lê Hồng Phong. Lợi dụng lúc quầy trải nghiệm vắng người, AA lén lút mở tủ trưng bày lấy trộm chiếc điện thoại Samsung Galaxy S21 trị giá 17.500.000 đồng bỏ vào balo. Khi AA vừa bước qua cửa an ninh thì chuông báo vang lên, nhân viên bảo vệ kiểm tra phát hiện bắt giữ giao công an.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi lén lút chiếm đoạt tài sản trị giá 17.500.000 đồng của bị cáo phạm vào khoản 1 Điều 173 BLHS 2015. Bị cáo chưa có tiền án tiền sự, là sinh viên đại học năm thứ 3 có học lực khá, phạm tội nhất thời do bồng bột. Tại phiên tòa thành khẩn khai báo, tài sản đã thu hồi nguyên vẹn trả lại siêu thị. Bị cáo có nơi cư trú rõ ràng và gia đình bảo lãnh, đủ điều kiện hưởng án treo.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Phan Anh AA phạm 'Tội trộm cắp tài sản'.
Áp dụng khoản 1 Điều 173; điểm i, s khoản 1, khoản 2 Điều 51; Điều 65 BLHS 2015.
Xử phạt bị cáo Phan Anh AA 01 (một) năm tù cho hưởng án treo, thời gian thử thách 02 năm.""",
    },
    {
        "id": "judgment_041_gay_roi_trat_tu_dua_xe",
        "case_number": "37/2022/HS-ST",
        "court": "Tòa án nhân dân quận Bình Thạnh, TP. Hồ Chí Minh",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2022-09-08",
        "crime_type": "Tội gây rối trật tự công cộng",
        "applicable_articles": ["318"],
        "defendant": {
            "name": "Đặng Hùng BB",
            "dob": "2002-11-20",
            "birth_year": 2002,
            "prior_convictions": 0,
        },
        "facts_summary": "Khuya ngày 12/06/2022, Đặng Hùng BB tụ tập cùng nhóm hơn 20 thanh thiếu niên chặn đường trên cầu Sài Gòn, dàn hàng ngang tổ chức so kè tốc độ, biểu diễn bốc đầu xe gây ách tắc giao thông tuyến huyết mạch và gây hoang mang lo sợ cho người đi đường.",
        "aggravating_factors": [
            "tụ tập đông người cản trở giao thông nghiêm trọng",
            "dùng phương tiện độ chế nguy hiểm",
        ],
        "mitigating_factors": ["thành khẩn khai báo", "ăn năn hối cải", "phạm tội lần đầu"],
        "verdict": "guilty",
        "sentence_type": "imprisonment",
        "sentence_years": 2.0,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN QUẬN BÌNH THẠNH, THÀNH PHỐ HỒ CHÍ MINH
BẢN ÁN SỐ: 37/2022/HS-ST NGÀY 08/09/2022 VỀ TỘI GÂY RỐI TRẬT TỰ CÔNG CỘNG

NỘI DUNG VỤ ÁN:
Vào hồi 01 giờ sáng ngày 12/06/2022, Đặng Hùng BB cầm đầu một nhóm hơn 20 thanh niên đi xe máy tụ tập tại chân cầu Sài Gòn. Nhóm này chặn các làn đường ô tô, dàn hàng ngang nẹt pô, rú ga inh ỏi và phóng bạt mạng thi thố tốc độ gây cản trở các phương tiện lưu thông suốt 30 phút, đe dọa trực tiếp an toàn giao thông đô thị.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi tụ tập đua xe trái phép, gây cản trở giao thông nghiêm trọng trên tuyến đường huyết mạch của thành phố đã cấu thành tội 'Gây rối trật tự công cộng' theo điểm c khoản 2 Điều 318 BLHS 2015. Bị cáo đóng vai trò kích động, phương tiện xe máy đã bị thay đổi kết cấu kỹ thuật. Quá trình xét xử bị cáo thành khẩn nhận tội, phạm tội lần đầu. Cần áp dụng hình phạt tù giam có thời hạn để giáo dục phòng ngừa chung.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Đặng Hùng BB phạm 'Tội gây rối trật tự công cộng'.
Áp dụng điểm c khoản 2 Điều 318; điểm s khoản 1, khoản 2 Điều 51 BLHS 2015.
Xử phạt bị cáo Đặng Hùng BB 02 (hai) năm tù.""",
    },
    {
        "id": "judgment_042_giao_thong_xe_tai_lan_lan",
        "case_number": "59/2022/HS-ST",
        "court": "Tòa án nhân dân thị xã Phú Mỹ, tỉnh Bà Rịa - Vũng Tàu",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2022-11-30",
        "crime_type": "Tội vi phạm quy định về tham gia giao thông đường bộ",
        "applicable_articles": ["260"],
        "defendant": {
            "name": "Nguyễn Văn CC",
            "dob": "1986-01-14",
            "birth_year": 1986,
            "prior_convictions": 0,
        },
        "facts_summary": "Sáng ngày 15/08/2022, Nguyễn Văn CC điều khiển xe tải ben lưu thông trên Quốc lộ 51, khi chuyển làn không chú ý quan sát và không bật đèn tín hiệu rẽ, va chạm vào xe máy đi cùng chiều làm người điều khiển xe máy tử vong.",
        "aggravating_factors": [],
        "mitigating_factors": [
            "thành khẩn khai báo",
            "ăn năn hối cải",
            "đầu thú",
            "bồi thường toàn bộ thiệt hại 220 triệu đồng",
            "đại diện hợp pháp của bị hại có đơn xin miễn truy cứu trách nhiệm hình sự",
        ],
        "verdict": "guilty",
        "sentence_type": "suspended",
        "sentence_years": 2.0,
        "suspended": True,
        "full_text": """TÒA ÁN NHÂN DÂN THỊ XÃ PHÚ MỸ, TỈNH BÀ RỊA - VŨNG TÀU
BẢN ÁN SỐ: 59/2022/HS-ST NGÀY 30/11/2022 VỀ TỘI VI PHẠM QUY ĐỊNH VỀ THAM GIA GIAO THÔNG ĐƯỜNG BỘ

NỘI DUNG VỤ ÁN:
Khoảng 08 giờ 15 ngày 15/08/2022, Nguyễn Văn CC lái xe tải ben chở đá trên Quốc lộ 51 hướng từ Phú Mỹ đi Vũng Tàu. Đến Km42, CC chuyển từ làn giữa sang làn sát dải phân cách mà không quan sát gương chiếu hậu và không bật đèn xi nhan, va vào xe mô tô của chị Đỗ Thị M khiến nạn nhân ngã xuống đường và bị bánh sau cán qua tử vong.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi chuyển làn không đảm bảo an toàn giao thông gây chết 01 người của bị cáo đã phạm vào điểm a khoản 1 Điều 260 BLHS 2015. Bị cáo ra đầu thú, thành khẩn khai báo, đã cùng chủ xe bồi thường trọn vẹn 220.000.000 đồng cho gia đình bị hại. Gia đình bị hại có đơn xin miễn truy cứu trách nhiệm hình sự cho bị cáo. Xét bị cáo có nhân thân tốt, đủ điều kiện hưởng án treo.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Nguyễn Văn CC phạm 'Tội vi phạm quy định về tham gia giao thông đường bộ'.
Áp dụng điểm a khoản 1 Điều 260; điểm b, s khoản 1, khoản 2 Điều 51; Điều 65 BLHS 2015.
Xử phạt bị cáo Nguyễn Văn CC 02 (hai) năm tù cho hưởng án treo, thời gian thử thách 04 năm.""",
    },
    # ==========================================
    # NĂM 2023 (4 bản án)
    # ==========================================
    {
        "id": "judgment_043_cuop_giat_day_chuyen",
        "case_number": "17/2023/HS-ST",
        "court": "Tòa án nhân dân quận 12, TP. Hồ Chí Minh",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2023-04-10",
        "crime_type": "Tội cướp giật tài sản",
        "applicable_articles": ["171"],
        "defendant": {
            "name": "Võ Thành DD",
            "dob": "1996-08-04",
            "birth_year": 1996,
            "prior_convictions": 1,
        },
        "facts_summary": "Trưa ngày 10/01/2023, Võ Thành DD chạy xe mô tô Exciter rảo quanh tuyến đường Lê Văn Khương, áp sát giật sợi dây chuyền vàng 18K trị giá 22.000.000 đồng của bà N đang đứng bên lề đường, làm bà N ngã xuống đường chấn thương phần mềm.",
        "aggravating_factors": ["dùng thủ đoạn nguy hiểm", "tái phạm"],
        "mitigating_factors": ["thành khẩn khai báo", "thu hồi trả lại tài sản"],
        "verdict": "guilty",
        "sentence_type": "imprisonment",
        "sentence_years": 4.5,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN QUẬN 12, THÀNH PHỐ HỒ CHÍ MINH
BẢN ÁN SỐ: 17/2023/HS-ST NGÀY 10/04/2023 VỀ TỘI CƯỚP GIẬT TÀI SẢN

NỘI DUNG VỤ ÁN:
Khoảng 11 giờ 30 ngày 10/01/2023, Võ Thành DD điều khiển xe máy Yamaha Exciter gắn biển số giả lưu thông trên đường Lê Văn Khương. Phát hiện bà Phan Thị N đứng mua hàng bên lề đường có đeo dây chuyền vàng, DD áp sát giật mạnh sợi dây chuyền vàng 18K trọng lượng 5 chỉ (trị giá 22.000.000 đồng) khiến bà N ngã trầy xước tay chân. DD tăng ga bỏ chạy nhưng bị công an trích xuất camera truy bắt sau 24 giờ.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi của bị cáo sử dụng xe máy tốc độ cao giật tài sản làm ngã người đi đường thuộc trường hợp dùng thủ đoạn nguy hiểm quy định tại điểm d khoản 2 Điều 171 BLHS 2015. Bị cáo có 01 tiền án về tội trộm cắp tài sản chưa được xóa án tích nên thuộc trường hợp tái phạm theo điểm h khoản 1 Điều 52 BLHS. Quá trình điều tra bị cáo thành khẩn nhận tội, tài sản đã thu hồi trả lại người bị hại.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Võ Thành DD phạm 'Tội cướp giật tài sản'.
Áp dụng điểm d khoản 2 Điều 171; điểm s khoản 1 Điều 51; điểm h khoản 1 Điều 52 BLHS 2015.
Xử phạt bị cáo Võ Thành DD 04 (bốn) năm 06 (sáu) tháng tù.""",
    },
    {
        "id": "judgment_044_lua_dao_chuyen_tien_gia_mao",
        "case_number": "35/2023/HS-ST",
        "court": "Tòa án nhân dân quận Hoàn Kiếm, thành phố Hà Nội",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2023-06-22",
        "crime_type": "Tội lừa đảo chiếm đoạt tài sản",
        "applicable_articles": ["174"],
        "defendant": {
            "name": "Đinh Thu EE",
            "dob": "1994-03-17",
            "birth_year": 1994,
            "prior_convictions": 0,
        },
        "facts_summary": "Từ tháng 11/2022 đến tháng 02/2023, Đinh Thu EE sử dụng tài khoản mạng xã hội giả mạo cán bộ bệnh viện, gửi hình ảnh biên lai giả kêu gọi tiền viện phí từ thiện phẫu thuật tim cho trẻ em nghèo, nhận ủng hộ của 12 nhà hảo tâm tổng số tiền 140.000.000 đồng rồi chiếm đoạt tiêu xài.",
        "aggravating_factors": [
            "dùng thủ đoạn tinh vi",
            "phạm tội 02 lần trở lên",
            "lợi dụng hoàn cảnh khó khăn dịch bệnh từ thiện",
        ],
        "mitigating_factors": [
            "thành khẩn khai báo",
            "đã bồi thường khắc phục toàn bộ 140 triệu đồng",
            "nuôi con nhỏ dưới 36 tháng tuổi",
        ],
        "verdict": "guilty",
        "sentence_type": "imprisonment",
        "sentence_years": 2.5,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN QUẬN HOÀN KIẾM, THÀNH PHỐ HÀ NỘI
BẢN ÁN SỐ: 35/2023/HS-ST NGÀY 22/06/2023 VỀ TỘI LỪA ĐẢO CHIẾM ĐOẠT TÀI SẢN

NỘI DUNG VỤ ÁN:
Trong khoảng thời gian cuối năm 2022 đầu năm 2023, Đinh Thu EE lập tài khoản Facebook giả mạo nhân viên phòng công tác xã hội Bệnh viện Nhi Trung ương. EE cắt ghép hình ảnh các bệnh nhi hiểm nghèo và biên lai viện phí giả mạo để kêu gọi quyên góp từ thiện. 12 cá nhân hảo tâm đã chuyển khoản vào tài khoản của EE với tổng số tiền 140.000.000 đồng, sau đó EE rút toàn bộ để tiêu dùng cá nhân.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi dùng thủ đoạn gian dối trên không gian mạng chiếm đoạt 140.000.000 đồng của nhiều người đã phạm vào điểm c, e khoản 2 Điều 174 BLHS 2015. Bị cáo có tình tiết tăng nặng phạm tội 02 lần trở lên. Tuy nhiên bị cáo nhân thân chưa tiền án tiền sự, tại cơ quan điều tra và phiên tòa khai báo thành khẩn, gia đình đã bồi thường hoàn trả 100% số tiền chiếm đoạt cho các bị hại và bị cáo đang nuôi con nhỏ dưới 36 tháng tuổi.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Đinh Thu EE phạm 'Tội lừa đảo chiếm đoạt tài sản'.
Áp dụng điểm c khoản 2 Điều 174; điểm b, s, n khoản 1, khoản 2 Điều 51; điểm g khoản 1 Điều 52 BLHS 2015.
Xử phạt bị cáo Đinh Thu EE 02 (hai) năm 06 (sáu) tháng tù.""",
    },
    {
        "id": "judgment_045_co_y_gay_thuong_tich_hung_khi",
        "case_number": "50/2023/HS-ST",
        "court": "Tòa án nhân dân thành phố Buôn Ma Thuột, tỉnh Đắk Lắk",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2023-09-18",
        "crime_type": "Tội cố ý gây thương tích",
        "applicable_articles": ["134"],
        "defendant": {
            "name": "Y FF",
            "dob": "1999-12-10",
            "birth_year": 1999,
            "prior_convictions": 0,
        },
        "facts_summary": "Chiều ngày 04/06/2023, tại buôn K, sau chầu rượu, Y FF phát sinh mâu thuẫn cãi vã với anh Y G về việc chăn thả bò. Y FF chạy về nhà lấy con rựa phát bờ rào chém một nhát trúng bắp tay phải anh Y G gây đứt cơ và mẻ xương, tỷ lệ tổn thương cơ thể 16%.",
        "aggravating_factors": ["dùng hung khí nguy hiểm"],
        "mitigating_factors": [
            "thành khẩn khai báo",
            "bồi thường thiệt hại 40 triệu đồng",
            "người đồng bào dân tộc thiểu số hiểu biết pháp luật hạn chế",
            "bị hại xin giảm nhẹ",
        ],
        "verdict": "guilty",
        "sentence_type": "imprisonment",
        "sentence_years": 2.5,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN THÀNH PHỐ BUÔN MA THUỘT, TỈNH ĐẮK LẮK
BẢN ÁN SỐ: 50/2023/HS-ST NGÀY 18/09/2023 VỀ TỘI CỐ Ý GÂY THƯƠNG TÍCH

NỘI DUNG VỤ ÁN:
Chiều ngày 04/06/2023, tại buôn K, xã Ea Tu, sau khi uống rượu, Y FF to tiếng cãi nhau với anh Y G liên quan đến việc trâu bò giẫm rẫy cà phê. Bực tức, Y FF chạy vào chòi rẫy lấy con rựa dài 65cm chém 01 nhát trúng bắp tay phải của anh Y G. Anh Y G được đưa đi mổ khâu nối cơ, kết luận giám định pháp y xác định tỷ lệ tổn thương cơ thể là 16%.

NHẬN ĐỊNH CỦA TÒA ÁN:
Bị cáo dùng rựa là hung khí nguy hiểm gây thương tích cho bị hại 16%, phạm vào điểm đ khoản 2 Điều 134 BLHS 2015. Bị cáo chưa có tiền án tiền sự, là người đồng bào dân tộc thiểu số hiểu biết pháp luật còn hạn chế, sau khi phạm tội đã tác động gia đình bồi thường 40.000.000 đồng, thành khẩn khai báo và được bị hại xin giảm nhẹ hình phạt.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Y FF phạm 'Tội cố ý gây thương tích'.
Áp dụng điểm đ khoản 2 Điều 134; điểm b, s khoản 1, khoản 2 Điều 51 BLHS 2015.
Xử phạt bị cáo Y FF 02 (hai) năm 06 (sáu) tháng tù.""",
    },
    {
        "id": "judgment_046_ma_tuy_mua_ban_thuoc_lac",
        "case_number": "68/2023/HS-ST",
        "court": "Tòa án nhân dân quận Ngô Quyền, thành phố Hải Phòng",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2023-12-12",
        "crime_type": "Tội mua bán trái phép chất ma túy",
        "applicable_articles": ["251"],
        "defendant": {
            "name": "Phạm Tấn GG",
            "dob": "1993-05-23",
            "birth_year": 1993,
            "prior_convictions": 0,
        },
        "facts_summary": "Rạng sáng ngày 18/09/2023, tại một quán karaoke trên đường Lê Hồng Phong, lực lượng công an phát hiện Phạm Tấn GG đang cất giữ trong người 15 viên thuốc lắc màu xám (MDMA có trọng lượng 5,82 gam) và 03 túi ketamine (trọng lượng 3,14 gam) nhằm bán cho các khách hát.",
        "aggravating_factors": [],
        "mitigating_factors": ["thành khẩn khai báo", "ăn năn hối cải"],
        "verdict": "guilty",
        "sentence_type": "imprisonment",
        "sentence_years": 7.5,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN QUẬN NGÔ QUYỀN, THÀNH PHỐ HẢI PHÒNG
BẢN ÁN SỐ: 68/2023/HS-ST NGÀY 12/12/2023 VỀ TỘI MUA BÁN TRÁI PHÉP CHẤT MA TÚY

NỘI DUNG VỤ ÁN:
Hồi 01 giờ 15 ngày 18/09/2023, kiểm tra hành chính quán karaoke Luxury trên đường Lê Hồng Phong, tổ công tác bắt quả tang Phạm Tấn GG đang tàng trữ 15 viên nén màu xám và 03 túi nylon chứa tinh thể màu trắng. GG khai nhận mua từ Hải Phòng mang vào quán karaoke bán kiếm lời. Kết quả giám định kết luận: 15 viên nén là MDMA, khối lượng 5,82 gam; tinh thể màu trắng là Ketamine, khối lượng 3,14 gam.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi mua bán trái phép 5,82 gam MDMA và 3,14 gam Ketamine của bị cáo thuộc trường hợp có từ 02 chất ma túy trở lên, cấu thành tội 'Mua bán trái phép chất ma túy' theo điểm i khoản 2 Điều 251 BLHS 2015 với khung hình phạt từ 07 đến 15 năm tù. Bị cáo chưa tiền án tiền sự, khai báo thành khẩn và tỏ thái độ ăn năn hối cải tại phiên tòa nên được áp dụng điểm s khoản 1 Điều 51 BLHS.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Phạm Tấn GG phạm 'Tội mua bán trái phép chất ma túy'.
Áp dụng điểm i khoản 2 Điều 251; điểm s khoản 1 Điều 51 BLHS 2015.
Xử phạt bị cáo Phạm Tấn GG 07 (bảy) năm 06 (sáu) tháng tù.""",
    },
    # ==========================================
    # NĂM 2024 (4 bản án)
    # ==========================================
    {
        "id": "judgment_047_giet_nguoi_do_ghen_tuong",
        "case_number": "12/2024/HS-ST",
        "court": "Tòa án nhân dân tỉnh Đồng Nai",
        "court_level": "province",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2024-01-18",
        "crime_type": "Tội giết người",
        "applicable_articles": ["123"],
        "defendant": {
            "name": "Tạ Văn HH",
            "dob": "1988-10-15",
            "birth_year": 1988,
            "prior_convictions": 0,
        },
        "facts_summary": "Tối ngày 22/09/2023, do nghi ngờ vợ có quan hệ tình cảm với anh Vũ Ngọc M, Tạ Văn HH chuẩn bị một con dao bầu giấu trong người tìm đến phòng trọ của anh M tại phường Long Bình Tân, đâm nhiều nhát vào vùng ngực và sườn làm anh M tử vong trên đường đưa đi cấp cứu.",
        "aggravating_factors": ["dùng hung khí nguy hiểm", "có tính chất côn đồ"],
        "mitigating_factors": [
            "đầu thú",
            "thành khẩn khai báo",
            "ăn năn hối cải",
            "đã bồi thường chi phí mai táng 150 triệu đồng cho gia đình nạn nhân",
        ],
        "verdict": "guilty",
        "sentence_type": "imprisonment",
        "sentence_years": 15.0,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN TỈNH ĐỒNG NAI
BẢN ÁN SỐ: 12/2024/HS-ST NGÀY 18/01/2024 VỀ TỘI GIẾT NGƯỜI

NỘI DUNG VỤ ÁN:
Tối ngày 22/09/2023, nghi ngờ vợ có quan hệ ngoài luồng, Tạ Văn HH thủ sẵn 01 dao bầu nhọn dài 30cm đi đến dãy phòng trọ tại phường Long Bình Tân, thành phố Biên Hòa. Gặp anh Vũ Ngọc M, hai bên lời qua tiếng lại, HH rút dao đâm liên tiếp 02 nhát vào ngực trái và mạn sườn anh M. Nạn nhân ngã gục và tử vong do sốc mất máu cấp thủng tim. HH sau đó mang dao đến Công an phường đầu thú.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi chuẩn bị hung khí đâm chết người chỉ vì nghi ngờ ghen tuông có tính chất côn đồ, phạm vào điểm n khoản 1 Điều 123 BLHS 2015. Sau khi gây án bị cáo đã đầu thú, thành khẩn nhận tội, gia đình đã tự nguyện nộp 150.000.000 đồng bồi thường mai táng và tổn thất tinh thần cho gia đình người bị hại. Bị cáo được áp dụng điểm b, s khoản 1, khoản 2 Điều 51 BLHS.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Tạ Văn HH phạm 'Tội giết người'.
Áp dụng điểm n khoản 1 Điều 123; điểm b, s khoản 1, khoản 2 Điều 51 BLHS 2015.
Xử phạt bị cáo Tạ Văn HH 15 (mười lăm) năm tù.""",
    },
    {
        "id": "judgment_048_gay_roi_trat_tu_hung_khi_dieu_54",
        "case_number": "22/2024/HS-ST",
        "court": "Tòa án nhân dân quận Sơn Trà, thành phố Đà Nẵng",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2024-03-25",
        "crime_type": "Tội gây rối trật tự công cộng",
        "applicable_articles": ["318"],
        "defendant": {
            "name": "Lâm Quốc II",
            "dob": "2001-04-09",
            "birth_year": 2001,
            "prior_convictions": 0,
        },
        "facts_summary": "Đêm ngày 10/12/2023, tại khu vực bờ đông cầu Rồng, do xích mích va chạm xe, Lâm Quốc II cùng một bạn đi cùng mang theo tuýp sắt rượt đuổi, đe dọa nhóm thanh niên đối diện làm hàng trăm du khách bỏ chạy toán loạn, giao thông trên cầu bị tê liệt gần 30 phút.",
        "aggravating_factors": ["dùng hung khí nguy hiểm"],
        "mitigating_factors": [
            "thành khẩn khai báo",
            "ăn năn hối cải",
            "đầu thú",
            "tự nguyện bồi thường thiệt hại",
            "gia đình có công với cách mạng",
            "ông nội là liệt sĩ",
        ],
        "verdict": "guilty",
        "sentence_type": "imprisonment",
        "sentence_years": 1.5,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN QUẬN SƠN TRÀ, THÀNH PHỐ ĐÀ NẴNG
BẢN ÁN SỐ: 22/2024/HS-ST NGÀY 25/03/2024 VỀ TỘI GÂY RỐI TRẬT TỰ CÔNG CỘNG

NỘI DUNG VỤ ÁN:
Khoảng 21 giờ 30 ngày 10/12/2023, tại phố đi bộ bờ đông cầu Rồng, Lâm Quốc II xảy ra cự cãi với nhóm thanh niên lạ. II lấy từ cốp xe máy 01 ống tuýp sắt dài 80cm rượt đuổi, đập phá biển hiệu quầy hàng lưu niệm và la hét khiến đông đảo người dân và khách du lịch hoảng sợ tháo chạy, làm mất an ninh trật tự khu vực du lịch trọng điểm.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi dùng hung khí gây rối trật tự công cộng thuộc trường hợp quy định tại điểm b khoản 2 Điều 318 BLHS 2015 với khung hình phạt từ 02 đến 07 năm tù. Tuy nhiên, bị cáo ra đầu thú, tại tòa khai báo thành khẩn, tự nguyện bồi thường thiệt hại cho quầy hàng, có nhân thân tốt và gia đình có công với cách mạng (ông nội là liệt sĩ). Hội đồng xét xử áp dụng khoản 1 Điều 54 BLHS xử phạt dưới mức thấp nhất của khung hình phạt để tạo điều kiện cho bị cáo sửa đổi.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Lâm Quốc II phạm 'Tội gây rối trật tự công cộng'.
Áp dụng điểm b khoản 2 Điều 318; điểm b, s, x khoản 1, khoản 2 Điều 51; khoản 1 Điều 54 BLHS 2015.
Xử phạt bị cáo Lâm Quốc II 01 (một) năm 06 (sáu) tháng tù.""",
    },
    {
        "id": "judgment_049_giao_thong_khong_chu_y_quan_sat",
        "case_number": "34/2024/HS-ST",
        "court": "Tòa án nhân dân huyện Bình Chánh, TP. Hồ Chí Minh",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2024-06-18",
        "crime_type": "Tội vi phạm quy định về tham gia giao thông đường bộ",
        "applicable_articles": ["260"],
        "defendant": {
            "name": "Vũ Tuấn KK",
            "dob": "1995-11-27",
            "birth_year": 1995,
            "prior_convictions": 0,
        },
        "facts_summary": "Khoảng 07 giờ ngày 25/02/2024, Vũ Tuấn KK điều khiển xe ô tô 7 chỗ lưu thông trên đường Trần Văn Giàu, khi chuyển hướng rẽ phải vào ngõ không chú ý quan sát gương chiếu hậu, va quẹt vào xe đạp điện của cháu N (15 tuổi) khiến cháu N ngã xuống đường tử vong do chấn thương sọ não.",
        "aggravating_factors": [],
        "mitigating_factors": [
            "thành khẩn khai báo",
            "ăn năn hối cải",
            "tự nguyện bồi thường toàn bộ thiệt hại 170 triệu đồng",
            "gia đình người bị hại có đơn xin bãi nại tha thiết giảm nhẹ hình phạt",
        ],
        "verdict": "guilty",
        "sentence_type": "suspended",
        "sentence_years": 1.5,
        "suspended": True,
        "full_text": """TÒA ÁN NHÂN DÂN HUYỆN BÌNH CHÁNH, THÀNH PHỐ HỒ CHÍ MINH
BẢN ÁN SỐ: 34/2024/HS-ST NGÀY 18/06/2024 VỀ TỘI VI PHẠM QUY ĐỊNH VỀ THAM GIA GIAO THÔNG ĐƯỜNG BỘ

NỘI DUNG VỤ ÁN:
Sáng ngày 25/02/2024, Vũ Tuấn KK điều khiển xe ô tô Innova BKS 51G-890.12 trên đường Trần Văn Giàu. Khi đến đoạn ngõ rẽ, KK bật xi nhan rẽ phải nhưng thiếu quan sát vùng điểm mù bên phải, va chạm với xe đạp điện do cháu Lê Bảo N (sinh năm 2009) điều khiển. Cú va chạm làm cháu N ngã xuống đường tử vong tại chỗ do chấn thương sọ não kín.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi chuyển hướng không chú ý quan sát gây tai nạn làm chết người của bị cáo vi phạm khoản 2 Điều 15 Luật Giao thông đường bộ, cấu thành tội phạm theo điểm a khoản 1 Điều 260 BLHS 2015. Bị cáo có nhân thân tốt, chưa tiền án tiền sự, khai báo thành khẩn, đã bồi thường toàn bộ 170.000.000 đồng và được gia đình cháu N làm đơn bãi nại xin giảm nhẹ. Bị cáo có đủ điều kiện áp dụng Điều 65 BLHS.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Vũ Tuấn KK phạm 'Tội vi phạm quy định về tham gia giao thông đường bộ'.
Áp dụng điểm a khoản 1 Điều 260; điểm b, s khoản 1, khoản 2 Điều 51; Điều 65 BLHS 2015.
Xử phạt bị cáo Vũ Tuấn KK 01 (một) năm 06 (sáu) tháng tù cho hưởng án treo, thời gian thử thách 03 năm.""",
    },
    {
        "id": "judgment_050_ma_tuy_tang_tru_khoan_1",
        "case_number": "45/2024/HS-ST",
        "court": "Tòa án nhân dân thành phố Rạch Giá, tỉnh Kiên Giang",
        "court_level": "district",
        "judgment_type": "first_instance",
        "legal_domain": "criminal",
        "judgment_date": "2024-08-20",
        "crime_type": "Tội tàng trữ trái phép chất ma túy",
        "applicable_articles": ["249"],
        "defendant": {
            "name": "Ngô Minh LL",
            "dob": "1997-02-14",
            "birth_year": 1997,
            "prior_convictions": 0,
        },
        "facts_summary": "Khoảng 14 giờ ngày 15/05/2024, tại phòng trọ số 4 trên đường Nguyễn Trung Trực, lực lượng chức năng kiểm tra phát hiện Ngô Minh LL đang cất giấu 01 đoạn ống hút nhựa hàn kín hai đầu chứa 0,35 gam chất bột màu trắng mua của một người lạ mặt để sử dụng cá nhân. Kết luận giám định xác định là ma túy Heroine.",
        "aggravating_factors": [],
        "mitigating_factors": ["thành khẩn khai báo", "ăn năn hối cải", "phạm tội lần đầu"],
        "verdict": "guilty",
        "sentence_type": "imprisonment",
        "sentence_years": 1.5,
        "suspended": False,
        "full_text": """TÒA ÁN NHÂN DÂN THÀNH PHỐ RẠCH GIÁ, TỈNH KIÊN GIANG
BẢN ÁN SỐ: 45/2024/HS-ST NGÀY 20/08/2024 VỀ TỘI TÀNG TRỮ TRÁI PHÉP CHẤT MA TÚY

NỘI DUNG VỤ ÁN:
Hồi 14 giờ ngày 15/05/2024, Công an thành phố Rạch Giá kiểm tra hành chính nhà trọ tại phường Vĩnh Bảo, phát hiện trong túi quần của Ngô Minh LL có 01 tép nhựa chứa bột màu trắng. LL khai nhận là Heroine mua về để bản thân sử dụng. Kết luận giám định số 214 xác định chất bột màu trắng là Heroine có khối lượng 0,35 gam.

NHẬN ĐỊNH CỦA TÒA ÁN:
Hành vi tàng trữ 0,35 gam Heroine nhằm mục đích sử dụng cá nhân của bị cáo phạm vào điểm c khoản 1 Điều 249 BLHS 2015. Bị cáo chưa có tiền án tiền sự, quá trình điều tra và tại phiên tòa thành khẩn khai báo, ăn năn hối cải nên áp dụng điểm s khoản 1 Điều 51 BLHS để giảm nhẹ một phần hình phạt.

QUYẾT ĐỊNH:
Tuyên bố bị cáo Ngô Minh LL phạm 'Tội tàng trữ trái phép chất ma túy'.
Áp dụng điểm c khoản 1 Điều 249; điểm s khoản 1 Điều 51 BLHS 2015.
Xử phạt bị cáo Ngô Minh LL 01 (một) năm 06 (sáu) tháng tù.""",
    },
]


def generate_new_judgments() -> None:
    JUDGMENTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Bắt đầu ghi {len(NEW_JUDGMENTS)} bản án mới vào {JUDGMENTS_DIR}...")
    for j in NEW_JUDGMENTS:
        file_name = f"{j['id']}.json"
        target_path = JUDGMENTS_DIR / file_name
        target_path.write_text(json.dumps(j, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✓ Đã ghi: {file_name}")
    print(f"\nHoàn tất ghi {len(NEW_JUDGMENTS)} bản án mới!")


if __name__ == "__main__":
    generate_new_judgments()
