import streamlit as st
from google import genai

# Настройки страницы сайта
st.set_page_config(page_title="ИИ-Репетитор по ОРТ", page_icon="🎓")

st.title("🎓 ИИ-Репетитор по ОРТ")
st.subheader("Подготовка к Общереспубликанскому тестированию 2026/2027")

# Получение API ключа из секретных настроек
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("Ошибка: API-ключ не найден. Добавьте GEMINI_API_KEY в Secrets.")
    st.stop()

# Инициализация клиента Google GenAI
client = genai.Client(api_key=api_key)

# Подробная инструкция репетитора для качественных ответов
SYSTEM_PROMPT = """
Ты — профессиональный, доброжелательный и терпеливый репетитор по подготовке к Общереспубликанскому тестированию (ОРТ) в Кыргызстане.
Твоя задача — не просто давать ответ, а помогать ученикам глубоко понимать тему.
Всегда объясняй логику решения задач пошагово, приводи понятные примеры и в конце предлагай ученику похожую задачку для тренировки, чтобы он закрепил материал.
"""

# Поле для ввода вопроса пользователем
user_input = st.chat_input("Задай вопрос или напиши задачу по ОРТ...")

if user_input:
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        try:
            # Используем актуальную модель gemini-3.8-flash и потоковый вывод для скорости
            response_stream = client.models.generate_content_stream(
                model="gemini-3.8-flash",
                contents=user_input,
                config={"system_instruction": SYSTEM_PROMPT}
            )
            
            # Функция для вывода текста по кусочкам в реальном времени
            def stream_parser():
                for chunk in response_stream:
                    if chunk.text:
                        yield chunk.text

            st.write_stream(stream_parser)
            
        except Exception as e:
            st.error(f"Произошла ошибка: {e}")
