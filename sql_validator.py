import pandas as pd
import re
from database import DEMO_DATABASE

class SQLSimulator:
    def __init__(self):
        self.tables = {
            "processing_operations": pd.DataFrame(DEMO_DATABASE["processing_operations"]),
            "partner_a_payments": pd.DataFrame(DEMO_DATABASE["partner_a_payments"]),
            "partner_b_payments": pd.DataFrame(DEMO_DATABASE["partner_b_payments"]),
            "operation_additional_data": pd.DataFrame(DEMO_DATABASE["operation_additional_data"]),
            "registry_statuses": pd.DataFrame(DEMO_DATABASE["registry_statuses"]),
            "commission_rates": pd.DataFrame(DEMO_DATABASE["commission_rates"])
        }
        
        # Приводим типы данных к корректным
        self._prepare_data_types()

    def _prepare_data_types(self):
        """Приведение типов данных для корректных операций"""
        for table_name, df in self.tables.items():
            # Определяем типы на основе данных
            for col in df.columns:
                if df[col].dtype == 'object':
                    # Пробуем преобразовать к числам где возможно
                    try:
                        df[col] = pd.to_numeric(df[col], errors='ignore')
                    except:
                        pass

    def execute_sql(self, sql_query):
        """Выполнение SQL запроса с полной поддержкой WHERE, JOIN, etc."""
        try:
            sql_lower = sql_query.lower().strip()
            
            # Базовый SELECT запрос
            if sql_lower.startswith('select'):
                return self._execute_select(sql_query)
            
            # UPDATE запрос - ОБНОВЛЕНО: недостаточные права
            elif sql_lower.startswith('update'):
                return None, "❌ ERROR: insufficient privileges for UPDATE operations"
                
            # INSERT запрос - ОБНОВЛЕНО: недостаточные права  
            elif sql_lower.startswith('insert'):
                return None, "❌ ERROR: insufficient privileges for INSERT operations"
                
            # DELETE запрос - ОБНОВЛЕНО: недостаточные права
            elif sql_lower.startswith('delete'):
                return None, "❌ ERROR: insufficient privileges for DELETE operations"
                
            # CREATE/DROP/ALTER - ОБНОВЛЕНО: недостаточные права
            elif any(word in sql_lower for word in ['create', 'drop', 'alter', 'truncate']):
                return None, "❌ ERROR: insufficient privileges for DDL operations"
                
            else:
                return None, "❌ Поддерживаются только SELECT запросы"
                
        except Exception as e:
            return None, f"❌ Ошибка выполнения: {str(e)}"

    def _execute_select(self, sql_query):
        """Обработка SELECT запросов"""
        # ОБНОВЛЕНО: Парсим с учетом алиасов
        select_match = re.search(r'select\s+(.*?)\s+from\s+(\w+)(?:\s+(\w+))?', sql_query.lower())
        if not select_match:
            return None, "❌ Неверный формат SELECT запроса"
            
        columns = select_match.group(1)
        table_name = select_match.group(2)
        table_alias = select_match.group(3)  # Может быть None
        
        if table_name not in self.tables:
            return None, f"❌ Таблица {table_name} не найдена"
            
        result = self.tables[table_name].copy()
        
        # ОБНОВЛЕНО: Обработка WHERE условий с алиасами
        where_match = re.search(r'where\s+(.*?)(?:\s+order by|\s+group by|\s*$)', sql_query.lower())
        if where_match:
            where_condition = where_match.group(1)
            # Заменяем алиасы на реальные имена таблиц в WHERE
            if table_alias:
                where_condition = where_condition.replace(f'{table_alias}.', '')
            result = self._apply_where_condition(result, where_condition)
        
        # ОБНОВЛЕНО: Обработка JOIN с алиасами
        if 'join' in sql_query.lower():
            result = self._apply_joins(sql_query, result, table_alias)
        
        # ОБНОВЛЕНО: Выбор колонок с алиасами
        if columns != '*':
            # Удаляем алиасы из названий колонок
            clean_columns = columns
            if table_alias:
                clean_columns = clean_columns.replace(f'{table_alias}.', '')
            
            selected_columns = [col.strip().split('.')[-1] for col in clean_columns.split(',')]  # Берем последнюю часть после точки
            missing_cols = [col for col in selected_columns if col not in result.columns]
            if missing_cols:
                return None, f"❌ Колонки не найдены: {missing_cols}"
            result = result[selected_columns]
        
        # ORDER BY с алиасами
        order_match = re.search(r'order by\s+(.*?)\s+(asc|desc)?', sql_query.lower())
        if order_match:
            order_column = order_match.group(1)
            # Удаляем алиас из названия колонки
            if table_alias and order_column.startswith(f'{table_alias}.'):
                order_column = order_column.replace(f'{table_alias}.', '')
            order_asc = order_match.group(2) != 'desc'
            if order_column in result.columns:
                result = result.sort_values(order_column, ascending=order_asc)
        
        return result, "✅ Запрос выполнен успешно"

    def _apply_where_condition(self, df, condition):
        """Применение условий WHERE любой сложности"""
        try:
            # Заменяем SQL операторы на Python
            condition = condition.replace('<>', '!=').replace('=', '==')
            
            # Безопасное выполнение условия
            return df.query(condition, engine='python')
        except:
            # Ручная обработка если query не сработал
            return self._manual_where_apply(df, condition)

    def _manual_where_apply(self, df, condition):
        """Ручное применение условий WHERE"""
        # Простые условия
        if ' and ' in condition:
            parts = condition.split(' and ')
            for part in parts:
                df = self._apply_simple_condition(df, part)
            return df
        elif ' or ' in condition:
            parts = condition.split(' or ')
            result_dfs = []
            for part in parts:
                result_dfs.append(self._apply_simple_condition(df, part))
            return pd.concat(result_dfs).drop_duplicates()
        else:
            return self._apply_simple_condition(df, condition)

    def _apply_simple_condition(self, df, condition):
        """Применение простого условия"""
        condition = condition.strip()
        
        # ОБНОВЛЕНО: Удаляем алиасы из условий
        condition = re.sub(r'\w+\.', '', condition)  # Удаляем "алиас." из условия
        
        # ОБНОВЛЕНО: Обработка IN и NOT IN
        if ' in (' in condition:
            col, values_str = condition.split(' in (')
            col = col.strip()
            values_str = values_str.rstrip(')')
            values = [v.strip().strip("'") for v in values_str.split(',')]
            return df[df[col].astype(str).isin(values)]
        
        elif ' not in (' in condition:
            col, values_str = condition.split(' not in (')
            col = col.strip()
            values_str = values_str.rstrip(')')
            values = [v.strip().strip("'") for v in values_str.split(',')]
            return df[~df[col].astype(str).isin(values)]
        
        # Обработка разных операторов
        for operator in ['==', '!=', '>=', '<=', '>', '<', ' like ']:
            if operator in condition:
                col, value = condition.split(operator)
                col = col.strip()
                value = value.strip().strip("'")
                
                # ОБНОВЛЕНО: Оба оператора != и <> обрабатываются как "не равно"
                if operator == '==':
                    return df[df[col].astype(str) == value]
                elif operator == '!=':  # Обрабатывает и != и <>
                    return df[df[col].astype(str) != value]
                elif operator == '>':
                    try:
                        return df[df[col] > float(value)]
                    except:
                        return df[df[col].astype(str) > value]
                elif operator == '<':
                    try:
                        return df[df[col] < float(value)]
                    except:
                        return df[df[col].astype(str) < value]
                elif operator == '>=':
                    try:
                        return df[df[col] >= float(value)]
                    except:
                        return df[df[col].astype(str) >= value]
                elif operator == '<=':
                    try:
                        return df[df[col] <= float(value)]
                    except:
                        return df[df[col].astype(str) <= value]
                elif operator == ' like ':
                    return df[df[col].astype(str).str.contains(value, case=False, na=False)]
        
        return df

    def _apply_joins(self, sql_query, base_df, base_alias):
        """Применение JOIN между таблицами"""
        sql_lower = sql_query.lower()
        
        # INNER JOIN
        if 'inner join' in sql_lower:
            join_match = re.search(r'inner join\s+(\w+)(?:\s+(\w+))?\s+on\s+(.*?)(?:\s+where|\s+order by|\s*$)', sql_lower)
            if join_match:
                join_table = join_match.group(1)
                join_alias = join_match.group(2)  # Может быть None
                join_condition = join_match.group(3)
                if join_table in self.tables:
                    # ОБНОВЛЕНО: Удаляем алиасы из условия JOIN
                    clean_condition = join_condition
                    if base_alias:
                        clean_condition = clean_condition.replace(f'{base_alias}.', '')
                    if join_alias:
                        clean_condition = clean_condition.replace(f'{join_alias}.', '')
                    return self._perform_join(base_df, self.tables[join_table], clean_condition, 'inner')
        
        # LEFT JOIN  
        elif 'left join' in sql_lower:
            join_match = re.search(r'left join\s+(\w+)(?:\s+(\w+))?\s+on\s+(.*?)(?:\s+where|\s+order by|\s*$)', sql_lower)
            if join_match:
                join_table = join_match.group(1)
                join_alias = join_match.group(2)  # Может быть None
                join_condition = join_match.group(3)
                if join_table in self.tables:
                    # ОБНОВЛЕНО: Удаляем алиасы из условия JOIN
                    clean_condition = join_condition
                    if base_alias:
                        clean_condition = clean_condition.replace(f'{base_alias}.', '')
                    if join_alias:
                        clean_condition = clean_condition.replace(f'{join_alias}.', '')
                    return self._perform_join(base_df, self.tables[join_table], clean_condition, 'left')
        
        return base_df

    def _perform_join(self, left_df, right_df, condition, join_type):
        """Выполнение JOIN операций"""
        # Парсим условие JOIN (простая реализация)
        if '=' in condition:
            left_col, right_col = condition.split('=')
            left_col = left_col.strip().split('.')[-1]  # Берем только имя колонки
            right_col = right_col.strip().split('.')[-1]  # Берем только имя колонки
            
            if left_col in left_df.columns and right_col in right_df.columns:
                if join_type == 'inner':
                    return pd.merge(left_df, right_df, left_on=left_col, right_on=right_col)
                elif join_type == 'left':
                    return pd.merge(left_df, right_df, left_on=left_col, right_on=right_col, how='left')
        
        return left_df

# Глобальный экземпляр симулятора
sql_simulator = SQLSimulator()

def validate_sql_query(sql_query):
    """Обертка для совместимости"""
    result, message = sql_simulator.execute_sql(sql_query)
    return result, message

# Для обратной совместимости (если где-то используется)
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
        import pandas as pd
        return pd.DataFrame(table_map[table_name])
    return None
