from openai import OpenAI

from app.core.config import settings


client = OpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)

MODEL_NAME = settings.openai_model


def generate_rag_answer(
    question: str,
    contexts: list[dict],
) -> str:
    context_text = "\n\n".join(
        [
            (
                f"[페이지 {item['page_number']}]\n"
                f"{item['text']}"
            )
            for item in contexts
        ]
    )

    system_prompt = """
당신은 LearnLoop의 AI 학습 코치입니다.

반드시 제공된 학습자료만을 근거로 답변하세요.

규칙:
1. 학습자료에 없는 내용을 추측하지 마세요.
2. 답을 찾을 수 없으면
   "제공된 학습자료에서 해당 내용을 찾을 수 없습니다."
   라고 답하세요.
3. 학생이 이해하기 쉽게 설명하세요.
4. 가능하면 근거 페이지 번호를 함께 알려주세요.
"""

    user_prompt = f"""
[학습자료]
{context_text}

[질문]
{question}
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )

    print("AI response:", response)

    answer = response.choices[0].message.content

    return answer or ""