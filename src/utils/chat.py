from typing import AsyncGenerator, List, Tuple
from ollama import AsyncClient

llm_client = AsyncClient()

# def format_context(results: list[dict]) -> str:
#     contexts = []

#     for item in results:
#         text = item["text"]
#         metadata = item.get("metadata", {})
#         distance = item.get("distance")
        
#         contexts.append(
#             f"[Source | distance={distance:.4f}]\n{text}"
#         )

#     return "\n\n---\n\n".join(contexts)

def format_context(results: list[dict]) -> str:
    return "\n\n".join(
        item.get("text", "").strip()
        for item in results
        if item.get("text")
    )




def build_rag_prompt_v3(user_query: str, context_str: str) -> str:
    prompt = f"""Bạn là trợ lý AI trả lời câu hỏi dựa trên tài liệu được cung cấp.
Ghi nhớ các yêu cầu sau:
1. Các ngữ cảnh dưới đây đã được hệ thống chọn lọc là những nội dung liên quan nhất đến câu hỏi.
2. Trả lời sử dụng chính xác thông tin văn bản của 1-2 ngữ cảnh đầu tiên.
3. Nếu thông tin từ bối cảnh thứ 2 trở đi có mâu thuẫn với thông tin từ ngữ cảnh đầu tiên, sử dụng thông tin ngữ cảnh đầu tiên.
4. Nếu không có thông tin, hãy nói rõ rằng tài liệu không cung cấp câu trả lời.
BÂY GIỜ, Sử dụng CÁC NGỮ CẢNH dưới đây để trả lời CÂU HỎI.
------------------
NGỮ CẢNH:
{context_str}
------------------
CÂU HỎI:
{user_query}
------------------
CÂU TRẢ LỜI:
""" 
    return prompt


def build_rag_prompt(user_query: str, context_str: str) -> str:
    """
    Prompt cho giai đoạn Augmented của RAG.
    Buộc LLM trả lời dựa trên bằng chứng, giảm hallucination,
    và tránh từ chối sai khi đã có đủ dữ liệu.
    """
    return f"""
Bạn là một trợ lý AI chuyên trả lời câu hỏi dựa trên tài liệu truy hồi (RAG).
Nhiệm vụ của bạn là **suy luận và trả lời câu hỏi CHỈ dựa trên NGỮ CẢNH được cung cấp**.

---

## NGỮ CẢNH (DỮ LIỆU TRUY HỒI) ##
{context_str}

---

## QUY TRÌNH SUY LUẬN BẮT BUỘC ##
Trước khi trả lời, bạn phải tuân thủ đúng các bước sau (thực hiện nội bộ, KHÔNG hiển thị):

1. **Kiểm tra ngữ cảnh**
   - Xác định xem ngữ cảnh có chứa thông tin liên quan trực tiếp đến câu hỏi hay không.

2. **Đánh giá mức độ đầy đủ**
   - Đủ thông tin → trả lời đầy đủ
   - Chỉ đủ một phần → trả lời phần có căn cứ
   - Không có thông tin → từ chối đúng quy định

3. **Ràng buộc kiến thức**
   - Tuyệt đối KHÔNG sử dụng kiến thức bên ngoài, suy đoán, hoặc “kiến thức phổ thông”.

---

## QUY TẮC TRẢ LỜI ##
### 1. Khi CÓ thông tin trong ngữ cảnh
- Trả lời **đúng trọng tâm câu hỏi**
- Có thể diễn giải lại cho dễ hiểu nhưng **KHÔNG làm thay đổi nội dung gốc**
- Chỉ sử dụng thông tin xuất hiện trong ngữ cảnh
- Nếu cần, có thể trích dẫn ngắn từ ngữ cảnh

### 2. Khi thông tin CHỈ CÓ MỘT PHẦN
- Trả lời phần có thể xác nhận
- BẮT BUỘC nêu rõ phần nào chưa có thông tin
- Không được suy diễn phần còn thiếu

### 3. Khi KHÔNG CÓ thông tin
- Chỉ được trả lời đúng câu sau (không thêm bớt):
> "Tôi không tìm thấy thông tin để trả lời câu hỏi này trong tài liệu được cung cấp."

---

## QUY ĐỊNH CẤM ##
- ❌ Không bịa đặt
- ❌ Không suy luận ngoài dữ liệu
- ❌ Không dùng kiến thức đã biết trước
- ❌ Không trả lời chung chung nếu ngữ cảnh đã đủ chi tiết

---

## ĐỊNH DẠNG CÂU TRẢ LỜI ##
- Ngắn gọn, chính xác
- Ưu tiên gạch đầu dòng nếu có nhiều ý
- Ngôn ngữ rõ ràng, phù hợp học sinh – giáo viên

---

## CÂU HỎI ##
{user_query}

---

## CÂU TRẢ LỜI ##
""".strip()


def build_rag_prompt_v2(user_query: str, context_str: str) -> str:
    """
    Prompt Augmented RAG có xét độ tương đồng (distance)
    nhằm tăng độ chính xác và giảm hallucination.
    """
    return f"""
Bạn là một trợ lý AI trả lời câu hỏi dựa trên hệ thống RAG (Retrieval-Augmented Generation).
Bạn **CHỈ được phép sử dụng thông tin từ các NGỮ CẢNH bên dưới** để trả lời.

Mỗi ngữ cảnh gồm:
- `text`: nội dung trích xuất
- `source`: nguồn tài liệu gốc
- `distance`: khoảng cách vector (distance càng nhỏ → mức độ liên quan và độ tin cậy càng cao)

---

## NGỮ CẢNH TRUY HỒI ##
{context_str}

---

## QUY TẮC SUY LUẬN BẮT BUỘC (THỰC HIỆN NỘI BỘ) ##
1. **Đánh giá mức độ liên quan**
   - Ưu tiên sử dụng các ngữ cảnh có `distance` nhỏ nhất.
   - Chỉ sử dụng ngữ cảnh có nội dung liên quan trực tiếp đến câu hỏi.

2. **Trọng số độ tin cậy**
   - Nếu nhiều ngữ cảnh cùng đề cập một thông tin:
     → Ưu tiên ngữ cảnh có `distance` nhỏ hơn.
   - Không kết hợp thông tin mâu thuẫn từ các ngữ cảnh có `distance` lớn.

3. **Kiểm tra độ đầy đủ**
   - Nếu ngữ cảnh có distance nhỏ **đủ thông tin** → trả lời đầy đủ.
   - Nếu chỉ có thông tin rời rạc → trả lời phần có căn cứ.
   - Nếu các ngữ cảnh có distance lớn hoặc không liên quan → coi như **không có thông tin**.

4. **Ràng buộc tri thức**
   - Không suy diễn ngoài `text`.
   - Không dùng kiến thức nền hoặc thông tin phổ thông.

---

## QUY TẮC TRẢ LỜI ##
### 1. Khi CÓ thông tin đáng tin cậy
- Trả lời đúng trọng tâm câu hỏi.
- Có thể diễn giải lại nhưng **không làm sai nội dung gốc**.
- Có thể nêu nguồn tài liệu (`source`) nếu cần làm rõ.

### 2. Khi thông tin CHỈ ĐỦ MỘT PHẦN
- Trả lời phần có thể xác nhận từ ngữ cảnh `distance` nhỏ.
- Nêu rõ phần nào **chưa có thông tin trong tài liệu**.

### 3. Khi KHÔNG CÓ thông tin phù hợp
- Chỉ được trả lời đúng câu sau:
> "Tôi không tìm thấy thông tin để trả lời câu hỏi này trong tài liệu được cung cấp."

---

## QUY ĐỊNH CẤM ##
- ❌ Không bịa đặt
- ❌ Không suy đoán
- ❌ Không tổng hợp từ ngữ cảnh có distance lớn nếu không liên quan
- ❌ Không trả lời mơ hồ khi ngữ cảnh đã đủ rõ

---

## ĐỊNH DẠNG CÂU TRẢ LỜI ##
- Ngắn gọn, chính xác
- Ưu tiên gạch đầu dòng nếu có nhiều ý
- Ngôn ngữ rõ ràng, phù hợp giáo dục

---

## CÂU HỎI ##
{user_query}

---

## CÂU TRẢ LỜI ##
""".strip()




async def stream_generator(prompt: str, model: str) -> AsyncGenerator[str, None]:
    """
    Streams the response from Ollama asynchronously.
    """
    try:
        stream = await llm_client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        async for chunk in stream:
            
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content
            if chunk.done:
                print(f"How long the response took to generate: {chunk.total_duration / 1000000000}")
                print(f"How long the model took to load: {chunk.load_duration / 1000000000}")
                print(f"Output tokens were processes: {chunk.eval_count}")
                print(f"How long it took to generate the output tokens: {chunk.eval_duration / 1000000000}")

    except Exception as e:
        yield f"\n[Error generating response: {str(e)}]"