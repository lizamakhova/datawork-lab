import pandas as pd
from database import DEMO_DATABASE

def validate_sql_query(sql_query):
    """
    Базовая валидация SQL запросов
    Возвращает (результат, фидбек)
    """
    sql_lower = sql_query.lower().strip()
    
    try:
        # Преобразуем данные в DataFrame для простоты
        processing_ops = pd.DataFrame(DEMO_DATABASE["processing_operations"])
        partner_a = pd.DataFrame(DEMO_DATABASE["partner_a_payments"])
        partner_b = pd.DataFrame(DEMO_DATABASE["partner_b_payments"])
        additional_data = pd.DataFrame(DEMO_DATABASE["operation_additional_data"])
        registries = pd.DataFrame(DEMO_DATABASE["registry_statuses"])
        commission_rates = pd.DataFrame(DEMO_DATABASE["commission_rates"])
        
        # Безопасное выполнение простых запросов
        if "select" in sql_lower and "processing_operations" in sql_lower:
            if "status = 'success'" in sql_lower:
                result = processing_ops[processing_ops['status'] == 'success']
                feedback = "✅ Найдены успешные операции. Не забудь проверить статусы партнеров!"
                return result, feedback
            
            elif "amount > 100" in sql_lower:
                result = processing_ops[processing_ops['amount'] > 100]
                feedback = "✅ Найдены операции больше 100 EUR"
                return result, feedback
                
            else:
                result = processing_ops.head(10)
                feedback = "✅ Показаны первые 10 операций. Уточни условия выборки!"
                return result, feedback
        
        # Проверка расхождений статусов
        elif any(word in sql_lower for word in ["расхожден", "discrep", "join", "partner"]):
            # Эмулируем сложный запрос
            success_ops = processing_ops[processing_ops['status'] == 'success']
            feedback = "💡 Для проверки расхождений нужно соединить processing_operations с partner_a_payments через partner_operation_id и сравнить статусы"
            return None, feedback
        
        # Проверка комиссий  
        elif any(word in sql_lower for word in ["комисс", "commission"]):
            feedback = "💡 Для проверки комиссий нужно сравнить commission_amount в processing_operations с расчетом по commission_rates"
            return None, feedback
            
        else:
            feedback = "⚠️ Запрос распознан. Для сложных запросов обратись к Алисе за помощью с JOIN"
            return None, feedback
            
    except Exception as e:
        return None, f"❌ Ошибка выполнения: {str(e)}. Проверь синтаксис SQL"

def get_dataframe(table_name):
    """Получение DataFrame по имени таблицы"""
    table_map = {
        "processing_operations": DEMO_DATABASE["processing_operations"],
        "partner_a_payments": DEMO_DATABASE["partner_a_payments"],
        "partner_b_payments": DEMO_DATABASE["partner_b_payments"], 
        "operation_additional_data": DEMO_DATABASE["operation_additional_data"],
        "registry_statuses": DEMO_DATABASE["registry_statuses"],
        "commission_rates": DEMO_DATABASE["commission_rates"]
    }
    
    if table_name in table_map:
        return pd.DataFrame(table_map[table_name])
    return None