import streamlit as st
import requests
import json
import re

class YandexGPTClient:
    def __init__(self):
        self.api_key = st.secrets.get("YANDEX_GPT_API_KEY")
        self.folder_id = st.secrets.get("YANDEX_FOLDER_ID")
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        
    def generate_response(self, character, user_message):
        if not self.api_key or not self.folder_id:
            return self._get_fallback_response(character, user_message)
        
        try:
            # КРАТКИЕ промпты которые работают с YandexGPT
            prompts = {
                "alice": "Ты - Алиса, руководитель аналитики. Отвечай как наставник: объясняй концепции, но не давай готовый код. Поддерживающий тон, говори 'если что, заходи' когда отправляешь за информацией.",
                "maxim": "Ты - Максим, финансовый директор. Отвечай кратко и по делу. Не давай технические детали - отправляй к Алисе. Говори о сроках и бизнес-задачах.",
                "dba_team": "Ты - DBA команда. Отвечай только на SQL запросы в формате UPDATE/INSERT. Будь формальным и техническим.",
                "partner_a": "Ты - поддержка Партнера А. Отвечай формально и профессионально. Говори что проверишь и вернешься с ответом.",
                "partner_b": "Ты - поддержка Партнера Б. Отвечай формально и профессионально. Говори что проверишь и вернешься с ответом."
            }
            
            prompt = prompts.get(character, "")
            
            headers = {
                "Authorization": f"Api-Key {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "modelUri": f"gpt://{self.folder_id}/yandexgpt/latest",
                "completionOptions": {
                    "stream": False,
                    "temperature": 0.7,
                    "maxTokens": "500"
                },
                "messages": [
                    {
                        "role": "system", 
                        "text": prompt
                    },
                    {
                        "role": "user",
                        "text": user_message
                    }
                ]
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            generated_text = result['result']['alternatives'][0]['message']['text']
            
            # Фильтруем готовые SQL запросы для Алисы
            if character == "alice":
                generated_text = self._filter_sql_queries(generated_text)
            
            return generated_text
            
        except Exception as e:
            st.error(f"❌ Ошибка AI: {str(e)}")
            return self._get_fallback_response(character, user_message)
    
    def _filter_sql_queries(self, text):
        """Убираем готовые SQL запросы из ответов Алисы"""
        if re.search(r'(SELECT|INSERT|UPDATE|DELETE)\s+.+\s+(FROM|INTO|SET|WHERE)', text, re.IGNORECASE):
            return "Попробуй сам написать запрос. Если что-то не получается - покажи свой вариант, помогу разобраться."
        return text
    
    def _get_fallback_response(self, character, user_message):
        """Fallback на умные ответы если AI не работает"""
        fallback_responses = {
            "alice": "Давай разберемся с этим вопросом. Расскажи подробнее что именно нужно сделать?",
            "maxim": "Зайди к Алисе за деталями по данным и запросам.", 
            "dba_team": "Привет! Напиши запрос в формате UPDATE/INSERT таблица УСЛОВИЯ.",
            "partner_a": "Добрый день! Проверим ваш запрос и вернемся с ответом.",
            "partner_b": "Добрый день! Уточним информацию и предоставим ответ."
        }
        return fallback_responses.get(character, "Чем могу помочь?")

# Глобальный клиент
yandex_gpt_client = YandexGPTClient()
