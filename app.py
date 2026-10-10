import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="ОРТ AI",
    page_icon="🎓",
    layout="centered"
)

st.title("🎓 ОРТ AI")
st.caption("Твой ИИ-репетитор для подготовки к ОРТ в Кыргызстане")

SYSTEM_PROMPT = """
Ты — ОРТ AI, терпеливый и профессиональный репетитор.
Помогай ученикам готовиться к ОРТ в Кыргызстане.

Объясняй математику, дроби, проценты, уравнения,
аналогии, чтение, грамотность и логику.

Объясняй сложные задачи пошагово.
Проверяй вычисления и объясняй ошибки.
Не выдумывай официальные правила ОРТ и проходные баллы.
Не называй созданные упражнения официальными заданиями.

Отвечай на русском языке, если ученик не попросил другой.
Если ученик пишет на кыргызском, отвечай на кыргызском.

В режиме обучения объясняй тему с нуля.
В режиме практики предлагай тренировочные задачи.
В режиме проверки знаний задавай вопросы по одному
и не раскрывай ответ до попытки ученика.
В режиме разбора ошибок объясняй, где и почему
ученик ошибся.
"""

# API-ключ
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    if not API_KEY or not API_KEY.strip():
        st.error("API-ключ пустой. Проверь настройки Secrets.")
        st.stop()
except (KeyError, FileNotFoundError):
    st.error(
        "Не найден GEMINI_API_KEY. "
        "Добавь ключ в Settings → Secrets в Streamlit."
    )
    st.stop()

# Клиент Gemini
client = genai.Client(api_key=API_KEY)

# Настройки обучения
with st.sidebar:
    st.header("📚 Настройки")

    mode = st.selectbox(
        "Режим обучения",
        [
            "Обучение",
            "Практика",
            "Проверка знаний",
            "Разбор ошибок"
        ]
    )

    subject = st.selectbox(
        "Предмет",
        [
            "Все предметы",
            "Математика",
            "Дроби и проценты",
            "Уравнения",
            "Аналогии",
            "Чтение",
            "Грамотность",
            "Логика"
        ]
    )

    language = st.selectbox(
        "Язык",
        ["Русский", "Кыргызский"]
    )

    if st.button("🗑️ Очистить переписку"):
        st.session_state.messages = []
        st.rerun()

# История
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Выбор моделей.
# Если модель недоступна, попробуем следующую.
MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash"
]

MODE_INSTRUCTIONS = {
    "Обучение": "Объясняй тему с нуля и по шагам.",
    "Практика": "Предлагай упражнения и помогай тренироваться.",
    "Проверка знаний": (
        "Задавай вопросы по одному. "
        "Не раскрывай ответ до попытки ученика."
    ),
    "Разбор ошибок": (
        "Найди ошибки в рассуждениях ученика "
        "и объясни, как их исправить."
    )
}

def ask_gemini(question):
    conversation = []

    for message in st.session_state.messages[-10:]:
        conversation.append(
            types.Content(
                role=message["role"],
                parts=[types.Part(text=message["content"])]
            )
        )

    context = f"""
Предмет: {subject}.
Режим: {mode}.
Инструкция режима: {MODE_INSTRUCTIONS[mode]}.
Язык ответа: {language}.

Вопрос ученика:
{question}
"""

    conversation.append(
        types.Content(
            role="user",
            parts=[types.Part(text=context)]
        )
    )

    errors = []

    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=conversation,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.4,
                    max_output_tokens=2048
                )
            )

            if response.text:
                return response.text

            errors.append(f"{model}: пустой ответ")

        except Exception as error:
            errors.append(
                f"{model}: {type(error).__name__}: {error}"
            )

    # Подробности сохраняются в журналах Streamlit.
    print("Ошибки Gemini API:", errors)

    return (
        "⚠️ Не удалось получить ответ от ИИ.\n\n"
        "Проверь API-ключ, доступность моделей и лимиты API. "
        "Если проблема повторяется, открой Logs в Streamlit Cloud."
    )

# Примеры вопросов
st.subheader("💡 Попробуй спросить")

examples = st.columns(3)

if examples[0].button("Дроби"):
    st.session_state.pending_question = "Объясни, как решать дроби."
    st.rerun()

if examples[1].button("Проценты"):
    st.session_state.pending_question = "Объясни проценты на примерах."
    st.rerun()

if examples[2].button("Логика"):
    st.session_state.pending_question = "Дай тренировочную задачу на логику."
    st.rerun()

question = st.chat_input("Напиши свой вопрос по ОРТ...")

if "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")

if question and question.strip():
    question = question.strip()

    if len(question) > 10000:
        st.warning("Слишком длинный вопрос. Сократи его.")
        st.stop()

    st.session_state.messages.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Репетитор думает..."):
            try:
                answer = ask_gemini(question)
            except Exception:
                answer = (
                    "Произошла ошибка. "
                    "Попробуй ещё раз позже."
                )

        st.markdown(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )
