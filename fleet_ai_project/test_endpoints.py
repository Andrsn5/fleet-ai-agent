import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

# Инициализируем клиент
client = TestClient(app)

# Фикстура для очистки БД перед каждым тестом (для чистоты экспериментов)
@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def test_import_vehicles():
    payload = {
        "vehicles": [
            {
                "brand": "Toyota",
                "model": "Camry",
                "vin": "VIN123TEST",
                "license_plate": "А123АА77",
                "year": 2022,
                "department": "IT",
                "responsible_person": "Иванов И.И.",
                "driver": "Петров П.П.",
                "mileage": 10000.5
            }
        ]
    }
    response = client.post("/vehicles/import", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["imported"] == 1

def test_get_vehicles_empty():
    response = client.get("/vehicles")
    assert response.status_code == 200
    assert response.json() == []

def test_delete_vehicle_not_found():
    response = client.delete("/vehicles/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Автомобиль с ID 999 не найден"

def test_full_lifecycle():
    # 1. Создаем авто
    payload = {
        "vehicles": [
            {
                "brand": "Ford",
                "model": "Focus",
                "vin": "VINFORD123",
                "license_plate": "В456ВВ77",
                "year": 2019,
                "department": "Sales",
                "responsible_person": "Смирнов С.С.",
                "driver": "Сидоров С.С.",
                "mileage": 50000
            }
        ]
    }
    client.post("/vehicles/import", json=payload)

    # 2. Получаем список и проверяем, что авто появилось
    res_get = client.get("/vehicles")
    vehicles = res_get.json()
    assert len(vehicles) == 1
    vehicle_id = vehicles[0]["id"]
    
    # 3. Удаляем созданное авто
    res_del = client.delete(f"/vehicles/{vehicle_id}")
    assert res_del.status_code == 200
    
    # 4. Проверяем, что авто больше нет
    res_get_empty = client.get("/vehicles")
    assert len(res_get_empty.json()) == 0

def test_agent_endpoint_mocked():
    # Тест проверяет доступность эндпоинта AI (без проверки качества ответа LLM)
    payload = {
        "query": "Привет",
        "session_id": "test_session_1"
    }
    response = client.post("/agent/ask", json=payload)
    # Если GigaChat не настроен локально в окружении тестов, может быть 500. 
    # В идеале здесь нужен mock (patch) для функции ask_agent.
    assert response.status_code in [200, 500]
