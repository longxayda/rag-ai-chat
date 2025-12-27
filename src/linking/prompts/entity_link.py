# linking/prompts/entity_link.py

def build_entity_link_prompt(text: str, name_a: str, name_b: str) -> str:
    return f"""
Dựa CHỈ vào đoạn văn sau.

Xác định xem "{name_a}" có liên quan TRỰC TIẾP đến "{name_b}" hay không.

CHỈ chấp nhận các quan hệ sau:
- sinh_ra_tai
- gan_lien_voi
- sang_lap
- to_chuc
- tham_gia
- thoi_cung
- dien_ra_tai
- quan_ly
- bao_ton

Nếu KHÔNG thấy mối quan hệ rõ ràng → related = false.

ĐOẠN VĂN:
{text}

CHỈ trả về JSON HỢP LỆ:
{{
  "related": true/false,
  "relation": "ten_quan_he" hoặc null
}}
"""
