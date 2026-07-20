from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Fleet AI Agent API", version="0.1.0")


@app.post("/vehicles/import", response_model=List[schemas.VehicleResponse])
async def import_vehicles(vehicles: List[schemas.VehicleCreate], db: Session = Depends(get_db)):
    db_vehicles = []
    for vehicle_data in vehicles:
        db_vehicle = models.Vehicle(**vehicle_data.model_dump())
        db.add(db_vehicle)
        db_vehicles.append(db_vehicle)
    db.commit()
    for db_vehicle in db_vehicles:
        db.refresh(db_vehicle)
    return db_vehicles


@app.get("/vehicles", response_model=List[schemas.VehicleResponse])
async def list_vehicles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    vehicles = db.query(models.Vehicle).offset(skip).limit(limit).all()
    return vehicles


from datetime import datetime, timedelta

@app.get("/maintenance/upcoming", response_model=List[schemas.VehicleResponse])
async def upcoming_maintenance(db: Session = Depends(get_db)):
    # Simple mockup: return vehicles with maintenance date in the future but within 30 days
    # For MVP and string dates (YYYY-MM-DD), doing basic string comparison or python filtering
    vehicles = db.query(models.Vehicle).all()
    now = datetime.now()
    thirty_days_later = now + timedelta(days=30)
    upcoming = []
    for v in vehicles:
        if v.next_maintenance_date:
            try:
                m_date = datetime.strptime(v.next_maintenance_date, "%Y-%m-%d")
                if now <= m_date <= thirty_days_later:
                    upcoming.append(v)
            except ValueError:
                pass
    return upcoming


@app.get("/maintenance/overdue", response_model=List[schemas.VehicleResponse])
async def overdue_maintenance(db: Session = Depends(get_db)):
    vehicles = db.query(models.Vehicle).all()
    now = datetime.now()
    overdue = []
    for v in vehicles:
        if v.next_maintenance_date:
            try:
                m_date = datetime.strptime(v.next_maintenance_date, "%Y-%m-%d")
                if m_date < now:
                    overdue.append(v)
            except ValueError:
                pass
    return overdue


@app.get("/repairs/statistics")
async def repairs_statistics(db: Session = Depends(get_db)):
    # Mockup for MVP
    vehicles = db.query(models.Vehicle).all()
    total_vehicles = len(vehicles)
    return {
        "total_vehicles_tracked": total_vehicles,
        "total_repairs_this_month": 5, # Mock data
        "most_frequent_issue": "Oil change" # Mock data
    }


@app.post("/agent/ask", response_model=schemas.AgentResponse)
async def ask_agent(query: schemas.AgentQuery, db: Session = Depends(get_db)):
    # Mockup of LangChain/LLM response
    # In a real scenario, this would format data and call an LLM.
    vehicles = db.query(models.Vehicle).all()
    count = len(vehicles)
    return {"response": f"You asked: '{query.query}'. We currently have {count} vehicles in the fleet. All systems operational."}


@app.post("/reports/generate", response_model=schemas.ReportResponse)
async def generate_report(db: Session = Depends(get_db)):
    vehicles = db.query(models.Vehicle).all()

    # Very basic mockup logic for MVP
    now = datetime.now()
    thirty_days_later = now + timedelta(days=30)
    upcoming_count = 0
    overdue_count = 0

    for v in vehicles:
        if v.next_maintenance_date:
            try:
                m_date = datetime.strptime(v.next_maintenance_date, "%Y-%m-%d")
                if now <= m_date <= thirty_days_later:
                    upcoming_count += 1
                elif m_date < now:
                    overdue_count += 1
            except ValueError:
                pass

    return {
        "total_vehicles": len(vehicles),
        "upcoming_maintenance_count": upcoming_count,
        "overdue_events_count": overdue_count,
        "summary": "Report generated successfully. Please review the dashboard for detailed metrics."
    }
