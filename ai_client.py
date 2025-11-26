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
        
    def generate_response(self, character, user_message):
        # Всегда показываем индикатор для реализма
        time.sleep(2)  # Задержка для реализма
            
        # Пробуем YandexGPT
        ai_response = self._try_yandex_gpt(character, user_message)
        if ai_response and ai_response != self._get_fallback_response(character, user_message):
            return ai_response + " 🚀"  # Добавляем маркер AI ответа
        
        # Если AI не сработал - умный fallback
        return self._get_smart_fallback(character, user_message)
    
    def _try_yandex_gpt(self, character, user_message):
        """Пытаемся получить ответ от YandexGPT"""
        if not self.api_key or not self.folder_id:
            st.error("❌ API ключи не настроены в Secrets")
            return None
        
        try:
            # ПРОБУЕМ РАЗНЫЕ МОДЕЛИ
            models = [
                f"gpt://{self.folder_id}/yandexgpt-lite",
                f"gpt://{self.folder_id}/yandexgpt",
                f"gpt://{self.folder_id}/yandexgpt/latest"
            ]
            
            for model_uri in models:
                try:
                    response = self._make_api_request(model_uri, character, user_message)
                    if response:
                        st.success(f"✅ AI ответ получен (модель: {model_uri.split('/')[-1]})")
                        return self._filter_sql_queries(response, character)
                except Exception as e:
                    st.warning(f"⚠️ Модель {model_uri.split('/')[-1]} не сработала: {str(e)}")
                    continue
            
            st.error("❌ Все модели YandexGPT недоступны")
            return None
            
        except Exception as e:
            st.error(f"❌ Критическая ошибка YandexGPT: {str(e)}")
            return None
    
    def _make_api_request(self, model_uri, character, user_message):
        """Делаем API запрос"""
        prompts = {
            "alice": "Ты - Алиса, руководитель аналитики. Отвечай как наставник, объясняй концепции, но не давай готовый код. Поддерживающий тон. Отвечай на русском.",
            "maxim": "Ты - Максим, финансовый директор. Отвечай кратко и по делу. Бизнес-ориентированный. Отвечай на русском.",
            "dba_team": "Ты - DBA команда. Формальный и технический. Отвечай на русском.",
            "partner_a": "Ты - поддержка Партнера А. Формальный и профессиональный. Отвечай на русском.",
            "partner_b": "Ты - поддержка Партнера Б. Формальный и профессиональный. Отвечай на русском."
        }
        
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "modelUri": model_uri,
            "completionOptions": {
                "stream": False,
                "temperature": 0.7,
                "maxTokens": "300"
            },
            "messages": [
                {
                    "role": "system", 
                    "text": prompts.get(character, "")
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
        return result['result']['alternatives'][0]['message']['text']
    
    def _get_smart_fallback(self, character, user_message):
        """УМНЫЕ fallback ответы с контекстом"""
        message_lower = user_message.lower()
        
        if character == "alice":
            if any(word in message_lower for word in ["привет", "здравств", "начать"]):
                return "Привет! Рада тебя видеть. Расскажи что нужно сделать - помогу разобраться с данными, бизнес-логикой или процессами работы. 🤗"
            
            elif "прибыль" in message_lower:
                return "Прибыль рассчитывается как сумма успешных операций за вычетом комиссий. Используй processing_operations с status='success', посчитай сумму amount и вычти commission_amount. Если нужны детали - заходи! 💰"
            
            elif any(word in message_lower for word in ["дай запрос", "напиши sql", "готовый"]):
                return "Лучше попробуй сам написать запрос, а я помогу его улучшить. Например, начни с SELECT * FROM processing_operations WHERE status='success'. Покажи что получилось! 💻"
            
            elif any(word in message_lower for word in ["связать", "join", "таблиц"]):
                return "Таблицы связываются через operation_additional_data. processing_operations → operation_additional_data → partner_a_payments. Ключевое поле - partner_operation_id. Проверь схему базы данных для точных названий полей. 🔗"
            
            elif any(word in message_lower for word in ["статус", "расхожден"]):
                return "При расхождениях статусов данные партнера всегда приоритетны. У нас success/failed, у PARTNER_A - COMPLETED/DECLINED. Если статусы разные - нужно исправить наши данные через DBA. ⚠️"
            
            else:
                return "Интересный вопрос! Давай разберемся подробнее. Что именно ты пытаешься сделать и что уже пробовал? 🤔"
        
        elif character == "maxim":
            if "прибыль" in message_lower:
                return "Нужна общая прибыль за вчера по успешным операциям. ASAP к 11:00 для встречи с инвесторами. За деталями по данным - к Алисе. 📊"
            else:
                return "Зайди к Алисе за техническими деталями. Мне нужны готовые цифры для отчетности. 🎯"
        
        return "Чем могу помочь? 💬"
    
    def _filter_sql_queries(self, text, character):
        """Фильтруем SQL только для Алисы"""
        if character == "alice":
            if re.search(r'(SELECT|INSERT|UPDATE|DELETE)\s+.+\s+(FROM|INTO|SET|WHERE)', text, re.IGNORECASE):
                return "Вижу что ты просишь готовый запрос! Попробуй сам написать, а я помогу его улучшить. Это лучший способ научиться. Покажи свой вариант! 💪"
        return text
    
    def _get_fallback_response(self, character, user_message):
        """Простой fallback"""
        return "Давай разберемся с этим вопросом. Расскажи подробнее что именно нужно сделать?"

# Глобальный клиент
yandex_gpt_client = YandexGPTClient()
