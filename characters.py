# Статические ответы персонажей по твоим промптам
CHARACTERS_RESPONSES = {
    "alice": {
        "name": "Алиса",
        "role": "Руководитель аналитики",
        "get_response": lambda message: get_alice_response(message.lower())
    },
    "maxim": {
        "name": "Максим", 
        "role": "Финансовый директор",
        "get_response": lambda message: get_maxim_response(message.lower())
    },
    "dba": {
        "name": "DBA команда",
        "role": "Команда баз данных", 
        "get_response": lambda message: get_dba_response(message.lower())
    },
    "partner_a": {
        "name": "Поддержка Партнер А",
        "role": "Внешний партнер",
        "get_response": lambda message: get_partner_response(message.lower())
    },
    "partner_b": {
        "name": "Поддержка Партнер Б", 
        "role": "Внешний партнер",
        "get_response": lambda message: get_partner_response(message.lower())
    }
}

def get_alice_response(message):
    """Ответы Алисы"""
    if any(word in message for word in ["sql", "запрос", "таблиц", "данн", "статус"]):
        return "Нужно сравнить наши данные и данные из реестра партнеров. Проверить, что нет дубликатов в реестрах. И подсвечу, что не во всех реестрах есть наши id, нужны будут id партнера из таблиц с доп данными"
    
    elif any(word in message for word in ["кирилл", "приоритет", "срочн", "задач"]):
        return "Пусть зайдет ко мне за приоритизацией, мы обсудим. Заходил Кирилл, его вопрос пока отложи, не горит. Доделай плиз задачу от Максима, она asap"
    
    elif any(word in message for word in ["реестр", "дубл", "reg_b"]):
        return "Зайди к партнеру, уточни плиз, почему нам прислали два"
    
    elif any(word in message for word in ["расхожден", "статус", "па023", "declined"]):
        return "Данные партнера всегда приоритетны, наш статус надо привести в соответствие их статусу. Если где-то сомневаемся - лучше уточнить у партнера"
    
    elif any(word in message for word in ["комисс", "commission", "расчет"]):
        return "Подсвечу на всякий случай, что важно сначала свериться с реестрами партнеров. Данные из реестров лежат в табличках partner_payments. Там, где нет наших id нужно использовать id партнера из additional данных. Комиссии тоже нужно проверить, что они в реестрах корректные"
    
    else:
        return "Привет! Расскажи подробнее что нужно - помогу разобраться с данными и процессами"

def get_maxim_response(message):
    """Ответы Максима"""
    if any(word in message for word in ["операц", "успешн", "прибыл", "анализ"]):
        return "за вчера общая сумма. Зайди к Алисе за деталями"
    
    elif any(word in message for word in ["срок", "когда", "врем"]):
        return "Нужно к 11:00 к встрече. ASAP!"
    
    else:
        return "Зайди к Алисе за деталями"

def get_dba_response(message):
    """Ответы DBA команды"""
    if any(word in message for word in ["исправ", "прав", "update", "insert"]):
        if any(word in message for word in ["update", "insert"]) and "where" in message:
            return "Привет! Готово, проверяй"
        else:
            return "Привет! Пришли ответ в корректном формате, пожалуйста. Мы выполняем только скрипты"
    
    else:
        return "Привет! Мы выполняем запросы в формате: UPDATE|INSERT таблица УСЛОВИЯ"

def get_partner_response(message):
    """Ответы партнеров"""
    if any(word in message for word in ["комисс", "расхожден", "реестр", "провер"]):
        return "Добрый день! Проверим и вернемся"
    
    elif any(word in message for word in ["дубл", "два реестр", "reg_b_001"]):
        return "Добрый день! Уточним и предоставим ответ"
    
    else:
        return "Добрый день! Чем можем помочь?"