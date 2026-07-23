from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from .database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String, index=True)
    model = Column(String, index=True)
    vin = Column(String, unique=True, index=True)
    license_plate = Column(String, unique=True, index=True)
    year = Column(Integer)
    department = Column(String)
    responsible_person = Column(String)
    driver = Column(String)
    mileage = Column(Float, default=0.0)
    
    events = relationship("Event", back_populates="vehicle", cascade="all, delete-orphan")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    event_type = Column(String, index=True) # Например: "insurance", "maintenance", "inspection", "repair"
    event_date = Column(Date)
    description = Column(Text, nullable=True)
    cost = Column(Float, default=0.0)

    vehicle = relationship("Vehicle", back_populates="events")
