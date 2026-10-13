from google import genai
from google.genai import types
import json
import re
import time
import streamlit as st
from supabase import create_client
st.set_page_config(page_title="ОРТ AI", page_icon="🎓", layout="centered")

SYSTEM_PROMPT = """
Ты — ОРТ AI, опытный и поддерживающий ИИ-репетитор для подготовки к Общереспубликанскому тестированию (ОРТ) в Кыргызстане.

ТВОЙ СТИЛЬ И ПРАВИЛА:
1. Давай развёрнутые, структурированные и подробные объяснения.
2. Объясняй темы и задачи пошагово: сначала суть, затем пример или ход решения, в конце — вывод или совет.
3. Математику и логику разбирай максимально детально с формулами и вычислениями.
4. Отвечай дружелюбно, как настоящий квалифицированный учитель.
5. Если приложено фото задания, прочитай его полностью, приведи условие и разбери решение по шагам.
6. Отвечай на языке пользователя (русский/кыргызский).
"""

# Актуальная и быстрая модель
MODEL = "gemini-3.6-flash"

SUBJECTS = ["Общий вопрос", "Математика", "Логика", "Аналогии", "Чтение"]

LANGUAGES = ["Русский", "Кыргызский", "Казахский"]

# Состояние приложения
if "messages" not in st.session_state:
  st.session_state.messages = []

if "quiz" not in st.session_state:
  st.session_state.quiz = None

if "quiz_answers" not in st.session_state:
  st.session_state.quiz_answers = {}

if "quiz_submitted" not in st.session_state:
  st.session_state.quiz_submitted = False


@st.cache_resource
def get_client():
  return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


def ask_ai(prompt, image_bytes=None, mime_type="image/jpeg"):
  """Получение полноценного и развёрнутого ответа от Gemini."""
  try:
    client = get_client()

    contents = [prompt]

    if image_bytes:
      contents.append(
          types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
      )

    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.4,
            max_output_tokens=2048,  # Достаточно места для подробных объяснений
        ),
    )

    return response.text or "ИИ не вернул текст. Попробуй ещё раз."

  except Exception as e:
    return f"⚠️ ТЕХНИЧЕСКАЯ ОШИБКА: {repr(e)}"


def create_quiz(subject, count, difficulty, language):
  """Создание тренировочного теста."""
  prompt = f"""
Создай тренировочный тест для подготовки к ОРТ в Кыргызстане.

Предмет: {subject}
Количество вопросов: {count}
Сложность: {difficulty}
Язык: {language}

Требования:
- Ровно {count} вопросов.
- У каждого вопроса ровно четыре варианта ответа.
- Только один правильный ответ.
- Вопросы должны быть грамотными и корректными.
- Для каждого вопроса добавь короткое объяснение.
- Не добавляй текст вне JSON.

Формат:
{{
  "questions": [
    {{
      "question": "Текст вопроса",
      "options": ["Вариант A", "Вариант B", "Вариант C", "Вариант D"],
      "answer": 0,
      "explanation": "Короткое объяснение"
    }}
  ]
}}

answer — индекс правильного варианта, начиная с нуля.
"""
  result = ask_ai(prompt)

  if not result:
    return None

  try:
    result = result.strip()
    result = re.sub(r"^```(?:json)?\s*", "", result)
    result = re.sub(r"\s*```$", "", result)

    data = json.loads(result)
    questions = data.get("questions", [])

    valid = []

    for q in questions:
      if not isinstance(q, dict):
        continue

      options = q.get("options")
      answer = q.get("answer")

      if (
          isinstance(q.get("question"), str)
          and isinstance(options, list)
          and len(options) == 4
          and isinstance(answer, int)
          and not isinstance(answer, bool)
          and 0 <= answer < 4
      ):
        valid.append(q)

    return valid or None

  except Exception as e:
    print("Quiz parsing error:", repr(e))
    return None


# Заголовок
st.title("🎓 ОРТ AI")
st.caption("Твой ИИ-помощник для подготовки к ОРТ")

with st.sidebar:
  st.header("⚙️ Настройки")

  subject = st.selectbox("Предмет", SUBJECTS, key="main_subject")

  language = st.selectbox("Язык ответа", LANGUAGES, key="main_language")

  st.divider()
  st.write("⚡ Быстрые ответы")
  st.write("📸 Решение заданий по фото")
  st.write("📝 Тренировочные тесты")

  if st.button("🗑️ Очистить историю чата"):
    st.session_state.messages = []
    st.rerun()


chat_tab, quiz_tab = st.tabs(["💬 ИИ-репетитор", "📝 Тесты ОРТ"])


# =========================================
# ЧАТ И РЕШЕНИЕ ЗАДАНИЙ ПО ФОТО
# =========================================

with chat_tab:
  st.subheader("Задай вопрос или отправь фото")

  with st.expander("📸 Сфотографировать или загрузить задание"):
    camera = st.camera_input("Сфотографируй задание")

    upload = st.file_uploader(
        "Или выбери изображение", type=["jpg", "jpeg", "png", "webp"]
    )

  photo = None
  mime_type = "image/jpeg"

  if camera is not None:
    photo = camera.getvalue()
  elif upload is not None:
    photo = upload.getvalue()
    mime_type = upload.type or "image/jpeg"

  for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
      st.markdown(msg["content"])

  question = st.chat_input("Напиши вопрос...")

  col1, col2, col3 = st.columns(3)

  if col1.button("➗ Дроби"):
    question = "Объясни дроби на простом примере."

  if col2.button("📊 Проценты"):
    question = "Объясни, как решать задачи на проценты."

  if col3.button("🧠 Логика"):
    question = "Дай одно задание на логику уровня ОРТ и объясни решение."

  if question:
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
      st.markdown(question)

      if photo:
        st.image(photo, caption="Фото задания", use_container_width=True)

    prompt = f"""
Предмет: {subject}
Язык ответа: {language}
Вопрос ученика: {question}

Дай подробное, развернутое объяснение.
Если есть задача, покажи правильное решение по шагам.
Если приложено изображение, разбери задание с него.
"""

    with st.chat_message("assistant"):
      with st.spinner("Думаю..."):
        answer = ask_ai(prompt, image_bytes=photo, mime_type=mime_type)

      if answer:
        st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})
      else:
        st.error(
            "Не удалось получить ответ. Проверь подключение к Gemini API и Logs."
        )


# =========================================
# ТЕСТЫ ОРТ
# =========================================

with quiz_tab:
  st.subheader("📝 Тренировочный тест")

  quiz_subject = st.selectbox("Выбери предмет теста", SUBJECTS[1:], key="quiz_subject")

  count = st.selectbox("Количество вопросов", [5, 10, 15], key="quiz_count")

  difficulty = st.selectbox(
      "Сложность", ["Лёгкая", "Средняя", "Сложная"], key="quiz_difficulty"
  )

  if st.button("🚀 Создать тест", type="primary", use_container_width=True):
    with st.spinner("Готовлю вопросы..."):
      quiz = create_quiz(quiz_subject, count, difficulty, language)

    if quiz:
      st.session_state.quiz = quiz
      st.session_state.quiz_answers = {}
      st.session_state.quiz_submitted = False
      st.rerun()
    else:
      st.error("Не получилось создать тест. Попробуй ещё раз.")

  quiz = st.session_state.quiz

  if quiz:
    st.divider()
    st.markdown(f"### Тест: {quiz_subject}")

    if not st.session_state.quiz_submitted:
      with st.form("ort_test_form"):
        for i, q in enumerate(quiz):
          st.markdown(f"**Вопрос {i + 1}.** {q['question']}")

          st.radio(
              "Выбери ответ",
              options=[0, 1, 2, 3],
              format_func=lambda x, opts=q["options"]: (
                  f"{chr(65 + x)}. {opts[x]}"
              ),
              index=None,
              key=f"answer_{i}",
          )

          st.divider()

        submitted = st.form_submit_button(
            "✅ Проверить ответы", use_container_width=True
        )

      if submitted:
        st.session_state.quiz_answers = {
            i: st.session_state.get(f"answer_{i}") for i in range(len(quiz))
        }

        st.session_state.quiz_submitted = True
        st.rerun()

    else:
      answers = st.session_state.quiz_answers
      correct = sum(
          1 for i, q in enumerate(quiz) if answers.get(i) == q["answer"]
      )

      total = len(quiz)
      percent = round(correct / total * 100)

      st.success(f"Результат: {correct} из {total} — {percent}%")
      st.progress(percent / 100)

      if percent >= 80:
        st.balloons()
        st.write("🌟 Отличный результат!")
      elif percent >= 50:
        st.write("👍 Хорошая работа! Продолжай тренироваться.")
      else:
        st.write("💪 Разбери ошибки и попробуй снова.")

      st.subheader("Разбор ответов")

      for i, q in enumerate(quiz):
        selected = answers.get(i)
        right = q["answer"]

        if selected == right:
          st.markdown(f"**Вопрос {i + 1}: ✅ Верно**")
        else:
          st.markdown(f"**Вопрос {i + 1}: ❌ Ошибка**")

        st.write(q["question"])
        st.write(f"Правильный ответ: {chr(65 + right)}. {q['options'][right]}")

        if selected is not None:
          st.write(
              f"Твой ответ: {chr(65 + selected)}. {q['options'][selected]}"
          )
        else:
          st.write("Ты пропустил этот вопрос.")

        st.info(q.get("explanation", ""))
        st.divider()

      if st.button("🔄 Создать новый тест"):
        st.session_state.quiz = None
        st.session_state.quiz_answers = {}
        st.session_state.quiz_submitted = False
        st.rerun()

  else:
    st.info("Выбери предмет и нажми «Создать тест».")


st.divider()
st.caption("ОРТ AI · Учись эффективнее каждый день")
