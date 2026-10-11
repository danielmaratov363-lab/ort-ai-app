import streamlit as st
from google import genai
from google.genai import types
import json
import re

st.set_page_config(
    page_title="ОРТ AI",
    page_icon="🎓",
    layout="centered"
)

SYSTEM_PROMPT = """
Ты — опытный ИИ-репетитор для подготовки к Общереспубликанскому
тестированию (ОРТ) в Кыргызстане.

Твои задачи:
1. Объяснять математику, логику, аналогии и чтение.
2. Решать задания пошагово и понятным русским языком.
3. Помогать готовиться к ОРТ.
4. Если ученик прислал фотографию задания, прочитать её,
   определить условие и помочь решить.
5. Если изображение нечёткое, попросить прислать более чёткое.
6. Не выдумывать условия, которых нет на фотографии.
7. Объяснять ошибки ученика и показывать правильный способ решения.
"""

MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash"
]

SUBJECTS = [
    "Математика",
    "Логика",
    "Аналогии",
    "Чтение",
    "Общий тест ОРТ"
]

if "messages" not in st.session_state:
    st.session_state.messages = []

if "quiz" not in st.session_state:
    st.session_state.quiz = None

if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}


@st.cache_resource
def get_client():
    return genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )


def ask_gemini(prompt, image_bytes=None, mime_type="image/jpeg"):
    client = get_client()
    errors = []

    contents = [prompt]

    if image_bytes:
        contents.append(
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            )
        )

    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.4,
                    max_output_tokens=3000
                )
            )

            if response.text:
                return response.text

            errors.append(f"{model}: пустой ответ")

        except Exception as e:
            errors.append(f"{model}: {str(e)}")
            print(f"Ошибка Gemini ({model}): {e}")

    return None


def generate_quiz(subject, count, difficulty):
    prompt = f"""
Создай тест для подготовки к ОРТ в Кыргызстане.

Предмет: {subject}
Количество вопросов: {count}
Сложность: {difficulty}

Требования:
- Каждый вопрос должен иметь ровно 4 варианта ответа.
- Только один вариант правильный.
- Вопросы должны быть понятными и корректными.
- Не повторяй одинаковые вопросы.
- Для каждого вопроса дай короткое объяснение правильного ответа.
- Не добавляй текст до или после JSON.

Верни строго JSON такого формата:
{{
  "questions": [
    {{
      "question": "Текст вопроса",
      "options": [
        "Вариант A",
        "Вариант B",
        "Вариант C",
        "Вариант D"
      ],
      "answer": 0,
      "explanation": "Объяснение ответа"
    }}
  ]
}}

Поле answer — номер правильного варианта, начиная с 0.
"""

    result = ask_gemini(prompt)

    if not result:
        return None

    try:
        result = result.strip()
        result = re.sub(r"^```(?:json)?\s*", "", result)
        result = re.sub(r"\s*```$", "", result)

        data = json.loads(result)
        questions = data.get("questions", [])

        valid_questions = []

        for q in questions:
            if (
                isinstance(q, dict)
                and isinstance(q.get("question"), str)
                and isinstance(q.get("options"), list)
                and len(q["options"]) == 4
                and isinstance(q.get("answer"), int)
                and 0 <= q["answer"] < 4
            ):
                valid_questions.append(q)

        if not valid_questions:
            return None

        return valid_questions

    except Exception as e:
        print("Ошибка обработки теста:", e)
        return None


# Заголовок
st.title("🎓 ОРТ AI")
st.caption("ИИ-репетитор для подготовки к ОРТ в Кыргызстане")

st.divider()

# Боковая панель
with st.sidebar:
    st.header("⚙️ Настройки")

    subject = st.selectbox(
        "Выбери предмет",
        SUBJECTS
    )

    language = st.selectbox(
        "Язык объяснений",
        ["Русский", "Кыргызский", "Казахский"]
    )

    st.divider()

    st.markdown("### 📚 Возможности")
    st.write("✅ ИИ-репетитор")
    st.write("✅ Тесты по ОРТ")
    st.write("✅ Проверка ответов")
    st.write("✅ Решение заданий по фото")
    st.write("✅ Камера и загрузка изображений")

    if st.button("🗑️ Очистить историю чата"):
        st.session_state.messages = []
        st.rerun()


# Вкладки
tab_chat, tab_quiz = st.tabs([
    "💬 ИИ-репетитор",
    "📝 Тесты по ОРТ"
])


# ==========================================
# ВКЛАДКА 1: ИИ-РЕПЕТИТОР И ФОТО
# ==========================================

with tab_chat:
    st.subheader("💡 Задай свой вопрос")

    st.write(
        "Напиши вопрос или сфотографируй задание. "
        "ИИ поможет разобраться в решении."
    )

    with st.expander("📸 Сфотографировать или загрузить задание"):
        camera_photo = st.camera_input(
            "Сделай фотографию задания"
        )

        uploaded_photo = st.file_uploader(
            "Или выбери фотографию с устройства",
            type=["jpg", "jpeg", "png", "webp"]
        )

        if camera_photo is not None:
            st.success("Фото сделано!")

        elif uploaded_photo is not None:
            st.success("Фото загружено!")

    current_photo = None
    current_mime = "image/jpeg"

    if camera_photo is not None:
        current_photo = camera_photo.getvalue()
        current_mime = "image/jpeg"

    elif uploaded_photo is not None:
        current_photo = uploaded_photo.getvalue()

        if uploaded_photo.type in [
            "image/jpeg",
            "image/png",
            "image/webp"
        ]:
            current_mime = uploaded_photo.type

    st.divider()

    # Примеры вопросов
    st.markdown("#### Попробуй спросить")

    col1, col2, col3 = st.columns(3)

    example = None

    with col1:
        if st.button("Дроби", use_container_width=True):
            example = "Объясни дроби на простых примерах."

    with col2:
        if st.button("Проценты", use_container_width=True):
            example = "Объясни проценты на примерах."

    with col3:
        if st.button("Логика", use_container_width=True):
            example = "Дай пример задания на логику для ОРТ и объясни решение."

    # История чата
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_question = st.chat_input(
        "Напиши свой вопрос по ОРТ..."
    )

    if example:
        user_question = example

    if user_question:
        st.session_state.messages.append({
            "role": "user",
            "content": user_question
        })

        with st.chat_message("user"):
            st.markdown(user_question)

            if current_photo:
                st.image(
                    current_photo,
                    caption="Прикреплённое задание",
                    use_container_width=True
                )

        prompt = f"""
Язык ответа: {language}
Предмет: {subject}

Вопрос ученика:
{user_question}

Если прикреплена фотография, внимательно прочитай её.
Объясни решение пошагово и понятным языком.
"""

        with st.chat_message("assistant"):
            with st.spinner("ИИ решает задание..."):
                answer = ask_gemini(
                    prompt,
                    image_bytes=current_photo,
                    mime_type=current_mime
                )

            if answer:
                st.markdown(answer)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

            else:
                st.error(
                    "Не удалось получить ответ от Gemini API. "
                    "Проверь Logs в Streamlit Cloud."
                )


# ==========================================
# ВКЛАДКА 2: ТЕСТЫ ПО ОРТ
# ==========================================

with tab_quiz:
    st.subheader("📝 Тренировочный тест ОРТ")

    st.write(
        "Ответь на вопросы, а затем проверь результат "
        "и прочитай объяснения."
    )

    quiz_subject = st.selectbox(
        "Предмет теста",
        SUBJECTS,
        key="quiz_subject"
    )

    count = st.select_slider(
        "Количество вопросов",
        options=[5, 10, 15],
        value=5
    )

    difficulty = st.selectbox(
        "Сложность",
        ["Лёгкая", "Средняя", "Сложная"]
    )

    if st.button(
        "🚀 Создать новый тест",
        type="primary",
        use_container_width=True
    ):
        with st.spinner("Создаю вопросы для теста..."):
            new_quiz = generate_quiz(
                quiz_subject,
                count,
                difficulty
            )

        if new_quiz:
            st.session_state.quiz = new_quiz
            st.session_state.quiz_submitted = False
            st.session_state.quiz_answers = {}
            st.rerun()

        else:
            st.error(
                "Не удалось создать тест. "
                "Попробуй ещё раз."
            )

    st.divider()

    quiz = st.session_state.quiz

    if quiz:
        st.markdown(f"### Тест: {quiz_subject}")
        st.write(f"Всего вопросов: {len(quiz)}")

        if not st.session_state.quiz_submitted:
            with st.form("ort_quiz_form"):
                for i, q in enumerate(quiz):
                    st.markdown(
                        f"**Вопрос {i + 1}.** {q['question']}"
                    )

                    st.radio(
                        "Выбери один ответ:",
                        options=range(4),
                        format_func=lambda x, opts=q["options"]: (
                            f"{chr(65 + x)}. {opts[x]}"
                        ),
                        key=f"quiz_answer_{i}",
                        index=None
                    )

                    st.divider()

                submitted = st.form_submit_button(
                    "✅ Проверить ответы",
                    use_container_width=True
                )

                if submitted:
                    answers = {}

                    for i in range(len(quiz)):
                        answers[i] = st.session_state.get(
                            f"quiz_answer_{i}"
                        )

                    st.session_state.quiz_answers = answers
                    st.session_state.quiz_submitted = True
                    st.rerun()

        else:
            answers = st.session_state.quiz_answers

            correct = 0

            for i, q in enumerate(quiz):
                selected = answers.get(i)
                right_answer = q["answer"]

                if selected == right_answer:
                    correct += 1

            total = len(quiz)
            percentage = round(correct / total * 100)

            st.success(
                f"🎉 Результат: {correct} из {total} "
                f"({percentage}%)"
            )

            st.progress(percentage / 100)

            if percentage >= 80:
                st.balloons()
                st.markdown("### 🌟 Отличный результат!")
            elif percentage >= 50:
                st.markdown("### 👍 Хорошо! Продолжай тренироваться.")
            else:
                st.markdown("### 💪 Не сдавайся! Разбери ошибки и попробуй снова.")

            st.divider()
            st.subheader("📖 Разбор ответов")

            for i, q in enumerate(quiz):
                selected = answers.get(i)
                right_answer = q["answer"]

                if selected == right_answer:
                    st.markdown(
                        f"**Вопрос {i + 1}: ✅ Правильно**"
                    )
                else:
                    st.markdown(
                        f"**Вопрос {i + 1}: ❌ Неправильно**"
                    )

                st.write(q["question"])

                st.write(
                    f"Правильный ответ: "
                    f"{chr(65 + right_answer)}. "
                    f"{q['options'][right_answer]}"
                )

                if selected is None:
                    st.write("Твой ответ: нет ответа")
                else:
                    st.write(
                        f"Твой ответ: "
                        f"{chr(65 + selected)}. "
                        f"{q['options'][selected]}"
                    )

                st.info(q.get("explanation", ""))
                st.divider()

            if st.button(
                "🔄 Пройти новый тест",
                use_container_width=True
            ):
                st.session_state.quiz = None
                st.session_state.quiz_submitted = False
                st.session_state.quiz_answers = {}
                st.rerun()

    else:
        st.info(
            "Нажми «Создать новый тест», "
            "чтобы начать подготовку к ОРТ."
        )

st.divider()

st.caption(
    "ОРТ AI · Твой помощник в подготовке к Общереспубликанскому тестированию"
)
