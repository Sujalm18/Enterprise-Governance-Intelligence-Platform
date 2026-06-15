import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import User
from backend.app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_role,
    get_current_tenant
)

@pytest.fixture(name="db_setup")
def fixture_db_setup():
    """Sets up a temporary SQLite database on disk for test execution."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    db_url = f"sqlite:///{db_path}"
    
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    
    SessionTest = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield SessionTest, db_path
    
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

@pytest.fixture(name="db_session")
def fixture_db_session(db_setup):
    SessionTest, _ = db_setup
    db = SessionTest()
    yield db
    db.close()

@pytest.fixture(name="client")
def fixture_client(db_setup, db_session):
    """Sets up a TestClient with overridden get_db dependency."""
    SessionTest, _ = db_setup
    
    def override_get_db():
        session = SessionTest()
        try:
            yield session
        finally:
            session.close()
            
    app.dependency_overrides[get_db] = override_get_db
    tc = TestClient(app)
    yield tc
    app.dependency_overrides.clear()


def test_password_hashing():
    password = "supersecretpassword123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_jwt_generation_and_decoding():
    data = {"sub": "testuser"}
    token = create_access_token(data)
    assert isinstance(token, str)


def test_login_endpoint(client, db_session):
    # Seed a user
    hashed_pwd = get_password_hash("password123")
    user = User(username="test_login_user", role="analyst", password_hash=hashed_pwd, tenant_id=1)
    db_session.add(user)
    db_session.commit()

    # Attempt login with correct credentials
    response = client.post("/api/auth/login", json={"username": "test_login_user", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "analyst"
    assert data["tenant_id"] == 1

    # Attempt login with incorrect password
    response_wrong_pw = client.post("/api/auth/login", json={"username": "test_login_user", "password": "wrongpassword"})
    assert response_wrong_pw.status_code == 401


def test_me_endpoint(client, db_session):
    # Seed a user
    hashed_pwd = get_password_hash("password123")
    user = User(username="profile_user", role="reviewer", password_hash=hashed_pwd, tenant_id=2)
    db_session.add(user)
    db_session.commit()

    # Access without auth token
    response_unauth = client.get("/api/auth/me")
    assert response_unauth.status_code == 401

    # Login and get token
    response_login = client.post("/api/auth/login", json={"username": "profile_user", "password": "password123"})
    token = response_login.json()["access_token"]

    # Access with auth token
    response_auth = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response_auth.status_code == 200
    data = response_auth.json()
    assert data["username"] == "profile_user"
    assert data["role"] == "reviewer"
    assert data["tenant_id"] == 2


def test_role_and_tenant_fallback():
    # Test fallback to headers when user is not authenticated
    assert get_current_role("Manager", None) == "Manager"
    assert get_current_tenant("3", None) == 3

    # Test fallback to default when headers are missing
    assert get_current_role(None, None) == "Analyst"
    assert get_current_tenant(None, None) == 1
