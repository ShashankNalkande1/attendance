# auth/monitoring_auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Dict, Any
from auth.dependencies import get_current_user
from auth.jwt_handler import SECRET_KEY, ALGORITHM

MONITORING_SECRET_KEY = SECRET_KEY + "_monitoring"  # Different secret for monitoring tokens
MONITORING_TOKEN_EXPIRE_HOURS = 1

router = APIRouter(prefix="/auth", tags=["monitoring"])

def create_monitoring_token(user_id: int) -> str:
    """Create a short-lived monitoring token"""
    payload = {
        "user_id": user_id,
        "role": "monitoring_officer",
        "scope": "read_only",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=MONITORING_TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, MONITORING_SECRET_KEY, algorithm=ALGORITHM)

def verify_monitoring_token(token: str) -> Dict[str, Any]:
    """
    Verify monitoring token - rejects standard JWT tokens
    """
    try:
        payload = jwt.decode(token, MONITORING_SECRET_KEY, algorithms=[ALGORITHM])
        
        # Strict validation: must have all monitoring-specific fields
        if payload.get("role") != "monitoring_officer":
            return None
        if payload.get("scope") != "read_only":
            return None
        if "user_id" not in payload:
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            return None
            
        return payload
    except JWTError:
        return None

class MonitoringTokenBearer(HTTPBearer):
    async def __call__(self, request):
        credentials = await super().__call__(request)
        payload = verify_monitoring_token(credentials.credentials)
        
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired monitoring token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload

@router.post("/monitoring-token")
def get_monitoring_token(
    current_user: dict = Depends(get_current_user)
):
    """
    Generate monitoring token - requires standard JWT with monitoring_officer role
    """
    if current_user.get("role") != "monitoring_officer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only monitoring officers can generate monitoring tokens"
        )
    
    monitoring_token = create_monitoring_token(current_user["user_id"])
    
    return {
        "access_token": monitoring_token,
        "token_type": "bearer",
        "expires_in": MONITORING_TOKEN_EXPIRE_HOURS * 3600
    }