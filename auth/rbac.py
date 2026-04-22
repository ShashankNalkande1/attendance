# auth/rbac.py
from fastapi import Depends, HTTPException, status
from typing import List
from auth.dependencies import get_current_user

def require_role(allowed_roles: List[str]):
    """
    Dependency factory for role-based access control
    Usage: require_role(["trainer", "institution"])
    """
    async def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {', '.join(allowed_roles)}"
            )
        
        return current_user
    
    return role_checker

def require_monitoring_token():
    """
    Dependency for monitoring endpoints - uses separate monitoring token
    """
    from auth.monitoring_auth import MonitoringTokenBearer
    return MonitoringTokenBearer()