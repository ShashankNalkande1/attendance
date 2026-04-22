# models.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Enum, Boolean, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum

Base = declarative_base()

class UserRole(enum.Enum):
    student = "student"
    trainer = "trainer"
    institution = "institution"
    programme_manager = "programme_manager"
    monitoring_officer = "monitoring_officer"

class AttendanceStatus(enum.Enum):
    present = "present"
    absent = "absent"
    late = "late"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    institution_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    institution = relationship("User", remote_side=[id], backref="members")
    owned_batches = relationship("Batch", back_populates="institution")
    trained_batches = relationship("BatchTrainer", back_populates="trainer")
    enrolled_batches = relationship("BatchStudent", back_populates="student")
    created_invites = relationship("BatchInvite", back_populates="created_by")
    sessions_conducted = relationship("Session", back_populates="trainer")
    attendance_records = relationship("Attendance", back_populates="student")

class Batch(Base):
    __tablename__ = "batches"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    institution_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    institution = relationship("User", back_populates="owned_batches")
    trainers = relationship("BatchTrainer", back_populates="batch")
    students = relationship("BatchStudent", back_populates="batch")
    invites = relationship("BatchInvite", back_populates="batch")
    sessions = relationship("Session", back_populates="batch")

class BatchTrainer(Base):
    __tablename__ = "batch_trainers"
    
    batch_id = Column(Integer, ForeignKey("batches.id"), primary_key=True)
    trainer_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    
    # Relationships
    batch = relationship("Batch", back_populates="trainers")
    trainer = relationship("User", back_populates="trained_batches")

class BatchStudent(Base):
    __tablename__ = "batch_students"
    
    batch_id = Column(Integer, ForeignKey("batches.id"), primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    
    # Relationships
    batch = relationship("Batch", back_populates="students")
    student = relationship("User", back_populates="enrolled_batches")

class BatchInvite(Base):
    __tablename__ = "batch_invites"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    
    # Relationships
    batch = relationship("Batch", back_populates="invites")
    created_by_user = relationship("User", back_populates="created_invites")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    batch = relationship("Batch", back_populates="sessions")
    trainer = relationship("User", back_populates="sessions_conducted")
    attendance_records = relationship("Attendance", back_populates="session")

class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(AttendanceStatus), nullable=False)
    marked_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="attendance_records")
    student = relationship("User", back_populates="attendance_records")

# Database setup
DATABASE_URL = "postgresql://user:password@localhost:5432/attendance_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()