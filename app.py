# app.py
import streamlit as st
import pandas as pd
import time
import html
from datetime import datetime

# Lazy-импорты — критично для cold start!
def get_demo_database():
    from database import get_demo_database as _get
    return _get()

def get_openai_client():
    if 'openai_client' not in st.session_state:
        from ai_client import OpenAIClient
        st.session_state.openai_client = OpenAIClient()
    return st.session_state.openai_client

def get_characters_responses():
    import characters  # ← локальный импорт, безопасный
    return characters.CHARACTERS_RESPONSES, characters.GROUP_CHATS

def get_database_schema():
    from database_schema import DATABASE_SCHEMA
    return DATABASE_SCHEMA

def get_knowledge_base():
    from knowledge_base import KNOWLEDGE_BASE
    return KNOWLEDGE_BASE

def validate_sql_query(sql_query):
    from sql_validator import validate_sql_query as _validate
    return _validate(sql_query)

# ========================
# Инициализация сессии
# ========================
def initialize_session():
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        
        # 👤 Профиль пользователя
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
        
        # 📚 База знаний — открытые статьи
        st.session_state.kb_expanded = {}
        
        # 🎯 Сценарии
        st.session_state.active_scenario = None
        st.session_state.scenario_start_time = None

# ========================
# UI Компоненты
# ========================
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
            # Подсчёт непрочитанных
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
        
        # 🎯 Сценарии (временно)
        st.markdown("### 🎯 Обучение")
        if st.button("▶️ Запустить сценарий", key="start_scenario", use_container_width=True, type="primary"):
            st.session_state.active_scenario = "revenue_mismatch"
            st.session_state.scenario_start_time = time.time()
            st.success("Сценарий запущен! Первое сообщение придет через 5 секунд.")
        
        # 🗑️ Сброс
        if st.button("🔄 Обнулить прогресс", key="reset", use_container_width=True):
            st.session_state.clear()
            st.rerun()

def render_chat_header(chat_id):
    display_names = {
        "alice": "Алиса Петрова",
        "maxim": "Максим Волков",
        "kirill": "Кирилл Смирнов",
        "dba_team": "#dba-team",
        "partner_a": "#partner_a_operations_chat",
        "partner_b": "#partner_b_operations_chat",
    }
    st.subheader(f"💬 {display_names[chat_id]}")

def render_message(msg, is_last=False, is_typing=False):
    from_user = msg['role'] == 'user'
    sender_name = "Вы" if from_user else msg.get('sender_name', 'Система')
    
    # Иконки отправителей (для групп)
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
    
    # Классы
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
    render_chat_header(chat_id)
    
    # Получаем персонажа
    CHARACTERS_RESPONSES, GROUP_CHATS = get_characters_responses()
    char_config = CHARACTERS_RESPONSES.get(chat_id) or GROUP_CHATS.get(chat_id)
    
    # Отображаем историю
    chat_history = st.session_state.chats[chat_id]
    for i, msg in enumerate(chat_history):
        is_last = (i == len(chat_history) - 1)
        render_message(msg, is_last=is_last)
    
    # Индикатор "печатает", если последнее сообщение — наше, и бот ещё не ответил
    if chat_history and chat_history[-1]['role'] == 'user' and not chat_history[-1].get('read', False):
        fake_bot_msg = {"role": "bot", "content": "", "sender_name": char_config['name']}
        render_message(fake_bot_msg, is_typing=True)
    
    # Форма ввода
    with st.form(key=f'chat_form_{chat_id}', clear_on_submit=True):
        user_input = st.text_input("Сообщение:", key=f"input_{chat_id}")
        submitted = st.form_submit_button("Отправить")
        
        if submitted and user_input.strip():
            # Добавляем сообщение пользователя
            new_msg = {
                "role": "user",
                "content": user_input.strip(),
                "timestamp": time.time(),
                "read": False,
                "id": f"msg_{int(time.time()*1000)}"
            }
            st.session_state.chats[chat_id].append(new_msg)
            
            # Планируем обработку (без st.rerun — пусть UI обновится сам)
            st.session_state[f'pending_response_{chat_id}'] = user_input.strip()
            st.rerun()

def process_ai_response(chat_id):
    """Обрабатывает ответ после отображения сообщения пользователя"""
    pending_key = f'pending_response_{chat_id}'
    if pending_key not in st.session_state or not st.session_state[pending_key]:
        return
    
    user_message = st.session_state[pending_key]
    
    # Получаем конфиг чата
    CHARACTERS_RESPONSES, GROUP_CHATS = get_characters_responses()
    char_config = CHARACTERS_RESPONSES.get(chat_id) or GROUP_CHATS.get(chat_id)
    
    # Получаем клиента (lazy)
    client = get_openai_client()
    
    # Задержка (реалистичное "ожидание прочтения")
    delays = {
        "alice": 8, "maxim": 25, "kirill": 12,
        "dba_team": 15, "partner_a": 18, "partner_b": 22
    }
    delay = delays.get(chat_id, 10)
    
    # Имитация: сначала "прочитано", потом "печатает", потом ответ
    time.sleep(delay - 2)
    
    # Помечаем как прочитано
    if st.session_state.chats[chat_id]:
        st.session_state.chats[chat_id][-1]["read"] = True
    st.rerun()  # → покажет ✔️ + "печатает…"
    
    time.sleep(2)  # имитация набора текста
    
    # Генерация ответа
    try:
        if chat_id in CHARACTERS_RESPONSES:
            response = CHARACTERS_RESPONSES[chat_id]['get_response'](user_message)
        else:
            response = GROUP_CHATS[chat_id]['get_response'](user_message)
    except Exception as e:
        response = f"❌ Ошибка генерации: {str(e)}"
    
    # Имена в групповых чатах
    sender_names = {
        "dba_team": "Михаил Шилин",
        "partner_a": "Анна Новикова",
        "partner_b": "Дмитрий Семенов",
    }
    
    # Добавляем ответ
    bot_msg = {
        "role": "bot",
        "content": response,
        "timestamp": time.time(),
        "read": True,
        "sender_name": sender_names.get(chat_id, char_config['name']),
        "id": f"msg_{int(time.time()*1000)}"
    }
    st.session_state.chats[chat_id].append(bot_msg)
    
    # Очищаем pending
    st.session_state[pending_key] = None
    st.rerun()

def sql_sandbox():
    st.subheader("🔧 SQL Песочница")
    
    # Ввод
    col1, col2 = st.columns([3, 1])
    with col1:
        sql_query = st.text_area("SQL запрос:", 
                                value=st.session_state.get('sql_last_query', ''),
                                height=120,
                                key="sql_input")
    with col2:
        if st.button("▶️ Выполнить", type="primary", key="run_sql"):
            if sql_query.strip():
                st.session_state.sql_last_query = sql_query
                result, feedback = validate_sql_query(sql_query)
                st.session_state.sql_last_result = result
                st.session_state.sql_last_feedback = feedback
                
                # Сохраняем в историю
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
        st.dataframe(st.session_state.sql_last_result)
    if st.session_state.sql_last_feedback:
        st.info(f"💡 {st.session_state.sql_last_feedback}")
    
    # История
    with st.expander("🕒 История запросов (последние 10)", expanded=False):
        if st.session_state.sql_history:
            for i, item in enumerate(reversed(st.session_state.sql_history)):
                with st.container():
                    st.code(item["query"], language="sql")
                    if item["result"] is not None:
                        st.dataframe(item["result"], use_container_width=True)
                    if item["feedback"]:
                        st.caption(item["feedback"])
                    st.markdown("---")
        else:
            st.caption("История пуста")

def knowledge_base():
    st.subheader("📚 База знаний")
    KNOWLEDGE_BASE = get_knowledge_base()
    
    for key, article in KNOWLEDGE_BASE.items():
        is_expanded = st.session_state.kb_expanded.get(key, False)
        with st.expander(article['title'], expanded=is_expanded):
            st.session_state.kb_expanded[key] = True
            st.markdown(article['content'])

def scenario_engine():
    """Заготовка под сценарии (реализуем далее)"""
    if st.session_state.active_scenario and st.session_state.scenario_start_time:
        elapsed = time.time() - st.session_state.scenario_start_time
        
        # Пример: через 5 сек — первое сообщение от Максима
        if elapsed > 5 and not st.session_state.get('scenario_step_1'):
            # Имитация входящего сообщения
            st.session_state.chats["maxim"].append({
                "role": "bot",
                "content": "Нужна выручка за 15.01 к 11:00. ASAP!",
                "timestamp": time.time(),
                "read": False,
                "sender_name": "Максим Волков",
                "id": f"msg_auto_{int(time.time()*1000)}"
            })
            st.session_state.scenario_step_1 = True
            st.rerun()

# ========================
# Main
# ========================
def main():
    st.set_page_config(
        page_title="DataWork Lab",
        page_icon="🔍",
        layout="wide"
    )
    
    # CSS (без изменений — оставляем ваш)
    st.markdown("""
    <style>
        .chat-message { ... } /* ваш CSS */
    </style>
    """, unsafe_allow_html=True)
    
    initialize_session()
    render_sidebar()
    scenario_engine()  # фоновая логика сценариев
    
    # Основной контент
    if st.session_state.active_tab == "chats":
        display_chat(st.session_state.active_chat)
        process_ai_response(st.session_state.active_chat)
    elif st.session_state.active_tab == "sql":
        sql_sandbox()
    else:
        knowledge_base()

if __name__ == "__main__":
    main()
