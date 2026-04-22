# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from models import Base, get_db, User, Batch, BatchTrainer, Session as DBSession, Attendance, UserRole, AttendanceStatus
from datetime import datetime, timedelta
from auth.password import hash_password

# Test database
TEST_DATABASE_URL = "postgresql://user:password@localhost:5432/attendance_test_db"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_institution(setup_test_db):
    db = TestingSessionLocal()
    user = User(
        name="Test Institution",
        email="institution@test.com",
        hashed_password=hash_password("test123"),
        role=UserRole.institution
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

@pytest.fixture
def test_trainer(test_institution):
    db = TestingSessionLocal()
    user = User(
        name="Test Trainer",
        email="trainer@test.com",
        hashed_password=hash_password("test123"),
        role=UserRole.trainer,
        institution_id=test_institution.id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

@pytest.fixture
def test_student():
    db = TestingSessionLocal()
    user = User(
        name="Test Student",
        email="student@test.com",
        hashed_password=hash_password("test123"),
        role=UserRole.student
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

@pytest.fixture
def test_batch(test_institution):
    db = TestingSessionLocal()
    batch = Batch(
        name="Test Batch",
        institution_id=test_institution.id
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    db.close()
    return batch

@pytest.fixture
def test_batch_student(test_batch, test_student):
    db = TestingSessionLocal()
    enrollment = BatchStudent(
        batch_id=test_batch.id,
        student_id=test_student.id
    )
    db.add(enrollment)
    db.commit()
    db.close()

@pytest.fixture
def test_batch_trainer(test_batch, test_trainer):
    db = TestingSessionLocal()
    trainer_rel = BatchTrainer(
        batch_id=test_batch.id,
        trainer_id=test_trainer.id
    )
    db.add(trainer_rel)
    db.commit()
    db.close()

@pytest.fixture
def test_session(test_batch, test_trainer):
    db = TestingSessionLocal()
    session = DBSession(
        batch_id=test_batch.id,
        trainer_id=test_trainer.id,
        title="Test Session",
        date=datetime.utcnow(),
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(hours=1)
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    db.close()
    return session

def test_student_signup_login(client):
    # Signup
    signup_response = client.post("/auth/signup", json={
        "name": "Test Student 2",
        "email": "student2@test.com",
        "password": "test123",
        "role": "student"
    })
    assert signup_response.status_code == 200
    token_data = signup_response.json()
    assert "access_token" in token_data
    
    # Login
    login_response = client.post("/auth/login", json={
        "email": "student2@test.com",
        "password": "test123"
    })
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    
    # Decode token to verify contents (basic check)
    assert len(token_data["access_token"]) > 0

def test_trainer_creates_session(client, test_trainer, test_batch, test_batch_trainer):
    # Login as trainer
    login_response = client.post("/auth/login", json={
        "email": "trainer@test.com",
        "password": "test123"
    })
    token = login_response.json()["access_token"]
    
    # Create session
    response = client.post("/sessions", 
        json={
            "batch_id": test_batch.id,
            "title": "New Test Session",
            "date": datetime.utcnow().isoformat(),
            "start_time": datetime.utcnow().isoformat(),
            "end_time": (datetime.utcnow() + timedelta(hours=2)).isoformat()
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # Verify in database
    db = TestingSessionLocal()
    session = db.query(DBSession).filter(DBSession.title == "New Test Session").first()
    assert session is not None
    assert session.batch_id == test_batch.id
    db.close()

def test_student_marks_attendance(client, test_student, test_batch, test_batch_student, test_session):
    # Login as student
    login_response = client.post("/auth/login", json={
        "email": "student@test.com",
        "password": "test123"
    })
    token = login_response.json()["access_token"]
    
    # Mark attendance
    response = client.post("/attendance/mark",
        json={
            "session_id": test_session.id,
            "status": "present"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # Verify in database
    db = TestingSessionLocal()
    attendance = db.query(Attendance).filter(
        Attendance.session_id == test_session.id,
        Attendance.student_id == test_student.id
    ).first()
    assert attendance is not None
    assert attendance.status == AttendanceStatus.present
    db.close()

def test_monitoring_endpoint_post_405(client):
    # POST to monitoring endpoint should return 405
    response = client.post("/monitoring/attendance")
    assert response.status_code == 405

def test_no_token_401(client):
    # Try to access protected endpoint without token
    response = client.post("/batches", json={
        "name": "Unauthorized Batch",
        "institution_id": 1
    })
    assert response.status_code == 401