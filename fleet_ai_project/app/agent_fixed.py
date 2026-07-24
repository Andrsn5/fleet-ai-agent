import os
import traceback
from datetime import date, timedelta
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_gigachat.chat_models import GigaChat
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv


from .database import SessionLocal
from . import models

# АГРЕССИВНОЕ ОТКЛЮЧЕНИЕ ПРОКСИ ДЛЯ HTTPX (ЧТОБЫ ИГНОРИРОВАТЬ SOCKS4 Windows)
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'SOCKS_PROXY', 'ALL_PROXY', 
            'http_proxy', 'https_proxy', 'socks_proxy', 'all_proxy']:
    if key in os.environ:
        del os.environ[key]

@tool
def get_upcoming_events_tool(days: int = 30) -> str:
    """Возвращает список ближайших мероприятий (ТО, страховка, техосмотр) для автопарка."""
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
        
        result = [f"Авто: {v.brand} {v.model} ({v.license_plate}), Событие: {e.event_type}, Дата: {e.event_date}" for e, v in events]
        return "\n".join(result)

@tool
def get_overdue_events_tool() -> str:
    """Возвращает список просроченных мероприятий (ТО, страховка)."""
    with SessionLocal() as db:
        today = date.today()
        events = db.query(models.Event, models.Vehicle).join(models.Vehicle).filter(
            models.Event.event_date < today,
            models.Event.event_type.in_(["maintenance", "insurance", "inspection"])
        ).all()
        
        if not events:
            return "Просроченных мероприятий нет."
        
        result = [f"ВНИМАНИЕ! Авто: {v.brand} {v.model} ({v.license_plate}), Просрочено: {e.event_type}, Дата: {e.event_date}" for e, v in events]
        return "\n".join(result)

load_dotenv() 

# Инициализация LLM
llm = GigaChat(
    credentials=os.getenv("GIGACHAT_CREDENTIALS"), 
    verify_ssl_certs=False,
    scope="GIGACHAT_API_PERS"
)


tools = [get_upcoming_events_tool, get_overdue_events_tool]
memory = MemorySaver()

system_message = (
    "Ты — профессиональный AI-агент для контроля технического состояния автопарка. "
    "Анализируй сроки, выявляй риски простоя и давай краткие рекомендации. "
    "Всегда используй инструменты для проверки данных в БД."
)

# Создаем агента (предупреждения langgraph игнорируем)
agent_executor = create_react_agent(
    llm, 
    tools, 
    checkpointer=memory
)

def ask_agent(query: str, session_id: str = "default_session") -> str:
    """Функция для чата с агентом с учетом сессии"""
    try:
        config = {"configurable": {"thread_id": session_id}}
        
        # Проверяем, есть ли уже сохраненная история для этой сессии
        state = agent_executor.get_state(config)
        
        if not state.values.get("messages"):
            # Если история пустая (первое сообщение в чате), задаем роль
            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=query)
            ]
        else:
            # Если история уже есть, отправляем ТОЛЬКО новый запрос пользователя
            messages = [
                HumanMessage(content=query)
            ]
        
        # Вызываем агента
        response = agent_executor.invoke(
            {"messages": messages}, 
            config=config
        )
        
        return response["messages"][-1].content
    except Exception as e:
        # Полный вывод ошибки в терминал Uvicorn
        print("\n" + "="*40)
        print("=== ОШИБКА ПРИ ВЫЗОВЕ AI-АГЕНТА ===")
        import traceback
        traceback.print_exc()
        print("="*40 + "\n")
        raise e

def generate_manager_report() -> str:
    query = (
        "Сформируй подробный управленческий отчет по автопарку в формате Markdown. "
        "1. Проверь просроченные мероприятия. "
        "2. Проверь ближайшие мероприятия на 30 дней. "
        "3. Сделай краткие управленческие выводы."
    )
    return ask_agent(query, session_id="report_generator_session")
