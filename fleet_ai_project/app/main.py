from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from datetime import date, timedelta
from typing import List

from . import models, schemas
from .database import get_db
from .agent_fixed import ask_agent, generate_manager_report

app = FastAPI(
    title="Fleet AI Agent API",
    description="API для контроля технического состояния и обслуживания автопарка",
    version="1.0.0"
)

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=500,
        content={"detail": "Ошибка базы данных. Убедитесь, что миграции применены (alembic upgrade head)."}
    )

@app.post("/vehicles/import", response_model=dict)
def import_vehicles(payload: schemas.ImportRequest, db: Session = Depends(get_db)):
    """
    Массовая загрузка автомобилей в систему.
    """
    imported_count = 0
    for v_data in payload.vehicles:
        # Проверяем, существует ли уже авто с таким VIN
        existing = db.query(models.Vehicle).filter(models.Vehicle.vin == v_data.vin).first()
        if not existing:
            new_vehicle = models.Vehicle(**v_data.model_dump())
            db.add(new_vehicle)
            imported_count += 1
    
    db.commit()
    return {"status": "success", "imported": imported_count}

@app.get("/vehicles", response_model=List[schemas.VehicleResponse])
def get_vehicles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Получение списка автомобилей с пагинацией.
    """
    vehicles = db.query(models.Vehicle).offset(skip).limit(limit).all()
    return vehicles


@app.get("/maintenance/upcoming", response_model=List[schemas.EventWithVehicleResponse])
def get_upcoming_maintenance(days_ahead: int = 30, db: Session = Depends(get_db)):
    """
    Получение списка ближайших мероприятий (ТО, страховка, техосмотр) на заданное число дней вперед.
    """
    today = date.today()
    future_date = today + timedelta(days=days_ahead)
    
    events = db.query(
        models.Event.id,
        models.Event.vehicle_id,
        models.Event.event_type,
        models.Event.event_date,
        models.Event.description,
        models.Event.cost,
        models.Vehicle.brand.label("vehicle_brand"),
        models.Vehicle.model.label("vehicle_model"),
        models.Vehicle.license_plate
    ).join(models.Vehicle).filter(
        models.Event.event_date >= today,
        models.Event.event_date <= future_date,
        models.Event.event_type.in_(["maintenance", "insurance", "inspection"])
    ).all()
    
    return events


@app.get("/maintenance/overdue", response_model=List[schemas.EventWithVehicleResponse])
def get_overdue_maintenance(db: Session = Depends(get_db)):
    """
    Получение списка просроченных мероприятий.
    """
    today = date.today()
    
    events = db.query(
        models.Event.id,
        models.Event.vehicle_id,
        models.Event.event_type,
        models.Event.event_date,
        models.Event.description,
        models.Event.cost,
        models.Vehicle.brand.label("vehicle_brand"),
        models.Vehicle.model.label("vehicle_model"),
        models.Vehicle.license_plate
    ).join(models.Vehicle).filter(
        models.Event.event_date < today,
        models.Event.event_type.in_(["maintenance", "insurance", "inspection"])
    ).all()
    
    return events


@app.get("/repairs/statistics", response_model=List[schemas.RepairStatisticResponse])
def get_repair_statistics(db: Session = Depends(get_db)):
    """
    Статистика ремонтов: группировка затрат и количества ремонтов по каждому автомобилю.
    """
    stats = db.query(
        models.Vehicle.id.label("vehicle_id"),
        models.Vehicle.brand,
        models.Vehicle.model,
        models.Vehicle.license_plate,
        func.sum(models.Event.cost).label("total_repair_cost"),
        func.count(models.Event.id).label("repair_count")
    ).join(models.Event).filter(
        models.Event.event_type == "repair"
    ).group_by(models.Vehicle.id).all()
    
    result = []
    for stat in stats:
        result.append({
            "vehicle_id": stat.vehicle_id,
            "brand": stat.brand,
            "model": stat.model,
            "license_plate": stat.license_plate,
            "total_repair_cost": stat.total_repair_cost or 0.0,
            "repair_count": stat.repair_count
        })
    return result


@app.post("/agent/ask", response_model=schemas.AgentResponse)
def chat_with_ai_agent(payload: schemas.AgentRequest):
    try:
        answer = ask_agent(payload.query, payload.session_id)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка работы AI: {str(e)}")

@app.post("/reports/generate", response_model=schemas.ReportResponse)
def generate_report():
    """
    Создание комплексного отчета для руководителя с помощью AI.
    """
    try:
        report_text = generate_manager_report()
        return {"report": report_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации отчета: {str(e)}")

@app.post("/events", response_model=schemas.EventResponse, tags=["Events"])
def create_event(payload: schemas.EventCreate, db: Session = Depends(get_db)):
    """
    Создание события (ТО, страховка, техосмотр, ремонт) для автомобиля.
    """
    event = models.Event(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@app.delete("/vehicles/{vehicle_id}", response_model=dict, tags=["Vehicles"])
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    """
    Удаление автомобиля по ID. Каскадно удалятся все связанные события (за счет настроек в models.py).
    """
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail=f"Автомобиль с ID {vehicle_id} не найден")
    
    db.delete(vehicle)
    db.commit()
    return {"status": "success", "message": f"Автомобиль с ID {vehicle_id} успешно удален"}

@app.get("/", response_class=FileResponse, tags=["UI"])
def read_root():
    """
    Отдает главную страницу дашборда (MVP интерфейс).
    """
    return "app/index.html"
