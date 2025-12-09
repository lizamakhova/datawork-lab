# report_generator.py
import json
import plotly.graph_objects as go

def generate_report(events, triggers_config):
    """
    Генерирует отчёт на основе событий и триггеров.
    events: list of {"type": "chat"/"sql"/"report", ...}
    triggers_config: содержимое triggers.json
    """
    # Базовые баллы
    scores = {
        "soft_skills": 0,
        "hard_skills": 0,
        "data_integrity": 0,
        "process_documentation": 0
    }
    feedback = {
        "soft_skills": [],
        "hard_skills": [],
        "data_integrity": [],
        "process_documentation": []
    }

    # Оценка событий
    for event in events:
        if event["type"] == "chat":
            from text_evaluator import TextEvaluator
            evaluator = TextEvaluator()
            triggers = evaluator.evaluate_chat_message(event["content"], to=event.get("to"))
            for t in triggers:
                for trig in triggers_config["mvp_triggers"]:
                    if trig["id"] == t["id"]:
                        scores[trig["block"]] += t["points"]
                        if t["points"] != 0:
                            feedback[trig["block"]].append(trig["feedback"])
                        break

        elif event["type"] == "sql":
            from text_evaluator import TextEvaluator
            evaluator = TextEvaluator()
            triggers = evaluator.evaluate_sql_query(event["query"])
            for t in triggers:
                for trig in triggers_config["mvp_triggers"]:
                    if trig["id"] == t["id"]:
                        scores[trig["block"]] += t["points"]
                        if t["points"] != 0:
                            feedback[trig["block"]].append(trig["feedback"])
                        break

        elif event["type"] == "report":
            from text_evaluator import TextEvaluator
            evaluator = TextEvaluator()
            report = event["data"]
            result = evaluator.evaluate_task_report(
                report["description"],
                report["action"],
                report["result"]
            )
            scores[result["block"]] += result["score"]
            for fb in result["feedback"]:
                feedback[result["block"]].append(fb)

    # Формируем структуру отчёта
    blocks = {
        "soft_skills": {
            "name": "Soft Skills",
            "score": max(0, min(100, scores["soft_skills"])),
            "max_score": 100,
            "feedback": list(set(feedback["soft_skills"]))
        },
        "hard_skills": {
            "name": "Hard Skills",
            "score": max(0, min(100, scores["hard_skills"])),
            "max_score": 100,
            "feedback": list(set(feedback["hard_skills"]))
        },
        "data_integrity": {
            "name": "Data Integrity",
            "score": max(0, min(100, scores["data_integrity"])),
            "max_score": 100,
            "feedback": list(set(feedback["data_integrity"]))
        },
        "process_documentation": {
            "name": "Документация",
            "score": max(0, min(12, scores["process_documentation"])),
            "max_score": 12,
            "feedback": list(set(feedback["process_documentation"]))
        }
    }

    # Рекомендации
    recommendations = []
    if blocks["soft_skills"]["score"] < 70:
        recommendations.append("🔹 Практикуйте уточнение сроков и приоритетов перед началом задачи")
    if blocks["data_integrity"]["score"] < 70:
        recommendations.append("🔹 Обратите внимание на работу с метаданными (is_excluded, registry_statuses)")
    if blocks["process_documentation"]["score"] < 10:
        recommendations.append("🔹 Используйте шаблон оформления задачи из базы знаний")

    return {
        "blocks": blocks,
        "total_score": sum(b["score"] for b in blocks.values()),
        "max_total": 312,
        "recommendations": recommendations,
        "radar_data": {
            "r": [blocks[k]["score"] for k in blocks],
            "theta": [blocks[k]["name"] for k in blocks]
        }
    }
