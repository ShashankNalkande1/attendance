# main.py - Updated with modern lifespan event handling
from fastapi import FastAPI
from contextlib import asynccontextmanager
from routes.auth import router as auth_router
from routes.batches import router as batches_router
from routes.attendance import router as attendance_router
from auth.monitoring_auth import router as monitoring_router
from models import create_tables, engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: This runs before the application starts receiving requests
    print("🚀 Starting up Attendance System API...")
    try:
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version}")
        
        # Create tables
        create_tables()
        print("✅ Database tables created/verified")
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        raise
    
    yield  # This separates startup and shutdown
    
    # Shutdown: This runs after the application has finished handling requests
    print("🛑 Shutting down Attendance System API...")
    # Clean up resources if needed
    engine.dispose()
    print("✅ Database connections closed")

# Create FastAPI app with lifespan
app = FastAPI(
    title="New Attendance System API",
    version="1.0.0",
    description="API for managing attendance with role-based access control",
    lifespan=lifespan
)

# Include routers
app.include_router(auth_router)
app.include_router(monitoring_router)
app.include_router(batches_router)
app.include_router(attendance_router)

@app.get("/")
def root():
    return {
        "message": "New Attendance System API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}

# Only run with uvicorn directly when script is executed
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8006))
    # For production, remove reload=True
    uvicorn.run(
        "main:app",  # Use import string instead of app object
        host="0.0.0.0",
        port=port,
        reload=True,  # Keep for development
        log_level="info"
    )