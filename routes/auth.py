# routes/auth.py - Complete version with login
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
    institution_name: Optional[str] = None
    institution_email: Optional[EmailStr] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: Optional[int] = None
    role: Optional[str] = None
    name: Optional[str] = None

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
            detail=f"Invalid role. Allowed: student, trainer, institution, programme_manager, monitoring_officer"
        )
    
    # Handle institution
    institution_id = user_data.institution_id
    
    if role == UserRole.student or role == UserRole.trainer:
        if user_data.institution_name:
            # Find or create institution by name
            institution = db.query(User).filter(
                User.name == user_data.institution_name,
                User.role == UserRole.institution
            ).first()
            
            if not institution:
                # Create new institution
                inst_email = user_data.institution_email or f"{user_data.institution_name.lower().replace(' ', '_')}@institution.com"
                institution = User(
                    name=user_data.institution_name,
                    email=inst_email,
                    hashed_password=hash_password(f"inst_{user_data.institution_name.lower().replace(' ', '_')}_123"),
                    role=UserRole.institution,
                    institution_id=None
                )
                db.add(institution)
                db.flush()
            
            institution_id = institution.id
        elif institution_id:
            # Verify institution exists
            institution = db.query(User).filter(
                User.id == institution_id,
                User.role == UserRole.institution
            ).first()
            if not institution:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Institution with id {institution_id} not found"
                )
    
    # Create user
    hashed_pw = hash_password(user_data.password)
    user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_pw,
        role=role,
        institution_id=institution_id if role != UserRole.institution else None
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create token
    token = create_access_token({
        "user_id": user.id,
        "role": user.role.value,
        "email": user.email
    })
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        role=user.role.value,
        name=user.name
    )

@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create access token
    token = create_access_token({
        "user_id": user.id,
        "role": user.role.value,
        "email": user.email
    })
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        role=user.role.value,
        name=user.name
    )

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user