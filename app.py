# app.py — финальная версия, 955 строк
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

# Load configs
try:
    with open("triggers.json", "r", encoding="utf-8") as f:
        TRIGGERS = json.load(f)
except Exception as e:
    st.warning(f"⚠️ Не найден triggers.json: {e}")
    TRIGGERS = {"mvp_triggers": []}

try:
    with open("role_weights.json", "r", encoding="utf-8") as f:
        ROLE_WEIGHTS = json.load(f)
except Exception as e:
    st.warning(f"⚠️ Не найден role_weights.json: {e}")
    ROLE_WEIGHTS = {
        "role_weights": {
            "analyst": {"soft_skills": 20, "hard_skills": 30, "data_integrity": 40, "process_documentation": 10}
        }
    }

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
        st.session_state.user_profiles = {
            "alex_data": {
                "name": "Алексей Иванов",
                "first_name": "Алексей",
                "last_name": "Иванов",
                "avatar": "🧑‍💻",
                "role": "candidate",
                "email": "alex.data@example.com"
            },
            "reviewer": {
                "name": "Ревьюер Системы",
                "first_name": "Ревьюер",
                "last_name": "Системы",
                "avatar": "👨‍🏫",
                "role": "reviewer",
                "email": "reviewer@dataworklab.com"
            }
        }
        st.session_state.active_profile = "alex_data"
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
        st.session_state.custom_weights = None
        st.session_state.reviewer_role = "analyst"
        st.session_state.w_soft = 20
        st.session_state.w_hard = 30
        st.session_state.w_integrity = 40
        st.session_state.w_doc = 10
        st.session_state.pending_response_for = None
        st.session_state.pending_user_input = ""
        st.session_state.response_start_time = None
        st.session_state.last_check = 0

# ==========================================
# UI: sidebar — с badge’ами для непрочитанных
# ==========================================
def render_sidebar():
    with st.sidebar:
        st.image("https://placehold.co/40x40/4A90E2/FFFFFF?text=DW", width=40)
        st.title("🔍 DataWork Lab")
        
        # 👤 Профиль
        st.markdown("### 👤 Профиль")
        for profile_id, profile in st.session_state.user_profiles.items():
            if st.button(f"{profile['avatar']} @{profile_id}", key=f"profile_{profile_id}", use_container_width=True):
                st.session_state.active_profile = profile_id
                st.rerun()
        
        # 🟢 Модалка профиля
        current = st.session_state.user_profiles[st.session_state.active_profile]
        with st.expander(f"👤 {current['name']} ({current['role']})", expanded=True):
            st.markdown(f"**Имя:** {current['first_name']}")
            st.markdown(f"**Фамилия:** {current['last_name']}")
            st.markdown(f"**Роль:** {current['role']}")
            st.markdown(f"**Email:** {current['email']}")
            st.markdown(f"**Аватар:** {current['avatar']}")
        
        # 🔍 DEBUG: Статус OpenAI API ключа
        try:
            api_key = st.secrets.get("OPENAI_API_KEY", "NOT_SET")
            key_status = "✅ OK" if api_key and "sk-" in str(api_key) else "❌ MISSING"
            st.caption(f"🔑 OpenAI: {key_status}")
        except Exception as e:
            st.caption(f"⚠️ Secrets error: {str(e)[:30]}...")
        
        # 📁 Инструменты — фильтруем по роли
        st.markdown("### 📁 Рабочие инструменты")
        role = current["role"]
        
        if role == "candidate":
            if st.button("🔧 SQL Песочница", key="tab_sql", use_container_width=True):
                st.session_state.active_tab = "sql"
            if st.button("📚 База знаний", key="tab_kb", use_container_width=True):
                st.session_state.active_tab = "kb"
            if st.button("📝 Отчёт по задачам", key="tab_report", use_container_width=True):
                st.session_state.active_tab = "report"
            if st.button("📊 Показать отчёт", key="show_report", use_container_width=True, type="primary"):
                st.session_state.active_tab = "report_result"
            
            # 💬 Чаты — с badge’ами для непрочитанных
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
                # ✅ Подсчёт непрочитанных
                unread = sum(1 for m in st.session_state.chats[chat_id] 
                             if m['role'] == 'bot' and not m.get('read', False))
                
                button_label = label
                if unread > 0:
                    button_label += f" •{unread}"
                
                if st.button(button_label, key=f"chat_nav_{chat_id}", use_container_width=True):
                    st.session_state.active_chat = chat_id
                    st.session_state.active_tab = "chats"
                    st.rerun()
        
        else:  # reviewer
            if st.button("🧪 Сценарии", key="tab_scenarios", use_container_width=True):
                st.session_state.active_tab = "scenarios"
            if st.button("⚖️ Настроить оценку", key="tab_reviewer", use_container_width=True):
                st.session_state.active_tab = "reviewer"
            if st.button("📈 Отчёты по кандидатам", key="tab_reports_overview", use_container_width=True):
                st.session_state.active_tab = "reports_overview"
            if st.button("🕒 История выполненного", key="tab_history", use_container_width=True):
                st.session_state.active_tab = "history"
        
        # 🎯 Сценарии
        st.markdown("### 🎯 Обучение")
        if st.button("▶️ Запустить сценарий", key="start_scenario", use_container_width=True):
            st.session_state.active_scenario = "revenue_mismatch"
            st.session_state.scenario_start_time = time.time()
            st.success("Сценарий запущен!")
        
        if st.button("🔄 Обнулить прогресс", key="reset", use_container_width=True):
            st.session_state.clear()
            st.rerun()

# ==========================================
# UI: профили
# ==========================================
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

# ==========================================
# UI: сообщения — с поддержкой typing
# ==========================================
def render_message(msg, is_typing=False):
    from_user = msg['role'] == 'user'
    sender_name = "Вы" if from_user else msg.get('sender_name', 'Система')
    
    sender_icon = ""
    if from_user:
        sender_icon = "👤 "
    else:
        source = msg.get("source", "unknown")
        if source == "fallback":
            sender_icon = "🟡 "
        elif source == "openai":
            sender_icon = "🤖 "
        else:
            sender_icon = "❓ "
    
    status = ""
    if from_user:
        if msg.get('read', False):
            status = " <span style='color:#1080e5;'>✔️</span>"
        else:
            status = " <span style='color:#aaa;'>⏱️</span>"
    
    msg_class = "user-message" if from_user else "bot-message"
    
    # ✅ Поддержка "печатает…"
    if msg.get("typing", False):
        content = "печатает…"
    else:
        content = html.escape(msg['content'], quote=False)
        if is_typing:
            content = "печатает…"
    
    strong_tag = f"<strong>{sender_icon}:</strong>"
    st.markdown(f"""
    <div class='chat-message {msg_class}'>
        {strong_tag}{status}<br>
        {content}
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# UI: чат — ИСПРАВЛЕНО: один "печатает…"
# ==========================================
def display_chat(chat_id):
    display_names = {
        "alice": "Алиса Петрова",
        "maxim": "Максим Волков",
        "kirill": "Кирилл Смирнов",
        "dba_team": "#dba-team",
        "partner_a": "#partner_a_operations_chat",
        "partner_b": "#partner_b_operations_chat",
    }
    st.subheader(f"💬 {display_names[chat_id]}")
    
    # ✅ Помечаем bot-сообщения как прочитанные ТОЛЬКО при открытии чата
    if st.session_state.active_chat == chat_id:
        for msg in st.session_state.chats[chat_id]:
            if msg['role'] == 'bot' and not msg.get('read', False):
                msg['read'] = True
    
    # ✅ 1. Показываем профиль или описание
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
    
    # ✅ 2. Отображаем историю
    for msg in st.session_state.chats[chat_id]:
        render_message(msg, is_typing=False)
    
    # ✅ 3. "Печатает…", если ожидаем ответ
    if st.session_state.pending_response_for == chat_id:
        render_message({"role": "bot", "content": "", "sender_name": display_names[chat_id]}, is_typing=True)
    
    # ✅ 4. Форма отправки — только сообщение, без "печатает…"
    with st.form(key=f'chat_form_{chat_id}', clear_on_submit=True):
        user_input = st.text_input("Сообщение:", key=f"input_{chat_id}", placeholder="Напишите сообщение...")
        submitted = st.form_submit_button("Отправить", type="primary")
        if submitted and user_input.strip():
            # ✅ Сразу сохраняем сообщение
            st.session_state.chats[chat_id].append({
                "role": "user",
                "content": user_input.strip(),
                "read": False,
                "timestamp": time.time()
            })
            st.session_state.events.append({
                "type": "chat",
                "to": chat_id,
                "content": user_input.strip(),
                "timestamp": time.time()
            })
            
            # ✅ Устанавливаем флаг ожидания
            st.session_state.pending_response_for = chat_id
            st.session_state.pending_user_input = user_input.strip()
            st.session_state.response_start_time = time.time()
            
            # ✅ ЕДИНСТВЕННЫЙ st.rerun() — чтобы отобразить сообщение
            st.rerun()

# ==========================================
# UI: отчёт по задаче
# ==========================================
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
            
            # Оценка отчёта
            report_score = evaluator.evaluate_task_report(description, action, result)
            st.session_state.scores["process_documentation"] = max(0, min(12, st.session_state.scores["process_documentation"] + report_score["score"]))
            
            st.success("Отчёт сохранён!")
            st.rerun()
        else:
            st.warning("Заполните все поля.")

# ==========================================
# UI: схема БД
# ==========================================
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

# ==========================================
# UI: SQL песочница
# ==========================================
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
        # ✅ Кнопка ВЫПОЛНИТЬ — ПЕРЕМЕЩЕНА ВНИЗ, ПОД ПОЛЕМ
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
                
                # Лог событий + оценка
                st.session_state.events.append({"type": "sql", "query": sql_query, "timestamp": time.time()})
                triggers = evaluator.evaluate_sql_query(sql_query)
                for t in triggers:
                    for trig in TRIGGERS["mvp_triggers"]:
                        if trig["id"] == t["id"]:
                            st.session_state.scores[trig["block"]] = max(0, st.session_state.scores[trig["block"]] + t["points"])
                            break
        
        # Результаты — под кнопкой
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

# ==========================================
# UI: база знаний
# ==========================================
def knowledge_base():
    st.subheader("📚 База знаний")
    KNOWLEDGE_BASE = get_knowledge_base()
    for key, article in KNOWLEDGE_BASE.items():
        is_expanded = st.session_state.kb_expanded.get(key, False)
        with st.expander(article['title'], expanded=is_expanded):
            st.session_state.kb_expanded[key] = True
            st.markdown(article['content'])

# ==========================================
# UI: сценарий — БЕЗ st.rerun()
# ==========================================
def scenario_engine():
    if st.session_state.active_scenario and st.session_state.scenario_start_time:
        elapsed = time.time() - st.session_state.scenario_start_time
        if elapsed > 2 and not st.session_state.get('scenario_step_1'):
            st.session_state.chats["maxim"].append({
                "role": "bot",
                "content": "Нужна выручка за 15.01 к 11:00. ASAP!",
                "timestamp": time.time(),
                "read": False,
                "id": f"auto_{int(time.time() * 1000)}"
            })
            st.session_state.scenario_step_1 = True

# ==========================================
# UI: режим ревьюера
# ==========================================
def reviewer_mode():
    st.subheader("👨‍🏫 Режим ревьюера")
    
    role = st.selectbox(
        "Роль кандидата",
        ["analyst", "dba", "product_analyst"],
        index=["analyst", "dba", "product_analyst"].index(st.session_state.reviewer_role)
    )
    st.session_state.reviewer_role = role
    
    base = ROLE_WEIGHTS["role_weights"][role]
    
    soft = st.slider("Soft Skills", 0, 100, st.session_state.get("w_soft", base["soft_skills"]))
    hard = st.slider("Hard Skills", 0, 100, st.session_state.get("w_hard", base["hard_skills"]))
    integrity = st.slider("Data Integrity", 0, 100, st.session_state.get("w_integrity", base["data_integrity"]))
    doc = st.slider("Документация", 0, 100, st.session_state.get("w_doc", base["process_documentation"]))
    
    total = soft + hard + integrity + doc
    if total != 100:
        st.warning(f"⚠️ Сумма весов: {total}%. Приведите к 100%.")
    else:
        st.success("✅ Веса корректны")
    
    if st.button("💾 Применить", type="primary"):
        st.session_state.custom_weights = {
            "soft_skills": soft,
            "hard_skills": hard,
            "data_integrity": integrity,
            "process_documentation": doc
        }
        st.session_state.w_soft = soft
        st.session_state.w_hard = hard
        st.session_state.w_integrity = integrity
        st.session_state.w_doc = doc
        st.success("Конфигурация применена. Теперь отчёты будут использовать эти веса.")

# ==========================================
# UI: отчёт
# ==========================================
def report_result():
    st.subheader("🏆 Ваш отчёт по компетенциям")
    
    blocks = {
        "soft_skills": {"name": "Soft Skills", "score": st.session_state.scores["soft_skills"], "max": 100},
        "hard_skills": {"name": "Hard Skills", "score": st.session_state.scores["hard_skills"], "max": 100},
        "data_integrity": {"name": "Data Integrity", "score": st.session_state.scores["data_integrity"], "max": 100},
        "process_documentation": {"name": "Документация", "score": st.session_state.scores["process_documentation"], "max": 12}
    }
    
    weights = st.session_state.custom_weights or ROLE_WEIGHTS["role_weights"][st.session_state.reviewer_role]
    
    weighted_score = (
        blocks["soft_skills"]["score"] * weights["soft_skills"] +
        blocks["hard_skills"]["score"] * weights["hard_skills"] +
        blocks["data_integrity"]["score"] * weights["data_integrity"] +
        blocks["process_documentation"]["score"] * weights["process_documentation"]
    ) / 100

    st.metric("Итоговый балл", f"{weighted_score:.1f} / 100")
    
    for k, v in blocks.items():
        st.markdown(f"### {v['name']}")
        st.progress(min(v["score"] / v["max"], 1.0))
        st.write(f"{v['score']} / {v['max']}")
        st.markdown("---")
    
    # Радар
    fig = go.Figure(data=go.Scatterpolar(
        r=[min(v["score"], v["max"]) for v in blocks.values()],
        theta=[v["name"] for v in blocks.values()],
        fill='toself'
    ))
    st.plotly_chart(fig, use_container_width=True)
    
    # Рекомендации
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
# ✅ История выполненного (Вариант C) — ИСПРАВЛЕНО: profile["name"]
# ==========================================
def history_overview():
    st.subheader("🕒 История выполненного")
    
    if not st.session_state.events:
        st.info("История пуста. Запустите сценарий.")
        return
    
    # === 1. Собираем данные ===
    rows = []
    for event in st.session_state.events:
        profile = st.session_state.user_profiles[st.session_state.active_profile]
        scenario = st.session_state.active_scenario or "—" 
        ts = time.strftime("%H:%M:%S", time.localtime(event["timestamp"]))
        hour = int(time.strftime("%H", time.localtime(event["timestamp"])))
        
        if event["type"] == "chat":
            content = event["content"][:100] + ("..." if len(event["content"]) > 100 else "")
            event_str = f"💬 {content}"
            if "срок" in event["content"].lower() or "дедлайн" in event["content"].lower():
                trigger, points = "clarify_deadline", 10
            elif "спасибо" in event["content"].lower() or "пожалуйста" in event["content"].lower():
                trigger, points = "polite_language", 1
            else:
                trigger, points = "—", 0
            context = "—" 
        elif event["type"] == "sql":
            query = event["query"][:100] + ("..." if len(event["query"]) > 100 else "")
            event_str = f"🔍 `{query}`"
            if "registry_statuses" in event["query"] and "is_excluded" not in event["query"]:
                trigger, points = "missing_is_excluded", -20
            elif "CREATE TABLE" in event["query"] and "backup" in event["query"].lower():
                trigger, points = "create_backup_table", 10
            else:
                trigger, points = "—", 0
            context = "REG002" if "REG002" in event["query"] else "—"
        elif event["type"] == "report":
            event_str = "📝 Отчёт по задаче"
            trigger, points = "task_report_filled", 12
            context = "—"
        else:
            event_str, trigger, points, context = str(event), "—", 0, "—"
        
        rows.append({
            "Кандидат": profile["name"],
            "Сценарий": scenario,
            "Событие": event_str,
            "Время": ts,
            "Час": hour,
            "Триггер": trigger,
            "Баллы": points,
            "Контекст": context,
            "Тип": "positive" if points > 0 else "negative" if points < 0 else "neutral"
        })
    
    df = pd.DataFrame(rows)
    
    # === 2. Фильтры слева (в 2 колонки) ===
    col_filter, col_main = st.columns([1, 3])
    
    with col_filter:
        st.markdown("#### 🔍 Фильтры")
        
        candidates = ["Все"] + sorted(df["Кандидат"].unique().tolist())
        selected_candidate = st.selectbox("Кандидат", candidates, key="filter_candidate")
        
        scenarios = ["Все"] + sorted(df["Сценарий"].unique().tolist())
        selected_scenario = st.selectbox("Сценарий", scenarios, key="filter_scenario")
        
        triggers = ["Все"] + sorted([t for t in df["Триггер"].unique() if t != "—"])
        selected_triggers = st.multiselect("Триггеры", triggers, default=["Все"], key="filter_triggers")
        
        min_hour, max_hour = st.slider(
            "Время суток",
            0, 23, (8, 20),
            format="%d:00"
        )
        
        # Применяем фильтры
        filtered_df = df.copy()
        if selected_candidate != "Все":
            filtered_df = filtered_df[filtered_df["Кандидат"] == selected_candidate]
        if selected_scenario != "Все":
            filtered_df = filtered_df[filtered_df["Сценарий"] == selected_scenario]
        if "Все" not in selected_triggers:
            filtered_df = filtered_df[filtered_df["Триггер"].isin(selected_triggers)]
        filtered_df = filtered_df[(filtered_df["Час"] >= min_hour) & (filtered_df["Час"] <= max_hour)]
    
    with col_main:
        # === 3. Агрегаты сверху ===
        st.markdown("#### 📊 Сводка")
        col1, col2, col3, col4 = st.columns(4)
        
        total_events = len(filtered_df)
        avg_score = filtered_df["Баллы"].mean() if total_events else 0
        top_trigger = filtered_df["Триггер"].value_counts().index[0] if total_events else "—"
        total_time = f"{filtered_df['Час'].max() - filtered_df['Час'].min() + 1}ч" if total_events else "—"
        
        col1.metric("Событий", total_events)
        col2.metric("Средний балл", f"{avg_score:+.1f}")
        col3.metric("Топ-триггер", top_trigger)
        col4.metric("Длительность", total_time)
        
        # === 4. Таблица / Лента ===
        view_mode = st.radio("Просмотр", ["Таблица", "Лента"], horizontal=True, key="view_mode")
        
        if view_mode == "Таблица":
            st.dataframe(filtered_df[["Кандидат", "Сценарий", "Событие", "Время", "Триггер", "Баллы", "Контекст"]], 
                        use_container_width=True, height=400)
        else:
            st.markdown("#### 📜 Хронология")
            for _, row in filtered_df.iterrows():
                color = "#2AB27B" if row["Баллы"] > 0 else "#E33" if row["Баллы"] < 0 else "#888"
                icon = "✅" if row["Баллы"] > 0 else "❌" if row["Баллы"] < 0 else "—"
                st.markdown(f"""
                <div style="padding: 0.5rem; border-left: 3px solid {color}; margin: 0.5rem 0; font-size: 0.95rem;">
                    <small>{row['Время']} · {row['Кандидат']} · {row['Сценарий']}</small><br>
                    <strong>{row['Событие']}</strong><br>
                    <span style="color:{color}">{icon} {row['Триггер']} ({row['Баллы']})</span>
                    {" · " + row["Контекст"] if row["Контекст"] != "—" else ""}
                </div>
                """, unsafe_allow_html=True)
        
        # === 5. График внизу ===
        st.markdown("#### 📈 Распределение по времени")
        if not filtered_df.empty:
            # Агрегируем по часам и типу
            chart_data = filtered_df.groupby(["Час", "Тип"]).size().reset_index(name="count")
            fig = go.Figure()
            
            for t in ["positive", "negative", "neutral"]:
                subset = chart_data[chart_data["Тип"] == t]
                fig.add_trace(go.Bar(
                    x=subset["Час"],
                    y=subset["count"],
                    name={"positive": "✅ Позитив", "negative": "❌ Негатив", "neutral": "— Нейтрально"}[t],
                    marker_color={"positive": "#2AB27B", "negative": "#E33", "neutral": "#888"}[t]
                ))
            
            fig.update_layout(barmode='stack', xaxis_title="Час", yaxis_title="Кол-во событий")
            st.plotly_chart(fig, use_container_width=True)
        
        # === 6. Экспорт (внизу) ===
        if not filtered_df.empty:
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Скачать CSV",
                data=csv,
                file_name="datawork_history.csv",
                mime="text/csv"
            )

# ==========================================
# UI: stub-вкладки
# ==========================================
def scenario_manager():
    st.subheader("🧪 Управление сценариями")
    st.info("Скоро: редактирование сценариев через UI")

def reports_overview():
    st.subheader("📈 Отчёты по кандидатам")
    st.info("Скоро: сравнение кандидатов, экспорт PDF")

# ==========================================
# Main — ФИНАЛЬНАЯ ЛОГИКА
# ==========================================
def main():
    st.set_page_config(page_title="DataWork Lab", page_icon="🔍", layout="wide")
    initialize_session()
    render_sidebar()
    scenario_engine()
    
    # ✅ ГАРАНТИРОВАННОЕ обновление — даже если вы в чате
    if st.session_state.pending_response_for:
        elapsed = time.time() - st.session_state.response_start_time
        now = time.time()
        
        # Проверяем не чаще 200 мс
        if now - st.session_state.last_check > 0.2:
            st.session_state.last_check = now
        
        # Если прошло 1.5 сек — генерируем ответ
        if elapsed >= 1.5:
            try:
                from characters import get_ai_response_with_source
                response, source = get_ai_response_with_source(
                    st.session_state.pending_response_for,
                    st.session_state.pending_user_input
                )
            except Exception as e:
                response = f"❌ Ошибка: {str(e)}"
                source = "fallback"
            
            chat_id = st.session_state.pending_response_for
            
            # Удаляем ВСЕ "печатает…"
            st.session_state.chats[chat_id] = [
                msg for msg in st.session_state.chats[chat_id]
                if not msg.get("typing", False)
            ]
            
            # Добавляем ответ
            st.session_state.chats[chat_id].append({
                "role": "bot",
                "content": response,
                "source": source,
                "read": False
            })
            
            # Сбрасываем флаги
            st.session_state.pending_response_for = None
            st.session_state.pending_user_input = ""
            
            # ✅ ГАРАНТИРОВАННЫЙ st.rerun() — даже если вы в чате
            st.rerun()
        
        else:
            # Показываем "печатает…", если его нет
            chat_id = st.session_state.pending_response_for
            has_typing = any(msg.get("typing", False) for msg in st.session_state.chats[chat_id])
            if not has_typing:
                st.session_state.chats[chat_id].append({
                    "role": "bot",
                    "content": "",
                    "typing": True
                })
                # ✅ Дополнительный st.rerun(), чтобы отобразить "печатает…" сразу
                st.rerun()
    
    # ... остальной код ...
    current_role = st.session_state.user_profiles[st.session_state.active_profile]["role"]
    
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
    elif st.session_state.active_tab == "reviewer":
        reviewer_mode()
    elif st.session_state.active_tab == "scenarios":
        scenario_manager()
    elif st.session_state.active_tab == "reports_overview":
        reports_overview()
    elif st.session_state.active_tab == "history":
        history_overview()

if __name__ == "__main__":
    main()
