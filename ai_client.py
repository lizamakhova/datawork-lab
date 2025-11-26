import streamlit as st
import requests
import json
import re
import time

class YandexGPTClient:
    def __init__(self):
        self.api_key = st.secrets.get("YANDEX_GPT_API_KEY")
        self.folder_id = st.secrets.get("YANDEX_FOLDER_ID")
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        
        # Диагностика
        if not self.api_key:
            st.error("❌ YANDEX_GPT_API_KEY не найден в Secrets")
        else:
            st.success(f"✅ API ключ найден: {self.api_key[:10]}...")
            
        if not self.folder_id:
            st.error("❌ YANDEX_FOLDER_ID не найден в Secrets")
        else:
            st.success(f"✅ Folder ID найден: {self.folder_id}")
    
    def generate_response(self, character, user_message):
        if not self.api_key or not self.folder_id:
            st.error("❌ Не могу подключиться к YandexGPT - проверьте Secrets")
            return self._get_fallback_response(character, user_message)
        
        # Показываем индикатор "печатает..."
        with st.spinner(f"🤔 {self._get_typing_message(character)}"):
            # Имитируем задержку 2-5 секунд
            time.sleep(2)
            
            try:
                # КРАТКИЕ промпты которые работают с YandexGPT
                prompts = {
                    "alice": "Ты - Алиса, руководитель аналитики. Отвечай как наставник: объясняй концепции, но не давай готовый код. Поддерживающий тон, говори 'если что, заходи' когда отправляешь за информацией. Отвечай на русском.",
                    "maxim": "Ты - Максим, финансовый директор. Отвечай кратко и по делу. Не давай технические детали - отправляй к Алисе. Говори о сроках и бизнес-задачах. Отвечай на русском.",
                    "dba_team": "Ты - DBA команда. Отвечай только на SQL запросы в формате UPDATE/INSERT. Будь формальным и техническим. Отвечай на русском.",
                    "partner_a": "Ты - поддержка Партнера А. Отвечай формально и профессионально. Говори что проверишь и вернешься с ответом. Отвечай на русском.",
                    "partner_b": "Ты - поддержка Партнера Б. Отвечай формально и профессионально. Говори что проверишь и вернешься с ответом. Отвечай на русском."
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
                        "maxTokens": "300"
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
                
                st.info("🔄 Отправляю запрос к YandexGPT...")
                response = requests.post(self.api_url, headers=headers, json=payload, timeout=15)
                
                if response.status_code != 200:
                    st.error(f"❌ Ошибка API: {response.status_code} - {response.text}")
                    return self._get_fallback_response(character, user_message)
                
                response.raise_for_status()
                
                result = response.json()
                generated_text = result['result']['alternatives'][0]['message']['text']
                
                st.success("✅ Получен ответ от AI!")
                
                # Фильтруем готовые SQL запросы для Алисы
                if character == "alice":
                    generated_text = self._filter_sql_queries(generated_text)
                
                return generated_text
                
            except requests.exceptions.Timeout:
                st.error("❌ Таймаут подключения к YandexGPT")
                return self._get_fallback_response(character, user_message)
            except Exception as e:
                st.error(f"❌ Ошибка YandexGPT: {str(e)}")
                return self._get_fallback_response(character, user_message)
    
    def _get_typing_message(self, character):
        messages = {
            "alice": "Алиса думает...",
            "maxim": "Максим печатает...", 
            "dba_team": "DBA команда проверяет запрос...",
            "partner_a": "Партнер А проверяет информацию...",
            "partner_b": "Партнер Б уточняет детали..."
        }
        return messages.get(character, "Печатает...")
    
    def _filter_sql_queries(self, text):
        """Убираем готовые SQL запросы из ответов Алисы"""
        if re.search(r'(SELECT|INSERT|UPDATE|DELETE)\s+.+\s+(FROM|INTO|SET|WHERE)', text, re.IGNORECASE):
            return "Попробуй сам написать запрос. Если что-то не получается - покажи свой вариант, помогу разобраться."
        return text
    
    def _get_fallback_response(self, character, user_message):
        """Умные fallback ответы"""
        message_lower = user_message.lower()
        
        if character == "alice":
            if "прибыль" in message_lower:
                return "Прибыль можно посчитать как сумму успешных операций за вычетом комиссий. Используй таблицу processing_operations с status='success'. Если что, заходи - помогу разобраться с деталями!"
            elif any(word in message_lower for word in ["sql", "запрос"]):
                return "Для работы с данными используй основные таблицы: processing_operations, partner_a_payments, partner_b_payments. Связывай их через operation_additional_data."
            else:
                return "Давай разберемся с этим вопросом. Расскажи подробнее что именно нужно сделать?"
        
        return "Чем могу помочь?"

# Глобальный клиент
yandex_gpt_client = YandexGPTClient()
