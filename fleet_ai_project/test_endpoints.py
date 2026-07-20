import subprocess
import time
import httpx
import sys

def run_tests():
    # Start the server in the background
    server_process = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3) # Wait for server to start

    base_url = "http://127.0.0.1:8000"
    client = httpx.Client(base_url=base_url)

    try:
        print("Testing /vehicles/import...")
        import_payload = [
            {
                "vin": "VIN" + str(int(time.time())),
                "plate_number": "A" + str(int(time.time()))[-4:] + "AA77",
                "make": "Toyota",
                "model": "Camry",
                "year": 2020,
                "mileage": 50000,
                "department": "Sales",
                "responsible": "Ivan Ivanov",
                "driver": "Petr Petrov",
                "next_maintenance_date": "2024-12-01"
            }
        ]
        r = client.post("/vehicles/import", json=import_payload)
        if r.status_code != 200:
            print("Import failed with status:", r.status_code, r.text)
        assert r.status_code == 200
        print("Import OK")

        print("Testing /vehicles...")
        r = client.get("/vehicles")
        assert r.status_code == 200
        assert len(r.json()) > 0
        print("Vehicles list OK")

        print("Testing /maintenance/upcoming...")
        r = client.get("/maintenance/upcoming")
        assert r.status_code == 200
        print("Upcoming OK")

        print("Testing /maintenance/overdue...")
        r = client.get("/maintenance/overdue")
        assert r.status_code == 200
        print("Overdue OK")

        print("Testing /repairs/statistics...")
        r = client.get("/repairs/statistics")
        assert r.status_code == 200
        print("Repairs Stats OK")

        print("Testing /agent/ask...")
        r = client.post("/agent/ask", json={"session_id": "test_session_1", "query": "How many cars do we have?"})
        assert r.status_code == 200
        assert "response" in r.json()
        print("Agent Ask OK")

        print("Testing / (UI)...")
        r = client.get("/")
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")
        print("UI Endpoint OK")

        print("Testing /reports/generate...")
        r = client.post("/reports/generate")
        assert r.status_code == 200
        assert "summary" in r.json()
        print("Reports Generate OK")

        print("All tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
    finally:
        server_process.terminate()
        client.close()

if __name__ == "__main__":
    run_tests()
