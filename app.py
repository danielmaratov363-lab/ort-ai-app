import streamlit as st
from google import genai

# Настройки страницы сайта
st.set_page_config(page_title="ОРТ-Репетитор | ИИ Помощник", page_icon="🎓")

st.title("🎓 ИИ-Репетитор по ОРТ")
st.caption("Подготовка к Общереспубликанскому тестированию 2026/2027")

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

Правила твоей работы:
1. При решении задач по математике и логике ОРТ: не давай сразу готовый вариант ответа (A, B, V, G). Объясняй ход мыслей пошагово и задавай наводящие вопросы.
2. Если ученик ошибается: мягко объясни, в чем именно ошибка, и подскажи верный ход.
3. При объяснении грамматики и аналогий: приводи понятные примеры в формате реальных вопросов ОРТ.
4. Отвечай четко, структурированно и простым языком.
"""

# Хранение истории переписки
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Поле ввода для сообщения
if user_input := st.chat_input("Задай вопрос или напиши задачу по ОРТ..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Отправка запроса в Gemini
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_input,
        config={"system_instruction": SYSTEM_PROMPT}
    )
    
    with st.chat_message("assistant"):
        st.markdown(response.text)
    st.session_state.messages.append({"role": "assistant", "content": response.text})