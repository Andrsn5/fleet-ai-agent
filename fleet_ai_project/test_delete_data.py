import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def test_delete_all_vehicles():
    vehicles_payload = {
        "vehicles": [
            {
                "brand": "Toyota",
                "model": "Camry",
                "vin": f"DELVIN{str(i).zfill(6)}",
                "license_plate": f"D{str(i).zfill(3)}DD77",
                "year": 2020,
                "department": "IT",
                "responsible_person": "Иванов И.И.",
                "driver": "Петров П.П.",
                "mileage": 10000.0
            }
            for i in range(10)
        ]
    }
    r = client.post("/vehicles/import", json=vehicles_payload)
    assert r.status_code == 200
    assert r.json()["imported"] == 10

    r = client.get("/vehicles")
    vehicles = r.json()
    assert len(vehicles) == 10

    for v in vehicles:
        r = client.delete(f"/vehicles/{v['id']}")
        assert r.status_code == 200

    r = client.get("/vehicles")
    assert r.json() == []
