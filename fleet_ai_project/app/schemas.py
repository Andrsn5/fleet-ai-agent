from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import date

class EventBase(BaseModel):
    event_type: str
    event_date: date
    description: Optional[str] = None
    cost: float = 0.0

class EventCreate(EventBase):
    vehicle_id: int

class EventResponse(EventBase):
    id: int
    vehicle_id: int
    model_config = ConfigDict(from_attributes=True)

class VehicleBase(BaseModel):
    brand: str
    model: str
    vin: str
    license_plate: str
    year: int
    department: str
    responsible_person: str
    driver: str
    mileage: float = 0.0

class VehicleCreate(VehicleBase):
    pass

class VehicleResponse(VehicleBase):
    id: int
    events: List[EventResponse] = []
    model_config = ConfigDict(from_attributes=True)

class ImportRequest(BaseModel):
    vehicles: List[VehicleCreate]

class EventWithVehicleResponse(EventResponse):
    vehicle_brand: str
    vehicle_model: str
    license_plate: str
    
    model_config = ConfigDict(from_attributes=True)

class RepairStatisticResponse(BaseModel):
    vehicle_id: int
    brand: str
    model: str
    license_plate: str
    total_repair_cost: float
    repair_count: int

class AgentRequest(BaseModel):
    query: str
    session_id: str = "default_session"

class AgentResponse(BaseModel):
    answer: str

class ReportResponse(BaseModel):
    report: str
