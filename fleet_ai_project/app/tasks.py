import os
from datetime import date, timedelta
from celery import Celery
from celery.schedules import crontab

from .database import SessionLocal
from . import models

celery_app = Celery(
    "fleet_tasks",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
)

celery_app.conf.timezone = 'UTC'

@celery_app.task
def check_upcoming_events_and_notify():
    with SessionLocal() as db:
        today = date.today()
        notify_days = [30, 14, 7, 1]
        
        for days in notify_days:
            target_date = today + timedelta(days=days)
            events = db.query(models.Event, models.Vehicle).join(models.Vehicle).filter(
                models.Event.event_date == target_date,
                models.Event.event_type.in_(["maintenance", "insurance", "inspection"])
            ).all()
            
            for event, vehicle in events:
                message = (f"Напоминание: через {days} дней ({event.event_date}) наступит срок "
                           f"события '{event.event_type}' для автомобиля {vehicle.brand} {vehicle.model} "
                           f"({vehicle.license_plate}).")
                send_notification(vehicle.responsible_person, message)
        
        overdue_events = db.query(models.Event, models.Vehicle).join(models.Vehicle).filter(
            models.Event.event_date < today,
            models.Event.event_type.in_(["maintenance", "insurance", "inspection"])
        ).all()
        
        for event, vehicle in overdue_events:
            message = (f"ВНИМАНИЕ! Просрочено событие '{event.event_type}' для автомобиля "
                       f"{vehicle.brand} {vehicle.model} ({vehicle.license_plate}). "
                       f"Плановая дата была: {event.event_date}.")
            send_notification(vehicle.responsible_person, message, level="CRITICAL")

def send_notification(recipient: str, message: str, level: str = "INFO"):
    prefix = "🔴 АЛЕРТ" if level == "CRITICAL" else "🔵 ИНФО"
    print(f"{prefix} | Кому: {recipient} | Сообщение: {message}")

celery_app.conf.beat_schedule = {
    'daily-fleet-check': {
        'task': 'app.tasks.check_upcoming_events_and_notify',
        'schedule': crontab(hour=8, minute=0),
    },
}
