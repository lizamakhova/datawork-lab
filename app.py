# app.py
import streamlit as st
import pandas as pd
import time
import html
from datetime import datetime

# ==========================================
# Lazy imports — критично для cold start
# ==========================================
def get_demo_database():
    from database import get_demo_database as _get
    return _get()

def get_openai_client():
    if 'openai_client' not in st.session_state:
        from ai_client import OpenAIClient
        st.session_state.openai_client = OpenAIClient()
    return st.session_state.openai_client

def get_database_schema():
    from database_schema import DATABASE_SCHEMA
    return DATABASE_SCHEMA

def get_knowledge_base():
    from knowledge_base import KNOWLEDGE_BASE
    return KNOWLEDGE_BASE

def validate_sql_query(sql_query):
    from sql_validator import validate_sql_query as _validate
    return _validate(sql_query)

# ==========================================
# Стили — мессенджер-интерфейс
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
# Инициализация сессии
# ==========================================
def initialize_session():
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        
        # 👤 Профиль
        st.session_state.user_profile = {
            "name": "Алексей", 
            "nickname": "alex_data",
            "avatar": "🧑‍💻"
        }
        
        # 💬 Чаты
        CHAT_KEYS = ["alice", "maxim", "kirill", "dba_team", "partner_a", "partner_b"]
        st.session_state.chats = {key: [] for key in CHAT_KEYS}
        st.session_state.active_chat = "alice"
        st.session_state.active_tab = "chats"
        
        # 📜 История SQL
        st.session_state.sql_history = []
        st.session_state.sql_last_result = None
        st.session_state.sql_last_feedback = ""
        st.session_state.sql_last_query = ""
        
        # 📚 База знаний
        st.session_state.kb_expanded = {}
        
        # 🎯 Сценарии
        st.session_state.active_scenario = None
        st.session_state.scenario_start_time = None

# ==========================================
# UI: sidebar
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
        
        # 📌 Чаты
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
            badge = f" <span style='background:#e33;color:white;padding:1px 6px;border-radius:10px;font-size:10px;'>{unread}</span>" if unread else ""
            
            if st.button(f"{label}{badge}", key=f"nav_{chat_id}", use_container_width=True):
                st.session_state.active_chat = chat_id
                st.session_state.active_tab = "chats"
        
        # 📁 Инструменты
        st.markdown("### 📁 Рабочие инструменты")
        if st.button("🔧 SQL Песочница", key="tab_sql", use_container_width=True):
            st.session_state.active_tab = "sql"
        if st.button("📚 База знаний", key="tab_kb", use_container_width=True):
            st.session_state.active_tab = "kb"
        
        # 🎯 Сценарии
        st.markdown("### 🎯 Обучение")
        if st.button("▶️ Запустить сценарий", key="start_scenario", use_container_width=True, type="primary"):
            st.session_state.active_scenario = "revenue_mismatch"
            st.session_state.scenario_start_time = time.time()
            st.success("Сценарий запущен!")
        
        # 🗑️ Сброс
        if st.button("🔄 Обнулить прогресс", key="reset", use_container_width=True):
            st.session_state.clear()
            st.rerun()

# ==========================================
# UI: профили персонажей
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
# UI: отображение чата
# ==========================================
def render_message(msg, is_last=False, is_typing=False):
    from_user = msg['role'] == 'user'
    sender_name = "Вы" if from_user else msg.get('sender_name', 'Система')
    
    # Иконки
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
    
    # Статус прочтения
    status = ""
    if from_user:
        if msg.get('read', False):
            status = " <span style='color:#1080e5;'>✔️</span>"
        else:
            status = " <span style='color:#aaa;'>⏱️</span>"
    
    # Класс
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
    # Заголовок
    display_names = {
        "alice": "Алиса Петрова",
        "maxim": "Максим Волков",
        "kirill": "Кирилл Смирнов",
        "dba_team": "#dba-team",
        "partner_a": "#partner_a_operations_chat",
        "partner_b": "#partner_b_operations_chat",
    }
    st.subheader(f"💬 {display_names[chat_id]}")
    
    # 👤 Профиль / описание
    if chat_id in ["alice", "maxim", "kirill"]:
        display_profile(chat_id)
    else:
        # Групповые чаты — описание
        GROUP_CHATS = {
            "dba_team": {
                "name": "#dba-team",
                "description": "Команда баз данных — выполняем SQL запросы",
                "members": "3 участника"
            },
            "partner_a": {
                "name": "#partner_a_operations_chat",
                "description": "Операции с Партнером А — вопросы по реестрам и комиссиям",
                "members": "Поддержка Партнер А + наша команда"
            },
            "partner_b": {
                "name": "#partner_b_operations_chat",
                "description": "Операции с Партнером Б — согласование реестров и статусов",
                "members": "Поддержка Партнер Б + наша команда"
            }
        }
        gc = GROUP_CHATS[chat_id]
        st.caption(f"{gc['description']} • {gc['members']}")
    
    # История
    chat_history = st.session_state.chats[chat_id]
    for i, msg in enumerate(chat_history):
        is_last = (i == len(chat_history) - 1)
        render_message(msg, is_last=is_last)
    
    # Индикатор "печатает"
    if chat_history and chat_history[-1]['role'] == 'user' and not chat_history[-1].get('read', False):
        fake_bot = {"role": "bot", "content": "", "sender_name": display_names[chat_id]}
        render_message(fake_bot, is_typing=True)
    
    # ✅ Форма — только один раз, после истории
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
            st.session_state[f'pending_response_{chat_id}'] = user_input.strip()
            st.rerun()

# ==========================================
# SQL Песочница
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

def sql_sandbox():
    st.subheader("🔧 SQL Песочница")
    tab1, tab2 = st.tabs(["📝 SQL Запрос", "🗃️ Схема БД"])
    
    with tab1:
        col1, col2 = st.columns([3, 1])
        with col1:
            sql_query = st.text_area("SQL запрос:", 
                                    value=st.session_state.sql_last_query,
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
        
        # Результат
        if st.session_state.sql_last_result is not None:
            st.success("✅ Запрос выполнен")
            st.dataframe(st.session_state.sql_last_result, use_container_width=True)
        if st.session_state.sql_last_feedback:
            st.info(f"💡 {st.session_state.sql_last_feedback}")
        
        # История
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
# База знаний
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
# Сценарий (заготовка)
# ==========================================
def scenario_engine():
    if st.session_state.active_scenario and st.session_state.scenario_start_time:
        elapsed = time.time() - st.session_state.scenario_start_time
        if elapsed > 2 and not st.session_state.get('scenario_step_1'):
            # Первое сообщение от Максима
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

# ==========================================
# Main
# ==========================================
def main():
    st.set_page_config(
        page_title="DataWork Lab",
        page_icon="🔍",
        layout="wide"
    )
    
    initialize_session()
    render_sidebar()
    scenario_engine()
    
    # Основной контент
    if st.session_state.active_tab == "chats":
        display_chat(st.session_state.active_chat)
        # Обработка AI — только если есть pending
        if f'pending_response_{st.session_state.active_chat}' in st.session_state:
            from characters import get_ai_response
            CHARACTERS_RESPONSES, GROUP_CHATS = {}, {}  # не нужны здесь
            chat_id = st.session_state.active_chat
            pending_key = f'pending_response_{chat_id}'
            if st.session_state.get(pending_key):
                user_msg = st.session_state[pending_key]
                
                # Задержка (ускоренная для демо)
                import random
                delays = {"alice": 2, "maxim": 5, "kirill": 2, "dba_team": 2, "partner_a": 3, "partner_b": 3}
                time.sleep(delays.get(chat_id, 2))
                
                # Помечаем как прочитано
                if st.session_state.chats[chat_id]:
                    st.session_state.chats[chat_id][-1]["read"] = True
                st.rerun()
                
                # Генерация ответа
                response = get_ai_response(chat_id, user_msg)
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
                    "sender_name": sender_names.get(chat_id, 
                        {"alice": "Алиса Петрова", "maxim": "Максим Волков", "kirill": "Кирилл Смирнов"}[chat_id]),
                    "id": f"msg_{int(time.time()*1000)}"
                })
                st.session_state[pending_key] = None
                st.rerun()
    
    elif st.session_state.active_tab == "sql":
        sql_sandbox()
    
    else:
        knowledge_base()

if __name__ == "__main__":
    main()
