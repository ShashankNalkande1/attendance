# routes/__init__.py
from .auth import router as auth_router
from .batches import router as batches_router
from .attendance import router as attendance_router

__all__ = ['auth_router', 'batches_router', 'attendance_router']