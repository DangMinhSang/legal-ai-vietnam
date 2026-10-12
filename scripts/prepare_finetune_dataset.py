"""Script chuẩn bị dữ liệu huấn luyện Fine-tuning (SFT) chuyên ngành Luật Hình sự Việt Nam.

Chuyển đổi kho bản án và tri thức BLHS 2015 thành định dạng ChatML/JSONL chuẩn:
- Model đích: Qwen2.5-3B/7B-Instruct, PhoGPT-4B, Vistral-7B
- Phân chia: Train / Validation (theo mốc thời gian để tránh rò rỉ dữ liệu)
- Tác vụ huấn luyện đa dạng:
  1. Trích xuất thực thể & Phân tích vai trò đương sự (Legal NER & Role Dissection)
  2. Định tội danh & Xác định điều khoản định khung hình phạt (Crime & Clause Classification)
  3. Phân tích tình tiết Đ.51, Đ.52 & Cá thể hóa hình phạt theo Đ.54, Đ.65 (Legal Reasoning & Sentencing)
  4. Phân tích toàn diện từ văn bản tự do 1 khung (Full End-to-End Free-form Case Analysis)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JUDGMENTS_DIR = PROJECT_ROOT / "data" / "sample" / "judgments"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "finetune"

SYSTEM_PROMPT = (
    "Bạn là Chuyên gia AI Pháp lý Hình sự Việt Nam cao cấp. Nhiệm vụ của bạn là đọc hiểu hồ sơ vụ án, "
    "bóc tách chính xác các đương sự, xác định đúng tội danh, điều khoản định khung theo Bộ luật Hình sự 2015 "
    "(sửa đổi, bổ sung 2017), phân tích các tình tiết tăng nặng (Điều 52), giảm nhẹ (Điều 51), "
    "và đề xuất cá thể hóa hình phạt đúng nguyên tắc (Điều 54, Điều 65 BLHS)."
)


def create_instruction_sample(system: str, user_prompt: str, assistant_response: str) -> dict[str, Any]:
    """Tạo 1 mẫu dữ liệu theo chuẩn ChatML messages."""
    return {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": assistant_response},
        ]
    }


def generate_samples_from_judgment(jdata: dict[str, Any]) -> list[dict[str, Any]]:
    """Sinh các cặp instruction-response từ 1 bản án."""
    samples: list[dict[str, Any]] = []

    facts = jdata.get("facts_summary", "")
    def_info = jdata.get("defendant", {})
    def_name = def_info.get("name", "Bị cáo")
    priors = def_info.get("prior_convictions", 0)
    birth_year = def_info.get("birth_year", 1990)
    crime_type = jdata.get("crime_type", "Tội phạm hình sự")
    articles = jdata.get("applicable_articles", [])
    agg = jdata.get("aggravating_factors", [])
    mit = jdata.get("mitigating_factors", [])
    verdict = jdata.get("verdict", "guilty")
    years = jdata.get("sentence_years", 0.0)
    suspended = jdata.get("suspended", False)
    sentence_type = jdata.get("sentence_type", "imprisonment")

    # -------------------------------------------------------------
    # Task 1: Bóc tách đương sự & nhân thân (Entity Extraction)
    # -------------------------------------------------------------
    prompt_ner = (
        f"Hãy bóc tách danh sách đương sự (bị cáo, bị hại), nhân thân và tiền án tiền sự từ văn bản sau:\n\n"
        f"\"\"\"\n{facts}\n\"\"\""
    )
    ans_ner_dict = {
        "parties": [
            {
                "name": def_name,
                "role": "Bị cáo",
                "birth_year": birth_year,
                "prior_convictions": priors,
                "role_detail": "Bị cáo trực tiếp thực hiện hành vi" if verdict == "guilty" else "Người bị truy tố",
            }
        ]
    }
    samples.append(create_instruction_sample(SYSTEM_PROMPT, prompt_ner, json.dumps(ans_ner_dict, ensure_ascii=False, indent=2)))

    # -------------------------------------------------------------
    # Task 2: Định danh tội danh và điều luật (Crime Classification)
    # -------------------------------------------------------------
    articles_str = ", ".join([f"Điều {a}" for a in articles])
    prompt_crime = (
        f"Dựa trên các tình tiết vụ việc sau đây, hãy xác định tội danh và các điều luật áp dụng theo BLHS 2015:\n\n"
        f"Tình tiết vụ việc: {facts}"
    )
    ans_crime = (
        f"Căn cứ vào hành vi và hậu quả trong vụ việc:\n"
        f"- Tội danh xác định: {crime_type}\n"
        f"- Điều luật áp dụng: {articles_str} Bộ luật Hình sự 2015 (sửa đổi, bổ sung 2017).\n"
        f"- Căn cứ pháp lý: Hành vi thỏa mãn đầy đủ các yếu tố cấu thành tội phạm theo quy định của điều luật nêu trên."
    )
    samples.append(create_instruction_sample(SYSTEM_PROMPT, prompt_crime, ans_crime))

    # -------------------------------------------------------------
    # Task 3: Phân tích toàn diện & Đề xuất mức án cá thể hóa
    # -------------------------------------------------------------
    prompt_full = (
        f"Phân tích toàn diện hồ sơ vụ án hình sự sau và đưa ra kết luận pháp lý kèm mức án đề xuất:\n\n"
        f"Hồ sơ vụ án: {facts}\n"
        f"Thông tin bị cáo: {def_name}, sinh năm {birth_year}, tiền án: {priors}."
    )

    penalty_desc = f"{years} năm tù"
    if suspended:
        penalty_desc += " (Cho hưởng án treo theo Điều 65 BLHS)"
    elif sentence_type == "non_custodial":
        penalty_desc = f"{years} năm cải tạo không giam giữ (Điều 36 BLHS)"
    elif verdict == "not_guilty":
        penalty_desc = "Tuyên bố KHÔNG CÓ TỘI (0.0 năm tù)"

    ans_full_dict = {
        "verdict": "CÓ TỘI" if verdict == "guilty" else "VÔ TỘI",
        "crime_name": crime_type,
        "applicable_articles": articles,
        "aggravating_factors": agg,
        "mitigating_factors": mit,
        "recommended_sentence": penalty_desc,
        "legal_reasoning": (
            f"Bị cáo {def_name} phạm {crime_type}. "
            f"Về tình tiết tăng nặng: {', '.join(agg) if agg else 'Không có'}. "
            f"Về tình tiết giảm nhẹ: {', '.join(mit) if mit else 'Không có'}. "
            f"Mức hình phạt đề xuất: {penalty_desc} bảo đảm tính nghiêm minh và cá thể hóa hình phạt."
        ),
    }
    samples.append(create_instruction_sample(SYSTEM_PROMPT, prompt_full, json.dumps(ans_full_dict, ensure_ascii=False, indent=2)))

    return samples


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    judgment_files = sorted(list(JUDGMENTS_DIR.glob("*.json")))
    print(f"[*] Tìm thấy {len(judgment_files)} bản án trong {JUDGMENTS_DIR}")

    train_samples: list[dict[str, Any]] = []
    val_samples: list[dict[str, Any]] = []

    # Phân chia theo ranh giới thời gian 2022-01-01 để chuẩn phương pháp luận
    for fpath in judgment_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)

            jdate = data.get("judgment_date", "2021-01-01")
            year = int(jdate.split("-")[0]) if "-" in jdate else 2021

            samples = generate_samples_from_judgment(data)
            if year >= 2022:
                val_samples.extend(samples)
            else:
                train_samples.extend(samples)
        except Exception as e:
            print(f"[!] Lỗi đọc file {fpath.name}: {e}")

    # Ghi ra file JSONL
    train_file = OUTPUT_DIR / "legal_sft_train.jsonl"
    val_file = OUTPUT_DIR / "legal_sft_val.jsonl"
    all_file = OUTPUT_DIR / "legal_sft_all.jsonl"

    all_samples = train_samples + val_samples

    with open(train_file, "w", encoding="utf-8") as f:
        for s in train_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    with open(val_file, "w", encoding="utf-8") as f:
        for s in val_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    with open(all_file, "w", encoding="utf-8") as f:
        for s in all_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print("[+] Đã tạo tập dữ liệu Fine-tuning SFT thành công:")
    print(f"    - Tập Huấn luyện (Train < 2022): {len(train_samples)} mẫu -> {train_file}")
    print(f"    - Tập Kiểm thử (Val >= 2022): {len(val_samples)} mẫu -> {val_file}")
    print(f"    - Tổng cộng (Toàn bộ): {len(all_samples)} mẫu -> {all_file}")


if __name__ == "__main__":
    main()
