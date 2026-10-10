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

client = genai.Client(api_key=api_key)

# Системная инструкция, которая превращает ИИ в репетитора
SYSTEM_PROMPT = """
Ты — профессиональный, доброжелательный и терпеливый репетитор по подготовке к Общереспубликанскому тестированию (ОРТ) в Кыргызстане.
Твоя задача — помогать ученикам правильно решать задачи и глубоко понимать темы.
"""

# Поле для ввода вопроса пользователем
user_input = st.chat_input("Задай вопрос или напиши задачу по ОРТ...")

if user_input:
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Думаю над решением..."):
            try:
                response = client.models.generate_content(
                   model="gemini-2.5-flash", 
                    contents=user_input,
                    config={"system_instruction": SYSTEM_PROMPT}
                )
                st.write(response.text)
            except Exception as e:
                st.error(f"Произошла ошибка: {e}")
