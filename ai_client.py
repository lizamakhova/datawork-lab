import time
import random
import re
import html

class OpenAIClient:
    def __init__(self):
        # Lazy import — только при создании экземпляра
        try:
            import streamlit as st
            self.api_key = st.secrets.get("OPENAI_API_KEY")
            if self.api_key:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
            else:
                self.client = None
        except Exception:
            self.client = None

    def _sanitize_input(self, text: str) -> str:
        """Базовая защита от инъекций на входе"""
        dangerous_patterns = [
            r'\b(UPDATE|INSERT|DELETE|DROP|ALTER|CREATE|TRUNCATE|EXEC)\b',
            r';\s*(--|#|/\*)',
            r"'(\s*OR\s+1=1|--)",
            r'(\.\.|/proc/self/environ)',
            r'<script.*?>.*?</script>',
        ]
        text = text.strip()
        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                raise ValueError("dangerous content")
        return text

    def generate_response(self, character, user_message, chat_history=[]):
        # 🔒 Санитизация входа
        try:
            user_message = self._sanitize_input(user_message)
        except ValueError:
            return "❌ Запрос содержит потенциально опасные команды. Пожалуйста, переформулируйте."

        # Задержка (реалистичное время реакции)
        delay = self._get_character_delay(character)
        time.sleep(delay)

        # Попытка OpenAI
        ai_response = self._try_openai(character, user_message, chat_history)
        if ai_response:
            return ai_response

        # Fallback
        return self._get_smart_fallback(character, user_message)

    def _try_openai(self, character, user_message, chat_history):
        if not self.client:
            return None

        try:
            # Lazy import — только при вызове
            import streamlit as st

            messages = [
                {"role": "system", "content": self._get_detailed_prompt(character)}
            ]

            # История (последние 6 сообщений)
            for msg in chat_history[-6:]:
                role = "user" if msg["role"] == "user" else "assistant"
                messages.append({"role": role, "content": msg["content"]})

            messages.append({"role": "user", "content": user_message})

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.3,
                max_tokens=500,
                timeout=10  # Защита от зависаний
            )

            result = response.choices[0].message.content
            result = self._filter_sql_queries(result, character)
            return html.escape(result, quote=False)

        except Exception as e:
            try:
                import streamlit as st
                st.error(f"❌ Ошибка OpenAI: {str(e)[:100]}")
            except:
                pass
            return None

    def _get_detailed_prompt(self, character):
        prompts = {
            "alice": """
Ты - Алиса, 28 лет, руководитель аналитики. Помогаешь сотруднику разобраться, но не даёшь готовые ответы.
— Задавай 1–2 наводящих вопроса
— Не обсуждай личные, политические, религиозные темы
— При некорректном поведении: сначала вежливо, потом формально, потом игнор
— Технический контекст: выручка = amount - commission_amount; статусы партнёров приоритетны.
Говори как наставник. Без эмодзи.
""",
            "maxim": """
Ты - Максим, финансовый директор. Формальный, занятой, фокус на результатах.
— «ASAP», «пож100», «к 11:00»
— Технические детали — к Алисе
— Игнорируй личные вопросы и эмоции
— При хамстве — игнор или «Зайди к Алисе»
Без эмодзи.
""",
            "kirill": """
Ты - Кирилл, продакт-менеджер. Горит, но не знает деталей.
— «Горит!», «критично для отчёта»
— Технические вопросы — к Алисе
— При личных вопросах — «точно мне?»
— При хамстве — «Мы так в команде не общаемся»
Без эмодзи.
""",
            "dba_team": """
Ты - Михаил Шилин, DBA.
— Только выполняем готовые запросы формата: UPDATE таблица SET ... WHERE ...
— Не помогаем писать, не консультируем по бизнес-логике
— «Формат описан в базе знаний»
— «Это не к нам»
Кратко. Без эмодзи.
""",
            "partner_a": """
Ты - Анна Новикова, поддержка Партнёра А.
— Статусы: COMPLETED, DECLINED, IN_PROGRESS
— Только по своим реестрам
— Формально, вежливо
Без эмодзи.
""",
            "partner_b": """
Ты - Дмитрий Семенов, поддержка Партнёра Б.
— Статусы: SUCCESS, FAILED
— Только по своим реестрам
— Формально, вежливо
Без эмодзи.
"""
        }
        return prompts.get(character, "Отвечай профессионально. Без эмодзи.")

    def _get_smart_fallback(self, character, user_message):
        fallbacks = {
            "alice": [
                "Давай разберёмся. Что именно нужно сделать?",
                "Что уже пробовал? С чего начнём?",
                "Помогу разобраться — расскажи подробнее."
            ],
            "maxim": [
                "Нужны цифры к 11:00. За деталями — к Алисе.",
                "ASAP! Если не успеваешь — скажи заранее."
            ],
            "kirill": [
                "Горит! Нужны данные как можно скорее.",
                "Критично для отчёта. Что уже есть?"
            ],
            "dba_team": [
                "Формат запросов описан в базе знаний.",
                "Это не к нам — обратись к руководителю."
            ],
            "partner_a": [
                "Наши статусы: COMPLETED, DECLINED, IN_PROGRESS.",
                "Готовы помочь по реестрам."
            ],
            "partner_b": [
                "Наши статусы: SUCCESS, FAILED.",
                "Готовы помочь по операциям."
            ]
        }
        resp = random.choice(fallbacks.get(character, ["Давай обсудим."]))
        return html.escape(resp, quote=False)

    def _filter_sql_queries(self, text, character):
        if character == "alice":
            if re.search(r'(SELECT|UPDATE|INSERT|DELETE)\s+.*\s+(FROM|INTO|SET|WHERE)', text, re.IGNORECASE):
                return "Попробуй написать запрос сам — я помогу улучшить!"
        return text

    def _get_character_delay(self, character):
        delays = {
            "alice": random.randint(6, 12),
            "maxim": 25,
            "kirill": 10,
            "dba_team": 15,
            "partner_a": 18,
            "partner_b": 22
        }
        return delays.get(character, 8)
