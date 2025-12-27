# linking/prompts/people_link.py

def build_people_link_prompt(text: str, name_a: str, name_b: str) -> str:
    return f"""
Dựa CHỈ vào đoạn văn sau.

"{name_a}" và "{name_b}" có mối quan hệ TRỰC TIẾP nào không?

CHỈ chấp nhận các loại quan hệ sau:
- cha_con
- me_con
- vo_chong
- anh_em
- ho_hang
- thay_tro
- dong_chi
- dong_doi
- hop_tac
- nguoi_ke_nhiem

Nếu KHÔNG rõ ràng → related = false.

ĐOẠN VĂN:
{text}

CHỈ trả JSON:
{{
  "related": true/false,
  "relation": "ten_quan_he" hoặc null
}}
"""
