from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import auth_routes, students, hostels, rooms, dashboard, fees, payments, complaints, maintenance, notifications, announcements, allocations, movements

app = FastAPI(title="HostelOS API", description="Smarter Hostel Management")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router, prefix="/api/auth", tags=["auth"])
app.include_router(students.router, prefix="/api/students", tags=["students"])
app.include_router(hostels.router, prefix="/api/hostels", tags=["hostels"])
app.include_router(rooms.router, prefix="/api/rooms", tags=["rooms"])
app.include_router(allocations.router, prefix="/api/allocations", tags=["allocations"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(fees.router, prefix="/api/fees", tags=["fees"])
app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
app.include_router(complaints.router, prefix="/api/complaints", tags=["complaints"])
app.include_router(maintenance.router, prefix="/api/maintenance", tags=["maintenance"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(announcements.router, prefix="/api/announcements", tags=["announcements"])
app.include_router(movements.router, prefix="/api/movements", tags=["movements"])

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "HostelOS API"}

@app.get("/")
def root():
    return {"status": "ok", "service": "HostelOS API"}
