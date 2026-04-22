# routes/attendance.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from models import get_db, Session as DBSession, Attendance, BatchStudent, UserRole, AttendanceStatus
from auth.rbac import require_role

router = APIRouter(prefix="/attendance", tags=["attendance"])

class MarkAttendanceRequest(BaseModel):
    session_id: int
    status: str  # "present", "absent", "late"

class AttendanceResponse(BaseModel):
    session_id: int
    student_id: int
    status: str
    marked_at: datetime

@router.post("/mark", response_model=AttendanceResponse)
def mark_attendance(
    attendance_data: MarkAttendanceRequest,
    current_user: dict = Depends(require_role(["student"])),
    db: Session = Depends(get_db)
):
    student_id = current_user["user_id"]
    
    # 1. Verify session exists
    session = db.query(DBSession).filter(DBSession.id == attendance_data.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 2. Verify student belongs to batch of that session
    is_enrolled = db.query(BatchStudent).filter(
        BatchStudent.batch_id == session.batch_id,
        BatchStudent.student_id == student_id
    ).first()
    
    if not is_enrolled:
        raise HTTPException(
            status_code=403, 
            detail="Student is not enrolled in the batch for this session"
        )
    
    # 3. Verify session date is not in future (optional but recommended)
    if session.date > datetime.utcnow():
        raise HTTPException(status_code=400, detail="Cannot mark attendance for future sessions")
    
    # 4. Validate status
    try:
        status_enum = AttendanceStatus(attendance_data.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status. Must be: present, absent, late")
    
    # 5. Insert or update attendance record
    attendance = db.query(Attendance).filter(
        Attendance.session_id == attendance_data.session_id,
        Attendance.student_id == student_id
    ).first()
    
    if attendance:
        # Update existing
        attendance.status = status_enum
        attendance.marked_at = datetime.utcnow()
    else:
        # Create new
        attendance = Attendance(
            session_id=attendance_data.session_id,
            student_id=student_id,
            status=status_enum
        )
        db.add(attendance)
    
    db.commit()
    db.refresh(attendance)
    
    return AttendanceResponse(
        session_id=attendance.session_id,
        student_id=attendance.student_id,
        status=attendance.status.value,
        marked_at=attendance.marked_at
    )