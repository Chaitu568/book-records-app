
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Testing Authentication

def test_login():
    response = client.post("/login", json={"username": "testuser", "password": "testpassword"})
    assert response.status_code == 200
    assert "access_token" in response.json()

#  Testing CRUD Operations
def test_create_book():
    token = client.post("/login", json={"username": "testuser", "password": "testpassword"}).json()["access_token"]
    response = client.post(
        "/books",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test Book",
            "author": "John Doe",
            "published_date": "2023-01-01",
            "summary": "This is a test book.",
            "genre": "Fiction"
        }
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Test Book"

def test_read_books():
    token = client.post("/login", json={"username": "testuser", "password": "testpassword"}).json()["access_token"]
    response = client.get("/books", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# Testing Error Handling
def test_book_not_found():
    token = client.post("/login", json={"username": "testuser", "password": "testpassword"}).json()["access_token"]
    response = client.get("/books/9999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"

# Testing Real-Time Updates
def test_real_time_updates():
    with client.stream("GET", "/stream-updates") as response:
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"


