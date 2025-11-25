import os
import streamlit as st

class AIClient:
    def __init__(self, api_token=None):
        self.api_token = api_token or os.getenv('HUGGINGFACE_TOKEN')
        self.model = "sberbank-ai/rugpt3large_based_on_gpt2"
        
        if not self.api_token:
            st.warning("⚠️ Hugging Face токен не настроен. Используются статические ответы.")
    
    def generate_response(self, prompt, user_message, max_length=300):
        """Генерация ответа через AI (заглушка - будет заменена на реальную интеграцию)"""
        # Временная заглушка - возвращаем статический ответ
        # В реальной реализации здесь будет вызов Hugging Face API
        
        # Имитация AI ответа на основе промпта
        if "Алиса" in prompt:
            return self._get_alice_response(user_message)
        elif "Максим" in prompt:
            return self._get_maxim_response(user_message)
        elif "DBA" in prompt:
            return self._get_dba_response(user_message)
        else:
            return self._get_partner_response(user_message)
    
    def _get_alice_response(self, user_message):
        """Имитация AI ответов Алисы"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ["sql", "запрос", "таблиц", "данн"]):
            return "Для работы с данными тебе понадобятся несколько таблиц. Основная - processing_operations содержит наши операции. Для связи с партнерами используй partner_a_payments и partner_b_payments через partner_operation_id из operation_additional_data. Не забудь проверить реестры в registry_statuses - там есть поле is_excluded которое должно быть 0 для активных реестров."
        
        elif any(word in message_lower for word in ["расхожден", "статус"]):
            return "При расхождениях статусов важно помнить: данные партнера всегда приоритетны. Например, операция PA023 - у нас статус success, а у партнера DECLINED. Нужно исправить наш статус на failed. Для этого используй запрос к DBA: UPDATE processing_operations SET status='failed' WHERE processing_id='PA023'"
        
        elif any(word in message_lower for word in ["комисс", "commission"]):
            return "Комиссии проверяются через сравнение commission_amount в processing_operations с расчетом по таблице commission_rates. Формула: amount * commission_percent + fixed_commission. Например, для PA037 расчет дает 4.30, а в реестре 3.20 - это расхождение нужно запросить у партнера."
        
        elif any(word in message_lower for word in ["реестр", "дубл"]):
            return "У PARTNER_B два активных реестра на одну дату - REG_B_001 и REG_B_002. Нужно уточнить у партнера какой корректен. В чате #partner_b_operations_chat запроси подтверждение и исключение некорректного реестра."
        
        else:
            return "Привет! Расскажи подробнее что тебя интересует - помогу разобраться с структурой данных, бизнес-логикой или процессами работы с партнерами."

    def _get_maxim_response(self, user_message):
        """Имитация AI ответов Максима"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ["операц", "успешн", "прибыл"]):
            return "Нужны успешные операции за вчера с общей суммой и комиссиями. ASAP к 11:00 для встречи с инвесторами."
        
        elif any(word in message_lower for word in ["срок", "когда"]):
            return "К 11:00 сегодня. Это критично для принятия решений по квартальной отчетности."
        
        elif any(word in message_lower for word in ["детал", "как"]):
            return "Технические детали уточни у Алисы - она поможет с запросами и данными."
        
        else:
            return "Зайди к Алисе за деталями по данным и запросам."

    def _get_dba_response(self, user_message):
        """Имитация AI ответов DBA команды"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ["update", "insert"]) and "where" in message_lower:
            return "Привет! Запрос выполнен. Проверь результаты. Не забудь про бэкапы данных при изменении системных таблиц."
        
        elif any(word in message_lower for word in ["исправ", "прав"]):
            return "Привет! Напиши запрос в корректном формате: UPDATE таблица SET поле=значение WHERE условие. Мы выполняем только скрипты с явными условиями."
        
        else:
            return "Привет! Мы выполняем запросы в формате: UPDATE|INSERT таблица УСЛОВИЯ. Убедись что в запросе есть WHERE условие для UPDATE."

    def _get_partner_response(self, user_message):
        """Имитация AI ответов партнеров"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ["комисс", "расхожден"]):
            return "Добрый день! Получили ваш запрос по расхождениям в комиссиях. Проверим расчеты и предоставим ответ в течение 2 рабочих дней."
        
        elif any(word in message_lower for word in ["реестр", "дубл"]):
            return "Добрый день! По вашему запросу о дублирующих реестрах: проверим и уточним у операционного отдела. Вернемся с ответом завтра."
        
        else:
            return "Добрый день! Чем можем помочь? Опишите подробнее ваш вопрос для более точного ответа."

# Глобальный клиент
ai_client = AIClient()
