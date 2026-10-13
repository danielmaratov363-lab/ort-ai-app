import streamlit as st
import time
from google import genai
from google.genai import types

# ---------------- НАСТРОЙКИ ----------------

st.set_page_config(
    page_title="ORT AI",
    page_icon="🎓",
    layout="centered"
)

MODEL = "gemini-3.5-flash-lite"
MAX_OUTPUT_TOKENS = 2048

SYSTEM_PROMPT = """
Ты — ORT AI, опытный ИИ-репетитор для подготовки к ОРТ в Кыргызстане.

Правила:
1. Отвечай на русском или кыргызском языке — в зависимости от языка ученика.
2. Объясняй подробно, понятно и пошагово.
3. В математике показывай формулы, вычисления и итоговый ответ.
4. В логике объясняй ход рассуждений.
5. Если пользователь отправил фотографию задания, прочитай условие и реши его по шагам.
6. Если фотография нечёткая, попроси прислать более чёткую.
7. Не выдумывай информацию, которой нет в условии.
8. Будь дружелюбным и терпеливым учителем.
9. Помогай ученику понять решение, а не только получить ответ.
10. По возможности добавляй похожий пример для самостоятельной практики.
"""

# ---------------- ПОДКЛЮЧЕНИЕ К GEMINI ----------------

@st.cache_resource
def get_client():
    api_key = st.secrets.get("GEMINI_API_KEY", "")

    if not api_key:
        return None

    return genai.Client(
        api_key=api_key,
        http_options={"timeout": 90000}
    )


def ask_ai(prompt, image_bytes=None, mime_type="image/jpeg"):
    client = get_client()

    if client is None:
        return (
            "⚠️ Не найден GEMINI_API_KEY. "
            "Проверь Secrets в настройках Streamlit."
        )

    contents = [prompt]

    if image_bytes:
        contents.append(
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            )
        )

    last_error = None

    # Повторяем запрос один раз при временной ошибке
    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.4,
                    max_output_tokens=MAX_OUTPUT_TOKENS
                )
            )

            if response.text:
                return response.text

            return "ИИ не вернул текст. Попробуй задать вопрос иначе."

        except Exception as e:
            last_error = e
            error = str(e).lower()

            temporary_error = any(
                code in error
                for code in [
                    "503",
                    "504",
                    "429",
                    "unavailable",
                    "deadline_exceeded",
                    "resource_exhausted"
                ]
            )

            if attempt == 0 and temporary_error:
                time.sleep(2)
                continue

            break

    error = str(last_error).lower()

    if "503" in error or "unavailable" in error:
        return (
            "⚠️ **Gemini временно недоступен.**\n\n"
            "Подожди немного и попробуй снова. "
            "Это может быть временная проблема сервера Google."
        )

    if "504" in error or "deadline_exceeded" in error:
        return (
            "⏳ **Gemini не успел ответить вовремя.**\n\n"
            "Попробуй ещё раз через минуту. "
            "Если ошибка повторяется, нужно проверить доступность модели."
        )

    if "429" in error or "resource_exhausted" in error:
        return (
            "⚠️ **Достигнут лимит запросов Gemini.**\n\n"
            "Проверь лимиты API или попробуй позже."
        )

    if "404" in error or "not_found" in error:
        return (
            f"⚠️ Модель `{MODEL}` не найдена или недоступна. "
            "Нужно проверить список моделей, доступных твоему API-ключу."
        )

    if "403" in error or "permission_denied" in error:
        return (
            "⚠️ Нет доступа к Gemini API. "
            "Проверь API-ключ и разрешения."
        )

    return (
        "⚠️ Не удалось получить ответ.\n\n"
        f"Техническая информация: `{str(last_error)[:500]}`"
    )


# ---------------- СОСТОЯНИЕ ПРИЛОЖЕНИЯ ----------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False


# ---------------- ЗАГОЛОВОК ----------------

st.title("🎓 ORT AI")
st.caption("Твой ИИ-помощник для подготовки к ОРТ")

chat_tab, quiz_tab = st.tabs(
    ["💬 ИИ-репетитор", "📝 Тесты ОРТ"]
)


# ---------------- ИИ-РЕПЕТИТОР ----------------

with chat_tab:
    st.subheader("Задай вопрос или отправь фото")

    uploaded = st.file_uploader(
        "📷 Загрузить фотографию задания",
        type=["png", "jpg", "jpeg", "webp"]
    )

    col1, col2, col3 = st.columns(3)

    quick_prompt = None

    if col1.button("➗ Дроби", use_container_width=True):
        quick_prompt = (
            "Объясни дроби для ОРТ подробно. "
            "Покажи правила и примеры с решениями."
        )

    if col2.button("📊 Проценты", use_container_width=True):
        quick_prompt = (
            "Объясни проценты для ОРТ. "
            "Покажи формулы и пошаговые решения примеров."
        )

    if col3.button("🧠 Логика", use_container_width=True):
        quick_prompt = (
            "Объясни логическое мышление для ОРТ "
            "и покажи примеры с подробными решениями."
        )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_prompt = st.chat_input("Напиши вопрос...")

    prompt = quick_prompt or user_prompt

    if prompt:
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        image_bytes = uploaded.getvalue() if uploaded else None
        mime_type = (
            uploaded.type
            if uploaded and uploaded.type
            else "image/jpeg"
        )

        with st.chat_message("assistant"):
            with st.spinner("ORT AI думает над ответом..."):
                answer = ask_ai(
                    prompt,
                    image_bytes=image_bytes,
                    mime_type=mime_type
                )

            st.markdown(answer)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

    if st.button("🧹 Очистить историю чата"):
        st.session_state.messages = []
        st.rerun()


# ---------------- ТРЕНИРОВОЧНЫЕ ТЕСТЫ ----------------

with quiz_tab:
    st.subheader("Мини-тест по математике и логике")

    questions = [
        {
            "q": "1. Сколько будет 25% от 800?",
            "options": ["100", "200", "250", "400"],
            "correct": 1,
            "explanation": "800 × 25 / 100 = 200."
        },
        {
            "q": "2. Вычисли: 3/4 + 1/8",
            "options": ["4/12", "7/8", "1", "5/8"],
            "correct": 1,
            "explanation": "3/4 = 6/8. Поэтому 6/8 + 1/8 = 7/8."
        },
        {
            "q": "3. Продолжи ряд: 2, 6, 18, 54, ...",
            "options": ["108", "162", "216", "56"],
            "correct": 1,
            "explanation": "Каждое число умножается на 3. 54 × 3 = 162."
        },
        {
            "q": "4. Товар стоил 800 сомов. Цена снизилась на 25%. Новая цена?",
            "options": ["200 сомов", "600 сомов", "700 сомов", "750 сомов"],
            "correct": 1,
            "explanation": "25% от 800 = 200. Новая цена: 800 − 200 = 600 сомов."
        },
        {
            "q": "5. Все квадраты — прямоугольники. Все прямоугольники — фигуры. Значит ли это, что все квадраты — фигуры?",
            "options": [
                "Да",
                "Нет",
                "Только некоторые",
                "Нельзя определить"
            ],
            "correct": 0,
            "explanation": "Да. Если каждый квадрат является прямоугольником, а каждый прямоугольник — фигурой, то каждый квадрат является фигурой."
        }
    ]

    with st.form("ort_test"):
        selected_answers = []

        for i, question in enumerate(questions):
            answer = st.radio(
                question["q"],
                question["options"],
                index=None,
                key=f"question_{i}"
            )
            selected_answers.append(answer)

        submitted = st.form_submit_button(
            "Проверить ответы",
            use_container_width=True
        )

    if submitted:
        score = 0

        for i, question in enumerate(questions):
            if selected_answers[i] == question["options"][question["correct"]]:
                score += 1

        st.session_state.quiz_submitted = True
        st.session_state.quiz_score = score
        st.session_state.quiz_answers = selected_answers

    if st.session_state.quiz_submitted:
        st.success(
            f"Твой результат: {st.session_state.quiz_score} из {len(questions)}"
        )

        with st.expander("Посмотреть решения", expanded=True):
            for i, question in enumerate(questions):
                correct = question["options"][question["correct"]]
                selected = st.session_state.quiz_answers[i]

                st.markdown(f"**{question['q']}**")

                if selected == correct:
                    st.write(f"✅ Правильно: {correct}")
                else:
                    st.write(f"❌ Твой ответ: {selected or 'не выбран'}")
                    st.write(f"✅ Правильный ответ: {correct}")

                st.caption(question["explanation"])

        if st.button("Пройти тест заново"):
            st.session_state.quiz_submitted = False
            st.rerun()


# ---------------- ПОДВАЛ ----------------

st.divider()
st.caption(
    "ORT AI — учебный помощник для подготовки к Общереспубликанскому тестированию."
)
