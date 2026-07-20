from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os

from . import models, schemas
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Fleet AI Agent API", version="0.1.0")

@app.get("/", include_in_schema=False)
async def serve_ui():
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    return FileResponse(index_path)


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
    vehicles = db.query(models.Vehicle).all()
    total_vehicles = len(vehicles)
    return {
        "total_vehicles_tracked": total_vehicles,
        "total_repairs_this_month": 5, 
        "most_frequent_issue": "Oil change" 
    }


agent_sessions = {}

@app.post("/agent/ask", response_model=schemas.AgentResponse)
async def ask_agent(query: schemas.AgentQuery, db: Session = Depends(get_db)):
    session_id = query.session_id
    if session_id not in agent_sessions:
        agent_sessions[session_id] = []

    agent_sessions[session_id].append({"role": "user", "content": query.query})

    vehicles = db.query(models.Vehicle).all()
    count = len(vehicles)
    history_length = len(agent_sessions[session_id])
    response_text = f"You asked: '{query.query}'. We have {count} vehicles. (Session: {session_id}, Messages in history: {history_length})"

    agent_sessions[session_id].append({"role": "agent", "content": response_text})

    return {"response": response_text}


@app.post("/reports/generate", response_model=schemas.ReportResponse)
async def generate_report(db: Session = Depends(get_db)):
    vehicles = db.query(models.Vehicle).all()

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
