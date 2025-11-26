import os
import streamlit as st
import requests
import json

class YandexGPTClient:
    def __init__(self):
        self.api_key = st.secrets.get("YANDEX_GPT_API_KEY")
        self.folder_id = st.secrets.get("YANDEX_FOLDER_ID")
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        
        if not self.api_key:
            st.error("❌ YandexGPT API ключ не настроен в Secrets")
        if not self.folder_id:
            st.error("❌ Yandex Folder ID не настроен в Secrets")
    
    def generate_response(self, prompt, user_message, max_length=300):
        if not self.api_key or not self.folder_id:
            return self._get_static_response(prompt, user_message)
        
        try:
            full_prompt = f"{prompt}\n\nПользователь: {user_message}\nАссистент:"
            
            headers = {
                "Authorization": f"Api-Key {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
                "completionOptions": {
                    "stream": False,
                    "temperature": 0.3,
                    "maxTokens": str(max_length)
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
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            generated_text = result['result']['alternatives'][0]['message']['text']
            
            return self._filter_ready_solutions(generated_text)
            
        except Exception as e:
            st.error(f"❌ Ошибка YandexGPT: {str(e)}")
            return self._get_static_response(prompt, user_message)
    
    def _filter_ready_solutions(self, response):
        forbidden_patterns = [
            r"SELECT\s+.+\s+FROM", 
            r"INSERT\s+INTO",
            r"UPDATE\s+\w+\s+SET",
            r"Вот\s+запрос:",
            r"Скопируй\s+этот\s+код"
        ]
        
        for pattern in forbidden_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                return "Попробуй сам написать запрос. Если что-то не получается - покажи свой вариант, помогу разобраться."
        
        return response
    
    def _get_static_response(self, prompt, user_message):
        if "Алиса" in prompt:
            return self._get_alice_response(user_message)
        elif "Максим" in prompt:
            return self._get_maxim_response(user_message)
        elif "DBA" in prompt:
            return self._get_dba_response(user_message)
        else:
            return self._get_partner_response(user_message)
    
    def _get_alice_response(self, user_message):
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ["sql", "запрос", "таблиц", "данн"]):
            return "Для работы с данными тебе понадобятся несколько таблиц. Основная - processing_operations содержит наши операции. Для связи с партнерами используй partner_a_payments и partner_b_payments через partner_operation_id из operation_additional_data."
        
        elif any(word in message_lower for word in ["расхожден", "статус"]):
            return "При расхождениях статусов важно помнить: данные партнера всегда приоритетны. Например, операция PA023 - у нас статус success, а у партнера DECLINED. Нужно исправить наш статус на failed."
        
        else:
            return "Привет! Расскажи подробнее что тебя интересует - помогу разобраться с структурой данных или процессами работы."

# Глобальный клиент
yandex_gpt_client = YandexGPTClient()
