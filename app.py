import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="ОРТ AI", page_icon="🎓")

st.title("🎓 ОРТ AI")
st.caption("ИИ-репетитор для подготовки к ОРТ в Кыргызстане")

SYSTEM_PROMPT = """
Ты — ОРТ AI, терпеливый репетитор.
Объясняй математику, дроби, проценты, уравнения,
аналогии, чтение и логику простым языком.
Решай задачи пошагово и проверяй вычисления.
Не выдумывай официальные правила ОРТ.
Отвечай на языке, выбранном учеником.
В режиме проверки знаний задавай вопросы по одному.
"""

try:
    api_key = st.secrets["GEMINI_API_KEY"].strip()
    if not api_key:
        st.error("API-ключ пустой.")
        st.stop()
except (KeyError, FileNotFoundError):
    st.error("Добавь GEMINI_API_KEY в Streamlit → Settings → Secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

with st.sidebar:
    st.header("📚 Настройки")

    mode = st.selectbox(
        "Режим",
        ["Обучение", "Практика", "Проверка знаний", "Разбор ошибок"]
    )

    subject = st.selectbox(
        "Предмет",
        ["Все предметы", "Математика", "Дроби и проценты",
         "Уравнения", "Аналогии", "Чтение", "Грамотность", "Логика"]
    )

    language = st.selectbox("Язык", ["Русский", "Кыргызский"])

    if st.button("Очистить переписку"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

st.subheader("💡 Попробуй спросить")

col1, col2, col3 = st.columns(3)

if col1.button("Дроби"):
    st.session_state.pending = "Объясни, как решать дроби."

if col2.button("Проценты"):
    st.session_state.pending = "Объясни проценты на примерах."

if col3.button("Логика"):
    st.session_state.pending = "Дай тренировочную задачу на логику."

question = st.chat_input("Напиши свой вопрос по ОРТ...")

if "pending" in st.session_state:
    question = st.session_state.pop("pending")

MODE_INSTRUCTIONS = {
    "Обучение": "Объясняй тему с нуля, по шагам.",
    "Практика": "Предлагай упражнения для тренировки.",
    "Проверка знаний": "Задавай вопросы по одному, не раскрывай ответ заранее.",
    "Разбор ошибок": "Находи ошибки и объясняй, как их исправить."
}

if question and question.strip():
    question = question.strip()

    if len(question) > 10000:
        st.warning("Сократи сообщение до 10 000 символов.")
        st.stop()

    st.session_state.messages.append(
        {"role": "user", "content": question}
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            history = []

            for msg in st.session_state.messages[-11:-1]:
                history.append(
                    types.Content(
                        role=msg["role"],
                        parts=[types.Part(text=msg["content"])]
                    )
                )

            prompt = f"""
Предмет: {subject}
Режим: {mode}
Инструкция: {MODE_INSTRUCTIONS[mode]}
Язык ответа: {language}

Вопрос ученика: {question}
"""

            history.append(
                types.Content(
                    role="user",
                    parts=[types.Part(text=prompt)]
                )
            )

            answer = None
            errors = []

            # Перебираем модели, если одна недоступна
            for model in ["gemini-2.5-flash", "gemini-2.0-flash"]:
                try:
                    response = client.models.generate_content(
                        model=model,
                        contents=history,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            temperature=0.4,
                            max_output_tokens=2048
                        )
                    )

                    answer = response.text

                    if answer:
                        break

                    errors.append(f"{model}: пустой ответ")

                except Exception as exc:
                    errors.append(f"{model}: {type(exc).__name__}: {exc}")

            if not answer:
                print("Gemini API errors:", errors)
                st.error(
                    "Не удалось получить ответ от Gemini API. "
                    "Открой Logs в Streamlit Cloud для диагностики."
                )
                st.stop()

            st.markdown(answer)

            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )

        except Exception as exc:
            print("Ошибка приложения:", repr(exc))
            st.error(
                "Ошибка при обращении к ИИ. "
                "Подробности находятся в Logs Streamlit Cloud."
            )
