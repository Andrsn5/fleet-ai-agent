import os
from datetime import date, timedelta
from langchain_core.tools import tool
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from .database import SessionLocal
from . import models

# Clear any problematic proxy environment variables
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'SOCKS_PROXY', 'http_proxy', 'https_proxy', 'socks_proxy']:
    if key in os.environ:
        del os.environ[key]

@tool
def get_upcoming_events_tool(days: int = 30) -> str:
    """Возвращает список ближайших мероприятий (ТО, страховка, техосмотр) для автопарка на заданное число дней."""
    with SessionLocal() as db:
        today = date.today()
        future_date = today + timedelta(days=days)
        events = db.query(models.Event, models.Vehicle).join(models.Vehicle).filter(
            models.Event.event_date >= today,
            models.Event.event_date <= future_date,
            models.Event.event_type.in_(["maintenance", "insurance", "inspection"])
        ).all()
        
        if not events:
            return "Нет предстоящих мероприятий в ближайшие дни."
        
        result = []
        for e, v in events:
            result.append(f"Авто: {v.brand} {v.model} ({v.license_plate}), Событие: {e.event_type}, Дата: {e.event_date}")
        return "\n".join(result)

@tool
def get_overdue_events_tool() -> str:
    """Возвращает список просроченных мероприятий (ТО, страховка) для автопарка. Это критические риски!"""
    with SessionLocal() as db:
        today = date.today()
        events = db.query(models.Event, models.Vehicle).join(models.Vehicle).filter(
            models.Event.event_date < today,
            models.Event.event_type.in_(["maintenance", "insurance", "inspection"])
        ).all()
        
        if not events:
            return "Отлично, просроченных мероприятий нет."
        
        result = []
        for e, v in events:
            result.append(f"ВНИМАНИЕ! Авто: {v.brand} {v.model} ({v.license_plate}), Просрочено: {e.event_type}, Дата: {e.event_date}")
        return "\n".join(result)

tools = [get_upcoming_events_tool, get_overdue_events_tool]

# Set environment variable for gigachat credentials to avoid proxy issues
os.environ["GIGACHAT_CREDENTIALS"] = "твой_ключ_здесь"

store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

def initialize_agent():
    try:
        from langchain_gigachat.chat_models import GigaChat
        try:
            from langchain.agents import AgentExecutor, create_tool_calling_agent
        except ImportError:
            from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
        from langchain_core.prompts import ChatPromptTemplate
        
        # Set credentials before creating the LLM
        credentials = os.getenv("GIGACHAT_CREDENTIALS", "твой_ключ_здесь")
        
        llm = GigaChat(
            credentials=credentials,
            verify_ssl_certs=False,
            scope="GIGACHAT_API_PERS"
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Ты — профессиональный AI-агент для контроля технического состояния автопарка. "
                       "Твоя задача: анализировать сроки, выявлять риски простоя и давать краткие рекомендации. "
                       "Всегда используй доступные инструменты для получения актуальных данных из базы. "
                       "Опирайся на историю диалога, если пользователь задает уточняющие вопросы."),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
        
        agent_with_history = RunnableWithMessageHistory(
            agent_executor,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
        
        def ask_agent(query: str, session_id: str = "default_session") -> str:
            """Функция для чата с агентом с учетом сессии"""
            try:
                response = agent_with_history.invoke(
                    {"input": query},
                    config={"configurable": {"session_id": session_id}}
                )
                return response["output"]
            except Exception as e:
                print(f"Error in ask_agent: {e}")
                return f"Error processing query: {str(e)}"
        
        def generate_manager_report() -> str:
            """Функция для генерации отчета (использует отдельную сессию)"""
            query = (
                "Сформируй подробный управленческий отчет по автопарку в формате Markdown. "
                "1. Проверь просроченные мероприятия. "
                "2. Проверь ближайшие мероприятия на 30 дней. "
                "3. Сделай краткие управленческие выводы."
            )
            return ask_agent(query, session_id="report_generator_session")
        
        return ask_agent, generate_manager_report, True
        
    except Exception as e:
        print(f"Предупреждение: не удалось инициализировать AI-агента: {e}")
        
        def ask_agent(query: str, session_id: str = "default_session") -> str:
            return "AI-агент временно недоступен. Проверьте настройки GIGACHAT_CREDENTIALS и версии библиотек."
        
        def generate_manager_report() -> str:
            return "AI-агент временно недоступен. Проверьте настройки GIGACHAT_CREDENTIALS и версии библиотек."
        
        return ask_agent, generate_manager_report, False

# Initialize agent functions
ask_agent, generate_manager_report, agent_initialized = initialize_agent()
