# DATABASE_URL = "postgresql://neondb_owner:npg_RKCJZi49dtkb@ep-shiny-band-aolnzzcu-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# models.py - Fixed relationship definitions
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum

load_dotenv()

# Neon PostgreSQL connection
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
     DATABASE_URL = "postgresg=require"

# Engine configuration
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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
    
    # Relationships - Fixed
    institution = relationship("User", remote_side=[id], backref="members")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

class Batch(Base):
    __tablename__ = "batches"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    institution_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    institution = relationship("User", backref="batches")
    trainers = relationship("BatchTrainer", back_populates="batch", cascade="all, delete-orphan")
    students = relationship("BatchStudent", back_populates="batch", cascade="all, delete-orphan")
    invites = relationship("BatchInvite", back_populates="batch", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="batch", cascade="all, delete-orphan")

class BatchTrainer(Base):
    __tablename__ = "batch_trainers"
    
    batch_id = Column(Integer, ForeignKey("batches.id"), primary_key=True)
    trainer_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    
    # Relationships
    batch = relationship("Batch", back_populates="trainers")
    trainer = relationship("User", backref="batch_trainer_assignments")

class BatchStudent(Base):
    __tablename__ = "batch_students"
    
    batch_id = Column(Integer, ForeignKey("batches.id"), primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    
    # Relationships
    batch = relationship("Batch", back_populates="students")
    student = relationship("User", backref="batch_student_assignments")

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
    created_by_user = relationship("User", backref="batch_invites_created")

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
    trainer = relationship("User", backref="sessions_conducted")
    attendance_records = relationship("Attendance", back_populates="session", cascade="all, delete-orphan")

class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(AttendanceStatus), nullable=False)
    marked_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="attendance_records")
    student = relationship("User", backref="attendance_records")

def create_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully")

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()