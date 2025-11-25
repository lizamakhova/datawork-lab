import streamlit as st
import pandas as pd
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

# Современные стили
st.markdown("""
<style>
    .chat-message {
        padding: 1rem; 
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 2rem;
        border-left: 4px solid #2196F3;
        color: #1565C0;
    }
    .bot-message {
        background-color: #f5f5f5;
        margin-right: 2rem;
        border-left: 4px solid #4CAF50;
        color: #2E7D32;
    }
    .chat-message strong {
        color: #333333;
        font-weight: 600;
    }
    .stTextInput input {
        border: 1px solid #ccc;
        border-radius: 8px;
        padding: 8px 12px;
        background: #fafafa;
        font-size: 14px;
        transition: all 0.2s ease;
    }
    .stTextInput input:focus {
        border-color: #2196F3;
        background: white;
        box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.1);
        outline: none;
    }
    .stTextArea textarea {
        border: 1px solid #ccc !important;
        border-radius: 8px !important;
        padding: 12px !important;
        background: #fafafa !important;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
    }
    .stTextArea textarea:focus {
        border-color: #2196F3 !important;
        background: white !important;
        box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.1) !important;
        outline: none !important;
    }
    .stButton button {
        background-color: #2196F3;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    .stButton button:hover {
        background-color: #1976D2;
        color: white;
    }
    .profile-card {
        padding: 1rem;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        margin-bottom: 1rem;
        background: white;
    }
</style>
""", unsafe_allow_html=True)

def initialize_chat():
    """Инициализация истории чатов"""
    if 'chats' not in st.session_state:
        st.session_state.chats = {
            'alice': [],
            'maxim': [],
            'dba_team': [],
            'partner_a': [],
            'partner_b': []
        }

def display_profile(character_key):
    """Отображение профиля персонажа"""
    if character_key in CHARACTERS_PROFILES:
        profile = CHARACTERS_PROFILES[character_key]
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 Профиль")
            st.markdown(f"**{profile['full_name']}**")
            st.markdown(f"{profile['status']}")
            st.markdown(f"**Роль:** {profile['role']}")
            st.markdown(f"**Отдел:** {profile['department']}")
            st.markdown(f"**Часы работы:** {profile['work_hours']}")

def display_chat(character_key):
    """Отображение чата с выбранным персонажем/группой"""
    if character_key in CHARACTERS_RESPONSES:
        character = CHARACTERS_RESPONSES[character_key]
        st.subheader(f"💬 Чат с {character['name']}")
    else:
        character = GROUP_CHATS[character_key]
        st.subheader(f"💬 {character['name']}")
    
    # Показ истории сообщений
    for msg in st.session_state.chats[character_key]:
        if msg['role'] == 'user':
            st.markdown(f"<div class='chat-message user-message'><strong>Вы:</strong> {msg['content']}</div>", 
                       unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-message bot-message'><strong>{character['name']}:</strong> {msg['content']}</div>", 
                       unsafe_allow_html=True)
    
    # Поле ввода
    with st.form(key=f'chat_form_{character_key}', clear_on_submit=True):
        user_input = st.text_input("Ваше сообщение:", key=f"input_{character_key}")
        submitted = st.form_submit_button("Отправить")
        
        if submitted and user_input:
            # Добавляем сообщение пользователя
            st.session_state.chats[character_key].append({
                'role': 'user', 
                'content': user_input
            })
            
            # Получаем ответ
            if character_key in CHARACTERS_RESPONSES:
                response = CHARACTERS_RESPONSES[character_key]['get_response'](user_input)
            else:
                response = GROUP_CHATS[character_key]['get_response'](user_input)
            
            # Добавляем ответ
            st.session_state.chats[character_key].append({
                'role': 'bot',
                'content': response
            })
            
            st.rerun()

def sql_sandbox():
    """SQL песочница с вкладками"""
    tab1, tab2 = st.tabs(["🔧 SQL Редактор", "🗃️ Схема БД"])
    
    with tab1:
        st.info("""
        **Доступные таблицы:**
        - `processing_operations` - наши операции
        - `partner_a_payments` - данные партнера А
        - `partner_b_payments` - данные партнера Б  
        - `operation_additional_data` - доп данные
        - `registry_statuses` - статусы реестров
        - `commission_rates` - ставки комиссий
        """)
        
        sql_query = st.text_area("SQL запрос:", height=150, 
                               placeholder="SELECT * FROM processing_operations WHERE status = 'success'")
        
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
    """Отображение схемы БД"""
    st.subheader("🗃️ Схема базы данных")
    
    selected_table = st.selectbox("Выберите таблицу:", list(DATABASE_SCHEMA.keys()))
    
    if selected_table:
        table_info = DATABASE_SCHEMA[selected_table]
        
        st.markdown(f"**Описание:** {table_info['description']}")
        st.markdown("---")
        
        # Отображение колонок
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
    """База знаний"""
    st.subheader("📚 База знаний")
    
    for article_key, article in KNOWLEDGE_BASE.items():
        with st.expander(article['title']):
            st.markdown(article['content'])

def main():
    # Заголовок в сайдбаре
    st.sidebar.title("🔍 DataWork Lab")
    st.sidebar.markdown("**Симулятор рабочих задач аналитика данных**")
    st.sidebar.markdown("---")
    
    initialize_chat()
    
    # Навигация
    page = st.sidebar.radio("Выберите раздел:", 
                           ["💬 Чаты с командой", "🔧 SQL Песочница", "📚 База знаний"])
    
    if page == "💬 Чаты с командой":
        # Выбор чата
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
        
        # Показываем профиль для индивидуальных чатов
        if selected_chat in ["alice", "maxim"]:
            display_profile(selected_chat)
        
        display_chat(selected_chat)
        
    elif page == "🔧 SQL Песочница":
        sql_sandbox()
        
    else:
        knowledge_base()

if __name__ == "__main__":
    main()
