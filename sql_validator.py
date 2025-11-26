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
        self._prepare_data_types()

    def _prepare_data_types(self):
        for table_name, df in self.tables.items():
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
            elif sql_lower.startswith('update'):
                return None, "❌ ERROR: insufficient privileges for UPDATE operations"
            elif sql_lower.startswith('insert'):
                return None, "❌ ERROR: insufficient privileges for INSERT operations"
            elif sql_lower.startswith('delete'):
                return None, "❌ ERROR: insufficient privileges for DELETE operations"
            elif any(word in sql_lower for word in ['create', 'drop', 'alter', 'truncate']):
                return None, "❌ ERROR: insufficient privileges for DDL operations"
            else:
                return None, "❌ Поддерживаются только SELECT запросы"
                
        except Exception as e:
            return None, f"❌ Ошибка выполнения: {str(e)}"

    def _execute_select(self, sql_query):
        try:
            sql_lower = sql_query.lower().strip()
            
            select_pattern = r'select\s+(.*?)\s+from\s+(\w+)(?:\s+(?:as\s+)?(\w+))?'
            select_match = re.search(select_pattern, sql_lower)
            
            if not select_match:
                return None, "❌ Неверный формат SELECT запроса"
                
            columns_part = select_match.group(1)
            table_name = select_match.group(2)
            table_alias = select_match.group(3)
            
            if table_name not in self.tables:
                return None, f"❌ Таблица {table_name} не найдена"
                
            result = self.tables[table_name].copy()
            
            where_match = re.search(r'where\s+(.*?)(?:\s+order\s+by|\s+group\s+by|\s+limit|\s*$)', sql_lower, re.IGNORECASE)
            if where_match:
                where_condition = where_match.group(1)
                if table_alias:
                    where_condition = re.sub(rf'\b{table_alias}\.\s*(\w+)', r'\1', where_condition)
                where_condition = re.sub(r'\b\w+\.\s*(\w+)', r'\1', where_condition)
                result = self._apply_where_condition(result, where_condition)
            
            if 'join' in sql_lower:
                result = self._apply_joins_with_aliases(sql_query, result, table_name, table_alias)
            
            if columns_part.strip() == '*':
                pass
            else:
                clean_columns = []
                for col in columns_part.split(','):
                    col = col.strip()
                    if table_alias and col.startswith(f'{table_alias}.'):
                        col = col.replace(f'{table_alias}.', '')
                    col = re.sub(r'^\w+\.', '', col)
                    col = col.replace('"', '').replace("'", "").strip()
                    
                    if col == '*':
                        clean_columns = list(result.columns)
                        break
                    clean_columns.append(col)
                
                missing_cols = [col for col in clean_columns if col not in result.columns]
                if missing_cols:
                    return None, f"❌ Колонки не найдены: {missing_cols}"
                result = result[clean_columns]
            
            order_match = re.search(r'order\s+by\s+(.*?)(?:\s+(asc|desc))?(?:\s+limit|\s*$)', sql_lower, re.IGNORECASE)
            if order_match:
                order_column = order_match.group(1).strip()
                if table_alias and order_column.startswith(f'{table_alias}.'):
                    order_column = order_column.replace(f'{table_alias}.', '')
                order_column = re.sub(r'^\w+\.', '', order_column)
                order_column = order_column.replace('"', '').replace("'", "")
                
                order_asc = order_match.group(2) != 'desc'
                if order_column in result.columns:
                    result = result.sort_values(order_column, ascending=order_asc)
                else:
                    return None, f"❌ Колонка для ORDER BY не найдена: {order_column}"
            
            return result, "✅ Запрос выполнен успешно"
            
        except Exception as e:
            return None, f"❌ Ошибка выполнения: {str(e)}"

    def _apply_joins_with_aliases(self, sql_query, base_df, base_table, base_alias):
        sql_lower = sql_query.lower()
        
        if 'inner join' in sql_lower:
            join_pattern = r'inner\s+join\s+(\w+)(?:\s+(?:as\s+)?(\w+))?\s+on\s+(.*?)(?:\s+where|\s+order\s+by|\s+group\s+by|\s*$)'
            join_match = re.search(join_pattern, sql_lower, re.IGNORECASE)
            if join_match:
                join_table = join_match.group(1)
                join_alias = join_match.group(2)
                join_condition = join_match.group(3)
                
                if join_table in self.tables:
                    clean_condition = join_condition
                    
                    if base_alias:
                        clean_condition = re.sub(rf'\b{base_alias}\.\s*(\w+)', r'\1', clean_condition)
                    if join_alias:
                        clean_condition = re.sub(rf'\b{join_alias}\.\s*(\w+)', r'\1', clean_condition)
                    clean_condition = re.sub(r'\b\w+\.\s*(\w+)', r'\1', clean_condition)
                    
                    return self._perform_join(base_df, self.tables[join_table], clean_condition, 'inner')
        
        elif 'left join' in sql_lower:
            join_pattern = r'left\s+join\s+(\w+)(?:\s+(?:as\s+)?(\w+))?\s+on\s+(.*?)(?:\s+where|\s+order\s+by|\s+group\s+by|\s*$)'
            join_match = re.search(join_pattern, sql_lower, re.IGNORECASE)
            if join_match:
                join_table = join_match.group(1)
                join_alias = join_match.group(2)
                join_condition = join_match.group(3)
                
                if join_table in self.tables:
                    clean_condition = join_condition
                    
                    if base_alias:
                        clean_condition = re.sub(rf'\b{base_alias}\.\s*(\w+)', r'\1', clean_condition)
                    if join_alias:
                        clean_condition = re.sub(rf'\b{join_alias}\.\s*(\w+)', r'\1', clean_condition)
                    clean_condition = re.sub(r'\b\w+\.\s*(\w+)', r'\1', clean_condition)
                    
                    return self._perform_join(base_df, self.tables[join_table], clean_condition, 'left')
        
        return base_df

    def _apply_where_condition(self, df, condition):
        try:
            condition = condition.replace('<>', '!=').replace('=', '==')
            condition = re.sub(r'\b\w+\.\s*(\w+)', r'\1', condition)
            return df.query(condition, engine='python')
        except Exception as e:
            return self._manual_where_apply(df, condition)

    def _manual_where_apply(self, df, condition):
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
        condition = condition.strip()
        condition = re.sub(r'\w+\.', '', condition)
        
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
        
        for operator in ['==', '!=', '>=', '<=', '>', '<', ' like ']:
            if operator in condition:
                col, value = condition.split(operator)
                col = col.strip()
                value = value.strip().strip("'")
                
                if operator == '==':
                    return df[df[col].astype(str) == value]
                elif operator == '!=':
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

    def _perform_join(self, left_df, right_df, condition, join_type):
        if '=' in condition:
            left_col, right_col = condition.split('=')
            left_col = left_col.strip().split('.')[-1]
            right_col = right_col.strip().split('.')[-1]
            
            if left_col in left_df.columns and right_col in right_df.columns:
                if join_type == 'inner':
                    return pd.merge(left_df, right_df, left_on=left_col, right_on=right_col)
                elif join_type == 'left':
                    return pd.merge(left_df, right_df, left_on=left_col, right_on=right_col, how='left')
        
        return left_df

sql_simulator = SQLSimulator()

def validate_sql_query(sql_query):
    result, message = sql_simulator.execute_sql(sql_query)
    return result, message

def get_dataframe(table_name):
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
