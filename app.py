import streamlit as st
import pandas as pd
import random
from database import DEMO_DATABASE
from characters import CHARACTERS_RESPONSES, CHARACTERS_PROFILES, GROUP_CHATS
from sql_validator import validate_sql_query
from knowledge_base import KNOWLEDGE_BASE
from database_schema import DATABASE_SCHEMA

# Настройка страницы
st.set_page_config(
    page_title="DataWork Lab",
    page_icon="🔍",
    layout="wide"
)

# Универсальные стили для светлой/темной темы
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
    }
    .user-message {
        margin-left: 3rem;
        border-left: 4px solid var(--user-accent, #4A90E2);
        background: var(--user-bg, #F0F8FF);
    }
    .bot-message {
        margin-right: 3rem; 
        border-left: 4px solid var(--bot-accent, #2AB27B);
        background: var(--bot-bg, #F6FFFE);
    }
    .chat-message strong {
        color: var(--strong-text, #1D1C1D) !important;
        font-weight: 600;
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
    
    .ai-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        margin-left: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

def initialize_chat():
    if 'chats' not in st.session_state:
        st.session_state.chats = {
            'alice': [], 'maxim': [], 'dba_team': [], 
            'partner_a': [], 'partner_b': []
        }

def display_profile(character_key):
    if character_key in CHARACTERS_PROFILES:
        profile = CHARACTERS_PROFILES[character_key]
        st.markdown(f"""
        <div style='
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 16px;
            margin-bottom: 1.5rem;
            color: white;
        '>
            <div style='display: flex; align-items: center; gap: 1.5rem;'>
                <div style='
                    font-size: 64px; 
                    background: white; 
                    border-radius: 50%; 
                    width: 80px; 
                    height: 80px; 
                    display: flex; 
                    align-items: center; 
                    justify-content: center;
                '>
                    {profile['photo']}
                </div>
                <div style='flex: 1;'>
                    <h3 style='margin: 0 0 0.5rem 0; color: white; font-size: 1.4rem;'>
                        {profile['full_name']}
                    </h3>
                    <div style='display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem;'>
                        <span style='background: rgba(255,255,255,0.2); padding: 0.35rem 0.9rem; border-radius: 20px;'>
                            {profile['role']}
                        </span>
                        <span style='background: rgba(255,255,255,0.2); padding: 0.35rem 0.9rem; border-radius: 20px;'>
                            {profile['department']}
                        </span>
                    </div>
                    <div style='display: flex; align-items: center; gap: 1.25rem; font-size: 0.9rem;'>
                        <span>{profile['status']}</span>
                        <span>🕐 {profile['work_hours']}</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def display_chat(character_key):
    if character_key in ["alice", "maxim"]:
        display_profile(character_key)
    
    if character_key in CHARACTERS_RESPONSES:
        character = CHARACTERS_RESPONSES[character_key]
        st.subheader(f"💬 Чат с {character['name']}")
    else:
        character = GROUP_CHATS[character_key]
        st.subheader(f"💬 {character['name']}")
        st.caption(f"{character['description']} • {character['members']}")
    
    # Показываем всю историю чата
    for msg in st.session_state.chats[character_key]:
        if msg['role'] == 'user':
            st.markdown(f"<div class='chat-message user-message'><strong>Вы:</strong> {msg['content']}</div>", unsafe_allow_html=True)
        else:
            # Добавляем бейдж AI к ответам
            ai_badge = " <span class='ai-badge'>AI</span>" if msg.get('ai_generated', False) else ""
            st.markdown(f"<div class='chat-message bot-message'><strong>{character['name']}:</strong>{ai_badge} {msg['content']}</div>", unsafe_allow_html=True)
    
    # Поле ввода
    with st.form(key=f'chat_form_{character_key}', clear_on_submit=True):
        user_input = st.text_input("Ваше сообщение:", key=f"input_{character_key}")
        submitted = st.form_submit_button("Отправить")
        
        if submitted and user_input:
            # НЕМЕДЛЕННО добавляем сообщение пользователя
            st.session_state.chats[character_key].append({
                'role': 'user', 
                'content': user_input
            })
            
            # Сохраняем сообщение для обработки AI
            st.session_state[f'pending_response_{character_key}'] = user_input
            
            # Перезагружаем чтобы показать сообщение пользователя
            st.rerun()

def process_ai_response(character_key):
    """Обрабатываем AI ответ после того как сообщение пользователя уже показано"""
    if (f'pending_response_{character_key}' in st.session_state and 
        st.session_state[f'pending_response_{character_key}']):
        
        user_message = st.session_state[f'pending_response_{character_key}']
        
        # ПРОВЕРКА НА ПОВТОРНЫЕ СООБЩЕНИЯ
        chat_history = st.session_state.chats[character_key]
        if len(chat_history) >= 2:
            last_user_message = None
            # Ищем последнее сообщение пользователя
            for msg in reversed(chat_history[:-1]):  # Исключаем текущее сообщение
                if msg['role'] == 'user':
                    last_user_message = msg['content']
                    break
            
            # Если сообщение повторяется
            if last_user_message and user_message.strip().lower() == last_user_message.strip().lower():
                repeat_responses = {
                    "alice": [
                        "Переформулируй вопрос, пожалуйста. Пока не понимаю, как тебе помочь",
                        "Ошиблась?)) Можешь по-другому спросить?",
                        "Уточни, пожалуйста, что именно нужно. Так я смогу лучше помочь"
                    ],
                    "maxim": ["Повтор. Уточни задачу", "Дублируешь. Конкретизируй"],
                    "dba_team": ["Запрос дублируется. Уточни формат", "Повтор. Проверь синтаксис"],
                    "partner_a": ["Повторяющийся вопрос. Уточни детали", "Дублирующий запрос. Конкретизируй"],
                    "partner_b": ["Повторяющийся вопрос. Уточни детали", "Дублирующий запрос. Конкретизируй"]
                }
                
                response = random.choice(repeat_responses.get(character_key, ["Повтор"]))
                st.session_state.chats[character_key].append({
                    'role': 'bot',
                    'content': response,
                    'ai_generated': True
                })
                st.session_state[f'pending_response_{character_key}'] = None
                st.rerun()
                return
        
        # Получаем ответ от AI
        with st.spinner(f"🤔 {get_typing_message(character_key)}"):
            if character_key in CHARACTERS_RESPONSES:
                response = CHARACTERS_RESPONSES[character_key]['get_response'](user_message)
            else:
                response = GROUP_CHATS[character_key]['get_response'](user_message)
        
        # Добавляем ответ в историю с пометкой AI
        st.session_state.chats[character_key].append({
            'role': 'bot',
            'content': response,
            'ai_generated': True
        })
        
        st.session_state[f'pending_response_{character_key}'] = None
        st.rerun()

def get_typing_message(character_key):
    messages = {
        "alice": "Алиса печатает...",
        "maxim": "Максим просматривает задачу...", 
        "dba_team": "DBA команда проверяет запрос...",
        "partner_a": "Партнер А уточняет информацию...",
        "partner_b": "Партнер Б консультируется с отделом..."
    }
    return messages.get(character_key, "Думает...")

def sql_sandbox():
    tab1, tab2 = st.tabs(["🔧 SQL Редактор", "🗃️ Схема БД"])
    
    with tab1:
        sql_query = st.text_area("SQL запрос:", height=150, 
                               placeholder="SELECT SUM(amount - commission_amount) as выручка FROM processing_operations WHERE status = 'success'")
        
        if st.button("Выполнить запрос"):
            if sql_query:
                result, feedback = validate_sql_query(sql_query)
                if result is not None:
                    st.success("✅ Запрос выполнен успешно")
                    st.dataframe(result)
                else:
                    st.error("❌ Ошибка в запросе")
                if feedback:
                    st.info(f"💡 {feedback}")
            else:
                st.warning("Введите SQL запрос")
    
    with tab2:
        show_database_schema()

def show_database_schema():
    st.subheader("🗃️ Схема базы данных")
    selected_table = st.selectbox("Выберите таблицу:", list(DATABASE_SCHEMA.keys()))
    
    if selected_table:
        table_info = DATABASE_SCHEMA[selected_table]
        st.markdown(f"**Описание:** {table_info['description']}")
        st.markdown("---")
        st.markdown("**Структура таблицы:**")
        for col_name, col_info in table_info['columns'].items():
            col1, col2, col3, col4 = st.columns([2, 2, 1, 4])
            with col1:
                st.markdown(f"`{col_name}`")
            with col2:
                st.markdown(col_info['type'])
            with col3:
                if col_info.get('pk'):
                    st.markdown("🔑")
                elif col_info.get('fk'):
                    st.markdown("🔗")
                else:
                    st.markdown("")
            with col4:
                st.markdown(col_info['description'])

def knowledge_base():
    st.subheader("📚 База знаний")
    for article_key, article in KNOWLEDGE_BASE.items():
        with st.expander(article['title']):
            st.markdown(article['content'])

def main():
    st.sidebar.title("🔍 DataWork Lab")
    st.sidebar.markdown("**Симулятор рабочих задач аналитика данных**")
    st.sidebar.markdown("---")
    
    initialize_chat()
    
    page = st.sidebar.radio("Выберите раздел:", 
                           ["💬 Чаты с командой", "🔧 SQL Песочница", "📚 База знаний"])
    
    if page == "💬 Чаты с командой":
        chat_type = st.sidebar.radio("Выберите чат:", 
                                   ["👩‍💼 Алиса", "👨‍💼 Максим", "🛠️ #dba-team", 
                                    "🤝 #partner_a_operations_chat", "🤝 #partner_b_operations_chat"])
        
        chat_map = {
            "👩‍💼 Алиса": "alice",
            "👨‍💼 Максим": "maxim", 
            "🛠️ #dba-team": "dba_team",
            "🤝 #partner_a_operations_chat": "partner_a",
            "🤝 #partner_b_operations_chat": "partner_b"
        }
        
        selected_chat = chat_map[chat_type]
        
        # Сначала показываем чат с текущей историей
        display_chat(selected_chat)
        
        # Затем обрабатываем AI ответ если есть ожидающее сообщение
        process_ai_response(selected_chat)
        
    elif page == "🔧 SQL Песочница":
        sql_sandbox()
        
    else:
        knowledge_base()

if __name__ == "__main__":
    main()
