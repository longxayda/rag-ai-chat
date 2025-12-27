def build_heritage_prompt(context_chunks: list[str]) -> str:
    context = "\n\n---\n\n".join(context_chunks)

    return f"""
      Bạn là chuyên gia nghiên cứu di sản văn hóa và thiên nhiên Việt Nam.

      CHỈ sử dụng thông tin có trong văn bản.
      KHÔNG suy đoán. KHÔNG bổ sung kiến thức bên ngoài.

      NHIỆM VỤ:
      Trích xuất DANH SÁCH DI SẢN (địa điểm, khu di tích, thắng cảnh).

      KHÔNG coi:
      - tên người
      - tổ chức
      - chính sách
      - hạ tầng
      là di sản.

      MỖI di sản gồm:
      - name (bắt buộc, không rỗng)
      - location (nếu có)
      - type: "Văn hóa" | "Thiên nhiên" | "Thiên nhiên & Văn hóa"
      - year (nếu không có → null)
      - description (1 đến 3 câu, ngắn)
      - image: null
      - category: "cultural" | "natural" | "mixed"

      QUY TẮC:
      - Không trùng name
      - Nếu KHÔNG có di sản → trả []
      - CHỈ JSON ARRAY
      - KHÔNG YAML
      - KHÔNG markdown
      - KHÔNG giải thích

      VĂN BẢN:
      {context}

      TRẢ VỀ DUY NHẤT JSON hợp lệ:
      CHỈ trả về MỘT JSON ARRAY thuần túy
      KHÔNG giải thích, KHÔNG chú thích
      [
        {{
          "name": "...",
          "location": "...",
          "type": "...",
          "year": null,
          "description": "...",
          "image": null,
          "category": "cultural"
        }}
      ]
"""

def build_people_prompt(context_chunks: list[str]) -> str:
    context = "\n\n---\n\n".join(context_chunks)

    return f"""
Bạn là nhà nghiên cứu lịch sử và văn hóa địa phương Việt Nam.

CHỈ sử dụng thông tin xuất hiện trong văn bản.
KHÔNG suy đoán.
KHÔNG bổ sung kiến thức bên ngoài.

NHIỆM VỤ:
Trích xuất DANH SÁCH CON NGƯỜI CỤ THỂ (nhân vật lịch sử, danh nhân, cá nhân tiêu biểu).

KHÔNG coi các đối tượng sau là con người:
- tổ chức
- tập thể
- chức danh chung (ví dụ: "lãnh đạo", "nhân dân")
- địa danh

MỖI người gồm:
- name (bắt buộc)
- birth_year (nếu không có → null)
- death_year (nếu không có → null)
- role (vai trò / nghề nghiệp chính, ngắn gọn)
- associated_place (địa phương gắn liền, nếu có)
- description (1 đến 3 câu, dựa trên văn bản)

QUY TẮC:
- Không trùng name
- Nếu KHÔNG có con người → trả []
- CHỈ JSON ARRAY
- KHÔNG markdown
- KHÔNG giải thích
- KHÔNG YAML

VĂN BẢN:
{context}

TRẢ VỀ DUY NHẤT JSON hợp lệ:
[
  {{
    "name": "...",
    "birth_year": null,
    "death_year": null,
    "role": "...",
    "associated_place": "...",
    "description": "..."
  }}
]
"""



def build_festival_prompt(context_chunks: list[str]) -> str:
    context = "\n\n---\n\n".join(context_chunks)

    return f"""
Bạn là chuyên gia nghiên cứu lễ hội và văn hóa dân gian Việt Nam.

Dưới đây là các đoạn văn bản trích từ tài liệu gốc.
CHỈ sử dụng thông tin xuất hiện trong văn bản.
KHÔNG suy đoán. KHÔNG bổ sung kiến thức bên ngoài.

NHIỆM VỤ:
Trích xuất CHỈ các LỄ HỘI hoặc SINH HOẠT VĂN HÓA
được mô tả rõ ràng trong văn bản.

❌ KHÔNG trích xuất:
- Hoạt động thường nhật
- Chương trình du lịch hiện đại
- Sự kiện hành chính

CẤU TRÚC MỖI LỄ HỘI:

{
  "name": string,
  "location": string | null,
  "time": string | null,
  "description": string,
  "type": "traditional" | "folk" | "religious" | "cultural"
}

QUY TẮC:
- Không trùng lặp
- Không suy đoán thời gian nếu không có
- description: 1–3 câu

YÊU CẦU:
- CHỈ JSON ARRAY
- KHÔNG markdown
- KHÔNG text ngoài JSON

VĂN BẢN:
{context}

TRẢ VỀ DUY NHẤT JSON hợp lệ.
"""
