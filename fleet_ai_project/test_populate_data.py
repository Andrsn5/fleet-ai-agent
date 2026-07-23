import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine
from datetime import date, timedelta

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def _make_event_payload(vehicle_id, event_type, days_offset, cost=5000.0):
    event_date = (date.today() + timedelta(days=days_offset)).isoformat()
    return {
        "vehicle_id": vehicle_id,
        "event_type": event_type,
        "event_date": event_date,
        "description": f"Тестовое событие {event_type}",
        "cost": cost
    }

def test_populate_many_vehicles_and_events():
    vehicles_payload = {
        "vehicles": [
            {
                "brand": "Toyota",
                "model": "Camry",
                "vin": f"VIN{str(i).zfill(6)}",
                "license_plate": f"А{str(i).zfill(3)}АА77",
                "year": 2020 + (i % 5),
                "department": "IT",
                "responsible_person": "Иванов И.И.",
                "driver": "Петров П.П.",
                "mileage": 10000.0 + i * 1000
            }
            for i in range(20)
        ]
    }
    r = client.post("/vehicles/import", json=vehicles_payload)
    assert r.status_code == 200
    assert r.json()["imported"] == 20

    r = client.get("/vehicles")
    assert len(r.json()) == 20

    vehicle_id = r.json()[0]["id"]

    events_payload = [
        _make_event_payload(vehicle_id, "maintenance", -10),
        _make_event_payload(vehicle_id, "insurance", 15),
        _make_event_payload(vehicle_id, "inspection", 30),
        _make_event_payload(vehicle_id, "repair", -5, cost=15000.0),
    ]
    for ev in events_payload:
        r = client.post("/events", json=ev)
        assert r.status_code == 200

    r = client.get("/maintenance/upcoming")
    assert r.status_code == 200

    r = client.get("/maintenance/overdue")
    assert r.status_code == 200

    r = client.get("/repairs/statistics")
    assert r.status_code == 200
    stats = r.json()
    assert len(stats) >= 1
    assert stats[0]["repair_count"] >= 1
