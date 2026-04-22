# routes/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import get_db, User
from auth.rbac import require_role

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
def get_all_users(
    current_user: dict = Depends(require_role(["trainer", "institution", "monitoring_officer"])),
    db: Session = Depends(get_db)
):
    """Get all users (admin/trainer only)"""
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role.value,
            "institution_id": u.institution_id,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]

@router.get("/institutions")
def get_institutions(
    db: Session = Depends(get_db)
):
    """Get all institutions (public)"""
    institutions = db.query(User).filter(User.role == "institution").all()
    return [
        {
            "id": i.id,
            "name": i.name,
            "email": i.email
        }
        for i in institutions
    ]