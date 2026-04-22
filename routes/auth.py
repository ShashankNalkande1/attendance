# routes/auth.py - Updated with auto-create institution functionality
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from models import get_db, User, UserRole
from auth.password import hash_password, verify_password
from auth.jwt_handler import create_access_token
from auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str
    institution_id: Optional[int] = None
    institution_name: Optional[str] = None  # New field for auto-creating institution
    institution_email: Optional[EmailStr] = None  # New field for institution email

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

def get_or_create_institution(db: Session, institution_id: Optional[int], institution_name: Optional[str], institution_email: Optional[EmailStr]) -> Optional[int]:
    """
    Get existing institution or create a new one
    Returns institution_id or None
    """
    # If institution_id is provided, verify it exists
    if institution_id is not None:
        institution = db.query(User).filter(
            User.id == institution_id,
            User.role == UserRole.institution
        ).first()
        
        if institution:
            return institution.id
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Institution with id {institution_id} not found"
            )
    
    # If institution_name is provided, try to find or create
    if institution_name:
        # Try to find existing institution by name
        existing_institution = db.query(User).filter(
            User.name == institution_name,
            User.role == UserRole.institution
        ).first()
        
        if existing_institution:
            return existing_institution.id
        
        # Create new institution
        # Use provided email or generate one
        inst_email = institution_email if institution_email else f"{institution_name.lower().replace(' ', '_')}@institution.com"
        
        # Check if email already exists
        existing_email = db.query(User).filter(User.email == inst_email).first()
        if existing_email:
            # Generate unique email
            base_email = inst_email.split('@')[0]
            inst_email = f"{base_email}_{db.query(User).count()}@institution.com"
        
        # Create default password for institution
        default_password = f"inst_{institution_name.lower().replace(' ', '_')}_123"
        
        new_institution = User(
            name=institution_name,
            email=inst_email,
            hashed_password=hash_password(default_password),
            role=UserRole.institution,
            institution_id=None
        )
        
        db.add(new_institution)
        db.flush()  # Get the ID without committing yet
        
        return new_institution.id
    
    return None

@router.post("/signup", response_model=TokenResponse)
def signup(user_data: SignupRequest, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate role
    try:
        role = UserRole(user_data.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Allowed roles: student, trainer, institution, programme_manager, monitoring_officer"
        )
    
    # Handle institution_id based on role
    institution_id = None
    
    if role == UserRole.student:
        # For students: try to get or create institution
        institution_id = get_or_create_institution(
            db, 
            user_data.institution_id, 
            user_data.institution_name,
            user_data.institution_email
        )
        
    elif role == UserRole.trainer:
        # For trainers: institution_id is required
        if user_data.institution_id is None and user_data.institution_name is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Trainer requires either institution_id or institution_name"
            )
        
        institution_id = get_or_create_institution(
            db, 
            user_data.institution_id, 
            user_data.institution_name,
            user_data.institution_email
        )
        
        if institution_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create or find institution"
            )
    
    elif role == UserRole.institution:
        # For institutions: they don't have an institution_id
        institution_id = None
        
        # Check if institution with same name already exists
        existing_inst = db.query(User).filter(
            User.name == user_data.name,
            User.role == UserRole.institution
        ).first()
        
        if existing_inst:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Institution with this name already exists"
            )
    
    # Create user
    hashed_pw = hash_password(user_data.password)
    user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_pw,
        role=role,
        institution_id=institution_id
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create token
    token = create_access_token({
        "user_id": user.id,
        "role": user.role.value
    })
    
    response_data = {
        "access_token": token,
        "token_type": "bearer"
    }
    
    # If an institution was auto-created, include its credentials in response
    if institution_id and user_data.institution_name and role == UserRole.student:
        institution = db.query(User).filter(User.id == institution_id).first()
        if institution and institution.created_at == user.created_at:  # Newly created
            response_data["institution_created"] = {
                "id": institution.id,
                "name": institution.name,
                "email": institution.email,
                "default_password": f"inst_{user_data.institution_name.lower().replace(' ', '_')}_123"
            }
    
    return response_data