# routes/batches.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import secrets
from models import get_db, Batch, BatchTrainer, BatchStudent, BatchInvite, User, UserRole
from auth.rbac import require_role

router = APIRouter(prefix="/batches", tags=["batches"])

class BatchCreate(BaseModel):
    name: str
    institution_id: int

class BatchInviteResponse(BaseModel):
    token: str
    expires_at: datetime

class JoinBatchRequest(BaseModel):
    token: str

@router.post("")
def create_batch(
    batch_data: BatchCreate,
    current_user: dict = Depends(require_role(["trainer", "institution"])),
    db: Session = Depends(get_db)
):
    # Verify institution exists
    institution = db.query(User).filter(
        User.id == batch_data.institution_id,
        User.role == UserRole.institution
    ).first()
    
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    # If user is trainer, verify they belong to this institution
    if current_user["role"] == "trainer":
        trainer = db.query(User).filter(User.id == current_user["user_id"]).first()
        if trainer.institution_id != batch_data.institution_id:
            raise HTTPException(
                status_code=403, 
                detail="Trainer can only create batches for their own institution"
            )
    
    batch = Batch(
        name=batch_data.name,
        institution_id=batch_data.institution_id
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    
    return {"id": batch.id, "name": batch.name, "institution_id": batch.institution_id}

@router.post("/{batch_id}/invite", response_model=BatchInviteResponse)
def create_invite(
    batch_id: int,
    current_user: dict = Depends(require_role(["trainer"])),
    db: Session = Depends(get_db)
):
    # Verify batch exists
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Verify trainer belongs to this batch
    is_trainer = db.query(BatchTrainer).filter(
        BatchTrainer.batch_id == batch_id,
        BatchTrainer.trainer_id == current_user["user_id"]
    ).first()
    
    if not is_trainer:
        raise HTTPException(status_code=403, detail="Not authorized to invite to this batch")
    
    # Generate unique token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    invite = BatchInvite(
        batch_id=batch_id,
        token=token,
        created_by=current_user["user_id"],
        expires_at=expires_at
    )
    db.add(invite)
    db.commit()
    
    return BatchInviteResponse(token=token, expires_at=expires_at)

@router.post("/join")
def join_batch(
    join_data: JoinBatchRequest,
    current_user: dict = Depends(require_role(["student"])),
    db: Session = Depends(get_db)
):
    # Find valid invite
    invite = db.query(BatchInvite).filter(
        BatchInvite.token == join_data.token,
        BatchInvite.used == False,
        BatchInvite.expires_at > datetime.utcnow()
    ).first()
    
    if not invite:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    # Check if already enrolled
    existing = db.query(BatchStudent).filter(
        BatchStudent.batch_id == invite.batch_id,
        BatchStudent.student_id == current_user["user_id"]
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this batch")
    
    # Add student to batch
    enrollment = BatchStudent(
        batch_id=invite.batch_id,
        student_id=current_user["user_id"]
    )
    db.add(enrollment)
    
    # Mark invite as used
    invite.used = True
    
    db.commit()
    
    return {"message": "Successfully joined batch", "batch_id": invite.batch_id}