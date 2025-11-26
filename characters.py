from ai_client import yandex_gpt_client

CHARACTERS_PROFILES = {
    "alice": {
        "full_name": "Алиса Петрова",
        "photo": "👩‍💼",
        "status": "🟢 Онлайн",
        "role": "Руководитель аналитики",
        "department": "Отдел аналитики", 
        "work_hours": "9:00-18:00 МСК"
    },
    "maxim": {
        "full_name": "Максим Волков",
        "photo": "👨‍💼",
        "status": "🟡 Не беспокоить",
        "role": "Финансовый директор", 
        "department": "Финансовый отдел",
        "work_hours": "Не указано"
    }
}

def get_ai_response(character_key, user_message):
    try:
        # Прямой вызов YandexGPT
        response = yandex_gpt_client.generate_response(character_key, user_message)
        return response
    except Exception as e:
        return get_static_response(character_key, user_message)

def get_static_response(character_key, user_message):
    message_lower = user_message.lower()
    
    if character_key == "alice":
        if any(word in message_lower for word in ["sql", "запрос", "таблиц", "данн"]):
            return "Нужно сравнить наши данные и данные из реестра партнеров. Проверить, что нет дубликатов в реестрах."
        elif any(word in message_lower for word in ["кирилл", "приоритет", "срочн"]):
            return "Пусть зайдет ко мне за приоритизацией, мы обсудим. Доделай плиз задачу от Максима, она asap"
        else:
            return "Привет! Расскажи подробнее что нужно - помогу разобраться с данными и процессами"
    
    elif character_key == "maxim":
        if any(word in message_lower for word in ["операц", "успешн", "прибыл", "анализ"]):
            return "за вчера общая сумма. Зайди к Алисе за деталями"
        elif any(word in message_lower for word in ["срок", "когда", "врем"]):
            return "Нужно к 11:00 к встрече. ASAP!"
        else:
            return "Зайди к Алисе за деталями"
    
    elif character_key == "dba_team":
        if any(word in message_lower for word in ["исправ", "прав", "update", "insert"]):
            if any(word in message_lower for word in ["update", "insert"]) and "where" in message_lower:
                return "Привет! Готово, проверяй"
            else:
                return "Привет! Пришли ответ в корректном формате, пожалуйста. Мы выполняем только скрипты"
        else:
            return "Привет! Мы выполняем запросы в формате: UPDATE|INSERT таблица УСЛОВИЯ"
    
    else:
        if any(word in message_lower for word in ["комисс", "расхожден", "реестр", "провер"]):
            return "Добрый день! Проверим и вернемся"
        elif any(word in message_lower for word in ["дубл", "два реестр"]):
            return "Добрый день! Уточним и предоставим ответ"
        else:
            return "Добрый день! Чем можем помочь?"

CHARACTERS_RESPONSES = {
    "alice": {
        "name": "Алиса Петрова",
        "get_response": lambda message: get_ai_response("alice", message)
    },
    "maxim": {
        "name": "Максим Волков", 
        "get_response": lambda message: get_ai_response("maxim", message)
    }
}

GROUP_CHATS = {
    "dba_team": {
        "name": "#dba-team",
        "icon": "🛠️",
        "description": "Команда баз данных - выполняем SQL запросы",
        "members": "3 участника",
        "get_response": lambda message: get_ai_response("dba_team", message)
    },
    "partner_a": {
        "name": "#partner_a_operations_chat",
        "icon": "🤝",
        "description": "Операции с Партнером А - вопросы по реестрам и комиссиям", 
        "members": "Поддержка Партнер А + наша команда",
        "get_response": lambda message: get_ai_response("partner_a", message)
    },
    "partner_b": {
        "name": "#partner_b_operations_chat", 
        "icon": "🤝",
        "description": "Операции с Партнером Б - согласование реестров и статусов",
        "members": "Поддержка Партнер Б + наша команда",
        "get_response": lambda message: get_ai_response("partner_b", message)
    }
}
