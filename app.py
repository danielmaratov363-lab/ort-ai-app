import streamlit as st
from google import genai

st.set_page_config(page_title="ОРТ AI", page_icon="🎓")

st.title("🎓 ОРТ AI")
st.subheader("ИИ-репетитор для подготовки к ОРТ в Кыргызстане")

api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("Ошибка: API-ключ не найден в secrets.toml")
    st.stop()

client = genai.Client(api_key=api_key)

SYSTEM_PROMPT = "Ты — полезный репетитор по подготовке к ОРТ в Кыргызстане. Объясняй понятно и пошагово."

user_input = st.chat_input("Напиши свой вопрос по ОРТ...")

if user_input:
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Думаю..."):
            try:
                # Используем самую стабильную и актуальную модель
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=user_input,
                    config={"system_instruction": SYSTEM_PROMPT}
                )
                st.write(response.text)
            except Exception as e:
                # Теперь мы увидим точный текст ошибки, если она возникнет
                st.error(f"Техническая ошибка: {e}")
