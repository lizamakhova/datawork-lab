# text_evaluator.py
import re

class TextEvaluator:
    def __init__(self):
        self.synonyms = {
            "root_cause": [r"потому\s+что", r"из-за", r"причин[аоы]", r"почему\s+так"],
            "polite": [r"спасибо", r"пожалуйста", r"можно\s+попросить", r"не\s+могли\s+бы"],
            "specific_id": [r"[a-z]{3}_\d{3}", r"PA\d{3}", r"PB\d{3}"],
            "blame_partner": [r"ошибка\s+у\s+вас", r"неправильн\w*\s+данн\w*", r"вы\s+сломали"],
            "blame_colleague": [r"ты\s+можешь\s+конкретнее", r"вы\s+некорректно"],
            "backup_request": [r"бэкап", r"резервн\w*\s+копи", r"CREATE\s+TABLE.*_backup"]
        }

    def evaluate_task_report(self, description: str, action: str, result: str) -> dict:
        score = 0
        feedback = []

        # 1. Описание проблемы
        if re.search(r"\d+[\.,]\d{2}", description) and re.search(r"выручк|расхожден", description, re.I):
            score += 3
        elif re.search(r"выручк|расхожден", description, re.I):
            score += 1

        # 2. Что правим
        if re.search(r"(processing_operations|UPDATE|CREATE\s+TABLE)", action, re.I) and "backup" in action.lower():
            score += 3
        elif re.search(r"(поправ|измен)", action, re.I):
            score += 1

        # 3. Фактический результат
        if re.search(r"(было.*\d+.*стало.*\d+|до.*\d+.*после.*\d+)", result, re.I) and "провер" in result.lower():
            score += 3
        elif re.search(r"(сделано|готово)", result, re.I):
            score += 1

        return {
            "block": "process_documentation",
            "score": min(score, 12),
            "max_score": 12,
            "feedback": feedback
        }

    def evaluate_chat_message(self, message: str, to: str = None) -> list:
        triggers = []
        msg_low = message.lower()

        if any(re.search(p, msg_low) for p in self.synonyms["polite"]):
            triggers.append({"id": "polite_language", "points": 1})
        if to in ["partner_a", "partner_b"] and any(re.search(p, msg_low) for p in self.synonyms["blame_partner"]):
            triggers.append({"id": "blame_partner", "points": -15})
        if any(re.search(p, msg_low) for p in self.synonyms["root_cause"]):
            triggers.append({"id": "root_cause_analysis", "points": 5})
        if any(re.search(p, message) for p in self.synonyms["specific_id"]):
            triggers.append({"id": "specific_reference", "points": 3})
        if any(re.search(p, msg_low) for p in self.synonyms["backup_request"]):
            triggers.append({"id": "create_backup_table", "points": 10})
        if "баз" in msg_low and ("знани" in msg_low or "kb" in msg_low):
            triggers.append({"id": "kb_search_before_ask", "points": 3})
        if re.search(r"что\s+значит|где\s+он", msg_low) and not re.search(r"баз[ау]\s+знаний", msg_low):
            triggers.append({"id": "no_kb_search", "points": -5})

        return triggers

    def evaluate_sql_query(self, query: str) -> list:
        triggers = []
        q = query.lower()

        if re.search(r"join\s+\w+\s+(?!on)", q):
            triggers.append({"id": "join_without_on", "points": -15})
        if "registry_statuses" in query and "is_excluded" not in query:
            triggers.append({"id": "missing_is_excluded", "points": -20})
        if "operation_additional_data" in query and "partner_operation_id" in query:
            triggers.append({"id": "use_additional_data_correctly", "points": 10})
        if "create table" in q and "backup" in q:
            triggers.append({"id": "create_backup_table", "points": 10})

        return triggers
