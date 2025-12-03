import pandas as pd
import re
import streamlit as st

class SQLSimulator:
    def __init__(self, demo_data):
        """demo_data — dict с таблицами из get_demo_database()"""
        self.tables = {
            "processing_operations": pd.DataFrame(demo_data["processing_operations"]),
            "partner_a_payments": pd.DataFrame(demo_data["partner_a_payments"]),
            "partner_b_payments": pd.DataFrame(demo_data["partner_b_payments"]),
            "operation_additional_data": pd.DataFrame(demo_data["operation_additional_data"]),
            "registry_statuses": pd.DataFrame(demo_data["registry_statuses"]),
            "commission_rates": pd.DataFrame(demo_data["commission_rates"])
        }
        self._prepare_data_types()

    def _prepare_data_types(self):
        for df in self.tables.values():
            for col in df.columns:
                if df[col].dtype == 'object':
                    try:
                        df[col] = pd.to_numeric(df[col], errors='ignore')
                    except:
                        pass

    def execute_sql(self, sql_query):
        try:
            sql_lower = sql_query.lower().strip()
            
            if sql_lower.startswith('select'):
                return self._execute_select(sql_query)
            elif any(kw in sql_lower for kw in ['update', 'insert', 'delete', 'drop', 'alter', 'create', 'truncate']):
                return None, "❌ ERROR: DML/DDL operations are not allowed in sandbox"
            else:
                return None, "❌ Only SELECT queries are supported"

        except Exception as e:
            return None, f"❌ Execution error: {str(e)}"

    def _execute_select(self, sql_query):
        try:
            sql_lower = sql_query.lower().strip()
            
            # Базовый парсинг SELECT ... FROM
            select_pattern = r'select\s+(.*?)\s+from\s+(\w+)(?:\s+(?:as\s+)?(\w+))?'
            select_match = re.search(select_pattern, sql_lower, re.IGNORECASE)
            if not select_match:
                return None, "❌ Invalid SELECT syntax. Expected: SELECT ... FROM table"
            
            columns_part = select_match.group(1).strip()
            table_name = select_match.group(2)
            table_alias = select_match.group(3)

            if table_name not in self.tables:
                return None, f"❌ Table not found: `{table_name}`"

            result = self.tables[table_name].copy()

            # Обработка JOIN
            if 'join' in sql_lower:
                result = self._apply_joins(sql_query, result, table_name)

            # Обработка WHERE
            where_match = re.search(r'where\s+(.*?)(?=\s+(?:order\s+by|group\s+by|limit|$))', sql_lower, re.IGNORECASE)
            if where_match:
                where_condition = where_match.group(1)
                result = self._apply_where_condition(result, where_condition, table_alias)

            # Обработка SELECT колонок
            if columns_part == '*':
                pass
            else:
                clean_columns = self._parse_columns(columns_part, table_alias, result.columns)
                missing = [c for c in clean_columns if c not in result.columns]
                if missing:
                    return None, f"❌ Columns not found: {missing}"
                result = result[clean_columns]

            # Обработка ORDER BY
            order_match = re.search(r'order\s+by\s+(\w+)(?:\s+(asc|desc))?', sql_lower, re.IGNORECASE)
            if order_match:
                col = order_match.group(1)
                asc = order_match.group(2) != 'desc'
                if col in result.columns:
                    result = result.sort_values(col, ascending=asc)
                else:
                    return None, f"❌ ORDER BY column not found: `{col}`"

            # Обработка LIMIT
            limit_match = re.search(r'limit\s+(\d+)', sql_lower, re.IGNORECASE)
            if limit_match:
                limit = int(limit_match.group(1))
                result = result.head(limit)

            # 🔒 Защита от DoS: лимит 1000 строк
            if len(result) > 1000:
                warning = f" (showing first 1000 of {len(result)} rows)"
                result = result.head(1000)
                return result, "✅ Query executed" + warning

            return result, "✅ Query executed successfully"

        except Exception as e:
            return None, f"❌ Query execution failed: {str(e)}"

    def _parse_columns(self, columns_part, table_alias, available_cols):
        cols = []
        for col in columns_part.split(','):
            col = col.strip().replace('"', '').replace("'", "")
            # Убираем алиасы: t1.name → name
            col = re.sub(r'^\w+\.', '', col)
            if table_alias and col.startswith(f'{table_alias}.'):
                col = col[len(table_alias)+1:]
            if col == '*':
                return list(available_cols)
            cols.append(col)
        return cols

    def _apply_joins(self, sql_query, base_df, base_table):
        sql_lower = sql_query.lower()
        
        # Поддержка INNER и LEFT JOIN
        join_types = [
            ('inner join', 'inner'),
            ('left join', 'left'),
        ]
        
        for kw, join_type in join_types:
            if kw in sql_lower:
                # Ищем первую JOIN-клаузулу
                pattern = rf'{kw}\s+(\w+)(?:\s+as\s+(\w+))?\s+on\s+(.*?)(?=\s+(?:where|order\s+by|limit|$|inner\s+join|left\s+join))'
                match = re.search(pattern, sql_lower, re.IGNORECASE)
                if match:
                    join_table = match.group(1)
                    join_alias = match.group(2)
                    condition = match.group(3)
                    
                    if join_table in self.tables:
                        right_df = self.tables[join_table]
                        result = self._perform_join(base_df, right_df, condition, join_type)
                        return result
        
        return base_df

    def _perform_join(self, left_df, right_df, condition, how='inner'):
        # Поддержка: t1.id = t2.id
        if '=' in condition:
            parts = condition.split('=')
            if len(parts) == 2:
                left_col = parts[0].strip().split('.')[-1]
                right_col = parts[1].strip().split('.')[-1]
                
                if left_col in left_df.columns and right_col in right_df.columns:
                    return pd.merge(left_df, right_df, 
                                  left_on=left_col, right_on=right_col, 
                                  how=how)
        return left_df

    def _apply_where_condition(self, df, condition, table_alias=None):
        try:
            # Нормализация: !=, <> → !=
            cond = condition.replace('<>', '!=').replace('=', '==')
            # Убираем алиасы
            cond = re.sub(r'\b\w+\.', '', cond)
            
            return df.query(cond, engine='python')
        except:
            return self._manual_where(df, condition)

    def _manual_where(self, df, condition):
        condition = condition.strip().lower()
        
        if '=' in condition and '>=' not in condition and '<=' not in condition and '!=' not in condition and '<>' not in condition:
            col, val = condition.split('=', 1)
            col, val = col.strip(), val.strip().strip("'\"")
            return df[df[col].astype(str) == val]
        
        elif '>' in condition and '>=' not in condition:
            col, val = condition.split('>', 1)
            col, val = col.strip(), val.strip()
            try:
                return df[df[col] > float(val)]
            except:
                return df[df[col].astype(str) > val]
        
        elif ' in (' in condition:
            col, vals = condition.split(' in (', 1)
            col = col.strip()
            vals = [v.strip().strip("'\"") for v in vals.rstrip(')').split(',')]
            return df[df[col].astype(str).isin(vals)]
        
        return df

# 🔥 Кэширование — критично для скорости
@st.cache_resource
def get_sql_simulator():
    from database import get_demo_database
    demo_data = get_demo_database()
    return SQLSimulator(demo_data)

def validate_sql_query(sql_query):
    simulator = get_sql_simulator()
    return simulator.execute_sql(sql_query)
