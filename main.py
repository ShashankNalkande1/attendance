# main.py - Updated with all routes
from fastapi import FastAPI
from contextlib import asynccontextmanager
from routes.auth import router as auth_router
from routes.users import router as users_router
from routes.batches import router as batches_router
from routes.attendance import router as attendance_router
from auth.monitoring_auth import router as monitoring_router
from models import create_tables, engine
from sqlalchemy import text
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting up Attendance System API...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version}")
        
        create_tables()
        print("✅ Database tables created/verified")
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        raise
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Attendance System API...")
    engine.dispose()
    print("✅ Database connections closed")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Attendance System API",
    version="1.0.0",
    description="API for managing attendance with role-based access control",
    lifespan=lifespan
)

# Add CORS middleware for HTML dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(monitoring_router)
app.include_router(batches_router)
app.include_router(attendance_router)

@app.get("/")
def root():
    return {
        "message": "Attendance System API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8006))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)