from app.database import SessionLocal, Base, engine
from app.models import Vehicle

def seed_data():
    # Создаем таблицы, если их вдруг нет
    Base.metadata.create_all(bind=engine)
    
    with SessionLocal() as db:
        # Проверяем, есть ли уже данные
        if db.query(Vehicle).count() > 0:
            print("База уже наполнена данными.")
            return
        
        vehicles = [
            Vehicle(brand="Toyota", model="Camry", vin="VIN001", license_plate="А111АА77", year=2021, department="IT", responsible_person="Иванов И.И.", driver="Петров П.", mileage=45000),
            Vehicle(brand="Ford", model="Transit", vin="VIN002", license_plate="В222ВВ77", year=2019, department="Логистика", responsible_person="Смирнов А.", driver="Сидоров В.", mileage=120000)
        ]
        
        db.add_all(vehicles)
        db.commit()
        print("Успешно добавлено 2 автомобиля в базу данных fleet.db!")

if __name__ == "__main__":
    seed_data()
