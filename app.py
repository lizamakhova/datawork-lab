# app.py
import streamlit as st
import pandas as pd
import time
import html
import json
import plotly.graph_objects as go
from datetime import datetime

# Lazy imports
def get_demo_database():
    from database import get_demo_database as _get
    return _get()

def get_database_schema():
    from database_schema import DATABASE_SCHEMA
    return DATABASE_SCHEMA

def get_knowledge_base():
    from knowledge_base import KNOWLEDGE_BASE
    return KNOWLEDGE_BASE

def validate_sql_query(sql_query):
    from sql_validator import validate_sql_query as _validate
    return _validate(sql_query)

# Load triggers
try:
    with open("triggers.json", "r", encoding="utf-8") as f:
        TRIGGERS = json.load(f)
except Exception as e:
    st.warning(f"⚠️ Не найден triggers.json: {e}")
    TRIGGERS = {"mvp_triggers": []}

from text_evaluator import TextEvaluator
evaluator = TextEvaluator()

# ==========================================
# Стили
# ==========================================
st.markdown("""
<style>
    .chat-message {
        padding: 1rem; 
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid var(--border-color, #e0e0e0);
        background: var(--message-bg, white);
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        color: var(--text-color, #333333) !important;
        line-height: 1.5;
    }
    .user-message {
        margin-left: 2.5rem;
        margin-right: 0.5rem;
        border-left: 4px solid var(--user-accent, #4A90E2);
        background: var(--user-bg, #F0F8FF);
    }
    .bot-message {
        margin-right: 2.5rem;
        margin-left: 0.5rem;
        border-left: 4px solid var(--bot-accent, #2AB27B);
        background: var(--bot-bg, #F6FFFE);
    }
    .chat-message strong {
        color: var(--strong-text, #1D1C1D) !important;
        font-weight: 600;
        font-size: 0.95rem;
    }
    
    :root {
        --border-color: #e0e0e0;
        --message-bg: white;
        --text-color: #333333;
        --user-accent: #4A90E2;
        --user-bg: #F0F8FF;
        --bot-accent: #2AB27B; 
        --bot-bg: #F6FFFE;
        --strong-text: #1D1C1D;
    }
    
    @media (prefers-color-scheme: dark) {
        :root {
            --border-color: #444444;
            --message-bg: #2D3748;
            --text-color: #E2E8F0;
            --user-accent: #63B3ED;
            --user-bg: #2A4365;
            --bot-accent: #68D391;
            --bot-bg: #22543D;
            --strong-text: #F7FAFC;
        }
    }
    
    .stApp[data-theme="dark"] {
        --border-color: #444444;
        --message-bg: #2D3748;
        --text-color: #E2E8F0;
        --user-accent: #63B3ED;
        --user-bg: #2A4365;
        --bot-accent: #68D391;
        --bot-bg: #22543D;
        --strong-text: #F7FAFC;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# Инициализация
# ==========================================
def initialize_session():
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.user_profile = {
            "name": "Алексей", 
            "nickname": "alex_data",
            "avatar": "🧑‍💻",
            "role": "candidate"
        }
        CHAT_KEYS = ["alice", "maxim", "kirill", "dba_team", "partner_a", "partner_b"]
        st.session_state.chats = {key: [] for key in CHAT_KEYS}
        st.session_state.active_chat = "alice"
        st.session_state.active_tab = "chats"
        st.session_state.sql_history = []
        st.session_state.sql_last_result = None
        st.session_state.sql_last_feedback = ""
        st.session_state.sql_last_query = ""
        st.session_state.kb_expanded = {}
        st.session_state.active_scenario = None
        st.session_state.scenario_start_time = None
        st.session_state.task_reports = []
        st.session_state.scores = {
            "soft_skills": 0,
            "hard_skills": 0,
            "data_integrity": 0,
            "process_documentation": 0
        }
        st.session_state.events = []

# ==========================================
# UI
# ==========================================
def render_sidebar():
    with st.sidebar:
        st.image("https://placehold.co/40x40/4A90E2/FFFFFF?text=DW", width=40)
        st.title("🔍 DataWork Lab")
        
        # 👤 Профиль
        st.markdown(f"""
        <div style='text-align: center; margin: 1rem 0; padding: 1rem; border-radius: 12px; background: #f8f9fa;'>
            <div style='font-size: 36px;'>{st.session_state.user_profile['avatar']}</div>
            <div><strong>{st.session_state.user_profile['name']}</strong></div>
            <div style='color: #666;'>@{st.session_state.user_profile['nickname']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 📌 Чаты — ✅ ДИНАМИЧЕСКИЙ СЧЁТЧИК
        st.markdown("### 💬 Чаты")
        chat_labels = {
            "alice": "👩‍💼 Алиса Петрова",
            "maxim": "👨‍💼 Максим Волков",
            "kirill": "👨 Кирилл Смирнов",
            "dba_team": "🛠️ #dba-team",
            "partner_a": "🤝 #partner_a_operations_chat",
            "partner_b": "🤝 #partner_b_operations_chat",
        }
        for chat_id, label in chat_labels.items():
            unread = sum(1 for m in st.session_state.chats[chat_id] 
                         if m['role'] == 'bot' and not m.get('read', False))
            badge = f" ({unread})" if unread > 0 else ""
            if st.button(f"{label}{badge}", key=f"nav_{chat_id}", use_container_width=True):
                st.session_state.active_chat = chat_id
                st.session_state.active_tab = "chats"
        
        # 📁 Инструменты
        st.markdown("### 📁 Рабочие инструменты")
        if st.button("🔧 SQL Песочница", key="tab_sql", use_container_width=True):
            st.session_state.active_tab = "sql"
        if st.button("📚 База знаний", key="tab_kb", use_container_width=True):
            st.session_state.active_tab = "kb"
        if st.button("📝 Отчёт по задачам", key="tab_report", use_container_width=True):
            st.session_state.active_tab = "report"
        if st.button("📊 Показать отчёт", key="show_report", use_container_width=True, type="primary"):
            st.session_state.active_tab = "report_result"
        
        # 🎯 Сценарии
        st.markdown("### 🎯 Обучение")
        if st.button("▶️ Запустить сценарий", key="start_scenario", use_container_width=True):
            st.session_state.active_scenario = "revenue_mismatch"
            st.session_state.scenario_start_time = time.time()
            st.success("Сценарий запущен!")
        
        if st.button("🔄 Обнулить прогресс", key="reset", use_container_width=True):
            st.session_state.clear()
            st.rerun()

def display_profile(chat_id):
    profiles = {
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
        },
        "kirill": {
            "full_name": "Кирилл Смирнов",
            "photo": "👨",
            "status": "🟢 Онлайн",
            "role": "Продакт-менеджер",
            "department": "Продуктовый отдел",
            "work_hours": "10:00-19:00 МСК"
        }
    }
    if chat_id in profiles:
        p = profiles[chat_id]
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.2rem;
            border-radius: 16px;
            margin-bottom: 1.2rem;
            color: white;
            font-size: 0.95rem;
        '>
            <div style='display: flex; align-items: center; gap: 1rem;'>
                <div style='
                    font-size: 48px; 
                    background: white; 
                    border-radius: 50%; 
                    width: 60px; 
                    height: 60px; 
                    display: flex; 
                    align-items: center; 
                    justify-content: center;
                '>
                    {p['photo']}
                </div>
                <div>
                    <h4 style='margin: 0 0 0.3rem 0; color: white;'>{p['full_name']}</h4>
                    <div style='display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.4rem; font-size: 0.85rem;'>
                        <span style='background: rgba(255,255,255,0.2); padding: 0.25rem 0.8rem; border-radius: 20px;'>
                            {p['role']}
                        </span>
                        <span style='background: rgba(255,255,255,0.2); padding: 0.25rem 0.8rem; border-radius: 20px;'>
                            {p['department']}
                        </span>
                    </div>
                    <div style='display: flex; align-items: center; gap: 1rem; font-size: 0.85rem;'>
                        <span>{p['status']}</span>
                        <span>🕐 {p['work_hours']}</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_message(msg, is_typing=False):
    from_user = msg['role'] == 'user'
    sender_name = "Вы" if from_user else msg.get('sender_name', 'Система')
    sender_icon = ""
    if not from_user:
        icons = {
            "Алиса Петрова": "👩‍💼",
            "Максим Волков": "👨‍💼",
            "Кирилл Смирнов": "👨",
            "Михаил Шилин": "👨‍🔧",
            "Анна Новикова": "👩",
            "Дмитрий Семенов": "👨",
        }
        sender_icon = icons.get(sender_name, "") + " "
    status = ""
    if from_user:
        if msg.get('read', False):
            status = " <span style='color:#1080e5;'>✔️</span>"
        else:
            status = " <span style='color:#aaa;'>⏱️</span>"
    msg_class = "user-message" if from_user else "bot-message"
    content = html.escape(msg['content'], quote=False)
    if is_typing:
        content = "печатает…"
    st.markdown(f"""
    <div class='chat-message {msg_class}'>
        <strong>{sender_icon}{sender_name}:</strong>{status}<br>
        {content}
    </div>
    """, unsafe_allow_html=True)

def display_chat(chat_id):
    # ✅ АВТОМАТИЧЕСКИ ПОМЕЧАЕМ ВСЕ СООБЩЕНИЯ ЧАТА КАК ПРОЧИТАННЫЕ
    for msg in st.session_state.chats[chat_id]:
        if msg['role'] == 'bot' and not msg.get('read', False):
            msg['read'] = True
    
    display_names = {
        "alice": "Алиса Петрова",
        "maxim": "Максим Волков",
        "kirill": "Кирилл Смирнов",
        "dba_team": "#dba-team",
        "partner_a": "#partner_a_operations_chat",
        "partner_b": "#partner_b_operations_chat",
    }
    st.subheader(f"💬 {display_names[chat_id]}")
    if chat_id in ["alice", "maxim", "kirill"]:
        display_profile(chat_id)
    else:
        GROUP_CHATS = {
            "dba_team": {"description": "Команда баз данных — выполняем SQL запросы", "members": "3 участника"},
            "partner_a": {"description": "Операции с Партнером А — вопросы по реестрам и комиссиям", "members": "Поддержка Партнер А + наша команда"},
            "partner_b": {"description": "Операции с Партнером Б — согласование реестров и статусов", "members": "Поддержка Партнер Б + наша команда"}
        }
        gc = GROUP_CHATS[chat_id]
        st.caption(f"{gc['description']} • {gc['members']}")
    
    for msg in st.session_state.chats[chat_id]:
        render_message(msg, is_typing=False)
    
    if st.session_state.chats[chat_id] and st.session_state.chats[chat_id][-1]['role'] == 'user' and not st.session_state.chats[chat_id][-1].get('read', False):
        render_message({"role": "bot", "content": "", "sender_name": display_names[chat_id]}, is_typing=True)
    
    with st.form(key=f'chat_form_{chat_id}', clear_on_submit=True):
        user_input = st.text_input("Сообщение:", key=f"input_{chat_id}", placeholder="Напишите сообщение...")
        submitted = st.form_submit_button("Отправить", type="primary")
        if submitted and user_input.strip():
            new_msg = {
                "role": "user",
                "content": user_input.strip(),
                "timestamp": time.time(),
                "read": False,
                "id": f"msg_{int(time.time()*1000)}"
            }
            st.session_state.chats[chat_id].append(new_msg)
            st.session_state.events.append({"type": "chat", "to": chat_id, "content": user_input.strip(), "timestamp": time.time()})
            
            # Оценка сообщения
            triggers = evaluator.evaluate_chat_message(user_input.strip(), to=chat_id)
            for t in triggers:
                for trig in TRIGGERS["mvp_triggers"]:
                    if trig["id"] == t["id"]:
                        st.session_state.scores[trig["block"]] += t["points"]
                        break
            
            try:
                from characters import CHARACTERS_RESPONSES
                response = CHARACTERS_RESPONSES[chat_id]['get_response'](user_input.strip())
                sender_names = {
                    "dba_team": "Михаил Шилин",
                    "partner_a": "Анна Новикова",
                    "partner_b": "Дмитрий Семенов",
                }
                st.session_state.chats[chat_id].append({
                    "role": "bot",
                    "content": response,
                    "timestamp": time.time(),
                    "read": True,
                    "sender_name": sender_names.get(chat_id, display_names[chat_id]),
                    "id": f"msg_{int(time.time()*1000)}"
                })
            except Exception as e:
                st.session_state.chats[chat_id].append({
                    "role": "bot",
                    "content": f"❌ Ошибка: {str(e)}",
                    "sender_name": "Система",
                    "read": True
                })
            st.rerun()

def task_report_form():
    st.subheader("📝 Новый отчёт по задаче")
    st.caption("Документируйте шаги для аудита и передачи контекста. Подробнее — в базе знаний.")
    
    description = st.text_area(
        "1. Описание проблемы",
        placeholder="Метрика, период, расхождение в цифрах",
        height=80
    )
    
    action = st.text_area(
        "2. Что правим",
        placeholder="Таблица, данные, запрос, меры предосторожности",
        height=100
    )
    
    result = st.text_area(
        "3. Фактический результат",
        placeholder="Состояние до/после, способ проверки, остаточное расхождение",
        height=100
    )
    
    if st.session_state.sql_history:
        recent_queries = [item["query"] for item in st.session_state.sql_history[-5:]]
        selected_sql = st.selectbox(
            "Вставить последний SQL-запрос",
            options=["— не выбрано —"] + recent_queries,
            key="report_sql_select"
        )
        if selected_sql != "— не выбрано —":
            if not action.strip():
                action = f"```sql\n{selected_sql}\n```"
            else:
                action += f"\n\n```sql\n{selected_sql}\n```"
    
    if st.button("✅ Сохранить отчёт", type="primary"):
        if description.strip() and action.strip() and result.strip():
            new_report = {
                "id": f"report_{int(time.time())}",
                "timestamp": time.time(),
                "description": description.strip(),
                "action": action.strip(),
                "result": result.strip()
            }
            st.session_state.task_reports.append(new_report)
            st.session_state.events.append({"type": "report", "data": new_report, "timestamp": time.time()})
            
            report_score = evaluator.evaluate_task_report(description, action, result)
            st.session_state.scores["process_documentation"] += report_score["score"]
            
            st.success("Отчёт сохранён!")
            st.rerun()
        else:
            st.warning("Заполните все поля.")

def show_database_schema():
    st.markdown("#### 🗃️ Схема базы данных")
    DATABASE_SCHEMA = get_database_schema()
    selected_table = st.selectbox("Выберите таблицу:", list(DATABASE_SCHEMA.keys()), key="schema_table")
    if selected_table:
        table_info = DATABASE_SCHEMA[selected_table]
        st.markdown(f"**Описание:** {table_info['description']}")
        st.markdown("---")
        st.markdown("**Структура таблицы:**")
        cols = st.columns([2, 2, 1, 3])
        cols[0].markdown("**Колонка**")
        cols[1].markdown("**Тип**")
        cols[2].markdown("**Ключ**")
        cols[3].markdown("**Описание**")
        for col_name, col_info in table_info['columns'].items():
            c0, c1, c2, c3 = st.columns([2, 2, 1, 3])
            c0.code(col_name)
            c1.code(col_info['type'])
            if col_info.get('pk'):
                c2.markdown("🔑")
            elif col_info.get('fk'):
                c2.markdown("🔗")
            else:
                c2.markdown("")
            c3.write(col_info['description'])

def sql_sandbox():
    st.subheader("🔧 SQL Песочница")
    tab1, tab2 = st.tabs(["📝 SQL Запрос", "🗃️ Схема БД"])
    
    with tab1:
        col1, col2 = st.columns([3, 1])
        with col1:
            sql_query = st.text_area("SQL запрос:", 
                                    value=st.session_state.get("sql_last_query", ""),
                                    height=120,
                                    key="sql_input")
        with col2:
            if st.button("▶️ Выполнить", type="primary", key="run_sql", use_container_width=True):
                if sql_query.strip():
                    st.session_state.sql_last_query = sql_query
                    result, feedback = validate_sql_query(sql_query)
                    st.session_state.sql_last_result = result
                    st.session_state.sql_last_feedback = feedback
                    st.session_state.sql_history.append({
                        "query": sql_query,
                        "result": result.copy() if result is not None else None,
                        "feedback": feedback,
                        "timestamp": time.time()
                    })
                    st.session_state.sql_history = st.session_state.sql_history[-10:]
                    
                    st.session_state.events.append({"type": "sql", "query": sql_query, "timestamp": time.time()})
                    triggers = evaluator.evaluate_sql_query(sql_query)
                    for t in triggers:
                        for trig in TRIGGERS["mvp_triggers"]:
                            if trig["id"] == t["id"]:
                                st.session_state.scores[trig["block"]] += t["points"]
                                break
        
        if st.session_state.sql_last_result is not None:
            st.success("✅ Запрос выполнен")
            st.dataframe(st.session_state.sql_last_result, use_container_width=True)
        if st.session_state.sql_last_feedback:
            st.info(f"💡 {st.session_state.sql_last_feedback}")
        
        with st.expander("🕒 История запросов (последние 10)", expanded=False):
            for item in reversed(st.session_state.sql_history):
                st.code(item["query"], language="sql")
                if item["result"] is not None:
                    st.dataframe(item["result"], use_container_width=True)
                if item["feedback"]:
                    st.caption(item["feedback"])
                st.markdown("---")
    
    with tab2:
        show_database_schema()

def knowledge_base():
    st.subheader("📚 База знаний")
    KNOWLEDGE_BASE = get_knowledge_base()
    for key, article in KNOWLEDGE_BASE.items():
        is_expanded = st.session_state.kb_expanded.get(key, False)
        with st.expander(article['title'], expanded=is_expanded):
            st.session_state.kb_expanded[key] = True
            st.markdown(article['content'])

def scenario_engine():
    if st.session_state.active_scenario and st.session_state.scenario_start_time:
        elapsed = time.time() - st.session_state.scenario_start_time
        
        # Максим — через 2 сек
        if elapsed > 2 and not st.session_state.get('scenario_step_1'):
            st.session_state.chats["maxim"].append({
                "role": "bot",
                "content": "Нужна выручка за 15.01 к 11:00. ASAP!",
                "timestamp": time.time(),
                "read": False,
                "sender_name": "Максим Волков",
                "id": f"auto_{int(time.time() * 1000)}"
            })
            st.session_state.scenario_step_1 = True
            st.rerun()
        
        # ✅ Кирилл — через 30 сек (конфликт дедлайнов)
        if elapsed > 30 and not st.session_state.get('scenario_step_kirill'):
            st.session_state.chats["kirill"].append({
                "role": "bot",
                "content": "У меня тут тоже горит! Проверь статусы в реестре Партнёра А — они не совпадают с нашими данными. К 11:00!",
                "timestamp": time.time(),
                "read": False,
                "sender_name": "Кирилл Смирнов",
                "id": f"auto_kirill_{int(time.time() * 1000)}"
            })
            st.session_state.scenario_step_kirill = True
            st.rerun()

def report_result():
    st.subheader("🏆 Ваш отчёт по компетенциям")
    
    blocks = {
        "soft_skills": {"name": "Soft Skills", "score": st.session_state.scores["soft_skills"], "max": 100},
        "hard_skills": {"name": "Hard Skills", "score": st.session_state.scores["hard_skills"], "max": 100},
        "data_integrity": {"name": "Data Integrity", "score": st.session_state.scores["data_integrity"], "max": 100},
        "process_documentation": {"name": "Документация", "score": st.session_state.scores["process_documentation"], "max": 12}
    }
    
    for k, v in blocks.items():
        st.markdown(f"### {v['name']}")
        st.progress(min(v["score"] / v["max"], 1.0))
        st.write(f"**{v['score']} / {v['max']}**")
        if k == "process_documentation" and v["score"] < 12:
            st.caption("🔹 Заполните все 3 пункта отчёта для максимума")
        st.markdown("---")
    
    fig = go.Figure(data=go.Scatterpolar(
        r=[min(v["score"], v["max"]) for v in blocks.values()],
        theta=[v["name"] for v in blocks.values()],
        fill='toself',
        name='Ваш профиль'
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)
    
    recommendations = []
    if blocks["soft_skills"]["score"] < 70:
        recommendations.append("🔹 Практикуйте уточнение сроков и приоритетов перед началом задачи")
    if blocks["data_integrity"]["score"] < 70:
        recommendations.append("🔹 Обратите внимание на работу с метаданными (is_excluded, registry_statuses)")
    if blocks["process_documentation"]["score"] < 10:
        recommendations.append("🔹 Используйте шаблон оформления задачи из базы знаний")
    
    if recommendations:
        st.subheader("📈 Рекомендации")
        for rec in recommendations:
            st.info(rec)

# ==========================================
# Main
# ==========================================
def main():
    st.set_page_config(page_title="DataWork Lab", page_icon="🔍", layout="wide")
    initialize_session()
    render_sidebar()
    scenario_engine()
    
    if st.session_state.active_tab == "chats":
        display_chat(st.session_state.active_chat)
    elif st.session_state.active_tab == "sql":
        sql_sandbox()
    elif st.session_state.active_tab == "kb":
        knowledge_base()
    elif st.session_state.active_tab == "report":
        task_report_form()
        if st.session_state.task_reports:
            st.subheader("📋 Сохранённые отчёты")
            for rep in reversed(st.session_state.task_reports):
                with st.expander(f"Отчёт от {time.strftime('%H:%M', time.localtime(rep['timestamp']))}"):
                    st.markdown(f"**1. Описание проблемы**\n\n{rep['description']}")
                    st.markdown(f"**2. Что правим**\n\n{rep['action']}")
                    st.markdown(f"**3. Фактический результат**\n\n{rep['result']}")
    elif st.session_state.active_tab == "report_result":
        report_result()

if __name__ == "__main__":
    main()
