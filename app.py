import streamlit as st
import pandas as pd
from database import DEMO_DATABASE
from characters import CHARACTERS_RESPONSES
from sql_validator import validate_sql_query

# Настройка страницы
st.set_page_config(
    page_title="DataWork Lab",
    page_icon="🔍",
    layout="wide"
)

# Стиль для чата
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
        border: 2px solid #2196F3;
        border-radius: 8px;
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
</style>
""", unsafe_allow_html=True)

def initialize_chat():
    """Инициализация истории чатов"""
    if 'chats' not in st.session_state:
        st.session_state.chats = {
            'alice': [],
            'maxim': [],
            'dba': [],
            'partner_a': [],
            'partner_b': []
        }

def display_chat(character):
    """Отображение чата с выбранным персонажем"""
    st.subheader(f"💬 Чат с {CHARACTERS_RESPONSES[character]['name']}")
    
    # Показ истории сообщений
    for msg in st.session_state.chats[character]:
        if msg['role'] == 'user':
            st.markdown(f"<div class='chat-message user-message'><strong>Вы:</strong> {msg['content']}</div>", 
                       unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-message bot-message'><strong>{CHARACTERS_RESPONSES[character]['name']}:</strong> {msg['content']}</div>", 
                       unsafe_allow_html=True)
    
    # Поле ввода
    with st.form(key=f'chat_form_{character}', clear_on_submit=True):
        user_input = st.text_input("Ваше сообщение:", key=f"input_{character}")
        submitted = st.form_submit_button("Отправить")
        
        if submitted and user_input:
            # Добавляем сообщение пользователя
            st.session_state.chats[character].append({
                'role': 'user', 
                'content': user_input
            })
            
            # Получаем ответ от персонажа
            response = CHARACTERS_RESPONSES[character]['get_response'](user_input)
            
            # Добавляем ответ бота
            st.session_state.chats[character].append({
                'role': 'bot',
                'content': response
            })
            
            st.rerun()

def sql_sandbox():
    """SQL песочница"""
    st.subheader("🔧 SQL Песочница")
    
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

def main():
    st.title("🔍 DataWork Lab")
    st.markdown("**Симулятор рабочих задач аналитика данных**")
    
    initialize_chat()
    
    # Сайдбар с навигацией
    st.sidebar.title("Навигация")
    page = st.sidebar.radio("Выберите раздел:", 
                           ["💬 Чаты с командой", "🔧 SQL Песочница"])
    
    if page == "💬 Чаты с командой":
        # Выбор персонажа для чата
        character = st.sidebar.radio("Выберите собеседника:", 
                                   ["Алиса", "Максим", "DBA команда", "Партнер А", "Партнер Б"])
        
        character_map = {
            "Алиса": "alice",
            "Максим": "maxim", 
            "DBA команда": "dba",
            "Партнер А": "partner_a",
            "Партнер Б": "partner_b"
        }
        
        display_chat(character_map[character])
        
    else:
        sql_sandbox()
    
    # Информация о данных в сайдбаре
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **Тестовые данные:**
    - 100+ операций
    - 2 партнера
    - 3 реестра
    - Реалистичные расхождения
    """)

if __name__ == "__main__":
    main()
