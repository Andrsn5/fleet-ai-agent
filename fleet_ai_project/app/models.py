from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Vehicle(Base):
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True, index=True)
    vin = Column(String, unique=True, index=True)
    plate_number = Column(String, unique=True)
    make = Column(String)
    model = Column(String)
    year = Column(Integer)
    mileage = Column(Float)
    department = Column(String)
    responsible = Column(String)
    driver = Column(String)
    next_maintenance_date = Column(String)  # Using String for dates in SQLite/MVP for simplicity, can be Date
    insurance_expiry_date = Column(String)
    inspection_expiry_date = Column(String)
