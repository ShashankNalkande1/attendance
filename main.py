# main.py
from fastapi import FastAPI
from routes import auth, batches, attendance
from auth import monitoring_auth
from models import create_tables

app = FastAPI(title="Attendance System API")

# Create tables on startup
@app.on_event("startup")
def startup_event():
    create_tables()

# Include routers
app.include_router(auth.router)
app.include_router(monitoring_auth.router)
app.include_router(batches.router)
app.include_router(attendance.router)

# Note: Sessions router would be similar to batches
# You would create routes/sessions.py with POST /sessions endpoint

@app.get("/")
def root():
    return {"message": "Attendance System API", "version": "1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)