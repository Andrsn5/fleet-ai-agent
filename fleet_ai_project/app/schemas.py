from pydantic import BaseModel
from typing import Optional, List

class VehicleBase(BaseModel):
    vin: str
    plate_number: str
    make: str
    model: str
    year: int
    mileage: float
    department: str
    responsible: str
    driver: str
    next_maintenance_date: Optional[str] = None
    insurance_expiry_date: Optional[str] = None
    inspection_expiry_date: Optional[str] = None

class VehicleCreate(VehicleBase):
    pass

class VehicleResponse(VehicleBase):
    id: int

    class Config:
        from_attributes = True

class AgentQuery(BaseModel):
    session_id: str
    query: str

class AgentResponse(BaseModel):
    response: str

class ReportResponse(BaseModel):
    total_vehicles: int
    upcoming_maintenance_count: int
    overdue_events_count: int
    summary: str
