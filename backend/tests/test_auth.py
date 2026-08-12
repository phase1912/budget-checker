import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base, get_db
from backend.app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth_unit.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_user_registration_and_login_flow():
    # 1. Register new user
    reg_payload = {
        "email": "john.doe@example.com",
        "password": "SecurePassword123!",
        "first_name": "John",
        "last_name": "Doe",
    }
    response = client.post("/api/v1/auth/register", json=reg_payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "john.doe@example.com"
    assert data["user"]["role"] == "user"

    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    # 2. Get current user profile (/me)
    headers = {"Authorization": f"Bearer {access_token}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "john.doe@example.com"
    assert me_data["first_name"] == "John"

    # 3. Login with credentials
    login_payload = {
        "email": "john.doe@example.com",
        "password": "SecurePassword123!",
    }
    login_resp = client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

    # 4. Refresh token rotation
    refresh_resp = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_resp.status_code == 200
    new_data = refresh_resp.json()
    assert "access_token" in new_data
    assert "refresh_token" in new_data

    # 5. Logout
    logout_resp = client.post(
        "/api/v1/auth/logout", json={"refresh_token": new_data["refresh_token"]}
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["message"] == "Logged out successfully"


def test_invalid_login_credentials():
    login_payload = {
        "email": "nonexistent@example.com",
        "password": "WrongPassword",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
