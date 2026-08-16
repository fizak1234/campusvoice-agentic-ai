import os
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc, text

from database import engine, Base, get_db, SessionLocal, init_db_schema
import models
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user_id,
    get_current_user,
    get_current_admin,
)
from ai_service import analyze_grievance, check_ollama_status

# Initialize database schema and columns
init_db_schema()

app = FastAPI(
    title="AI-Powered College Grievance Management System",
    description="Full-stack AI grievance platform using FastAPI, PostgreSQL, and local Ollama Llama 3.2 3B.",
    version="1.0.0",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows frontend on localhost:5173, localhost:3000, etc.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------
# Pydantic Schemas
# -------------------------------------------------------------

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    role: Optional[str] = "user"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class GrievanceCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    category: Optional[str] = None  # Optional from UI, AI predicts or overrides


class GrievanceStatusUpdate(BaseModel):
    status: str = Field(..., description="Pending, In Progress, Resolved, Rejected")


class GrievanceResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str
    category: str
    status: str
    priority: str
    ai_summary: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    student_name: Optional[str] = None
    student_email: Optional[str] = None

    class Config:
        from_attributes = True


class AIAnalyzeRequest(BaseModel):
    title: str
    description: str


# -------------------------------------------------------------
# Database Seeding & Startup Event
# -------------------------------------------------------------

@app.on_event("startup")
def seed_default_accounts():
    """Seed default admin and demo student accounts if not already present."""
    db = SessionLocal()
    try:
        # Check Admin
        admin_email = "admin@college.edu"
        admin = db.query(models.User).filter(models.User.email == admin_email).first()
        if not admin:
            admin = models.User(
                name="College Administrator",
                email=admin_email,
                hashed_password=hash_password("admin123"),
                role="admin",
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        # Check Demo Student
        student_email = "student@college.edu"
        student = db.query(models.User).filter(models.User.email == student_email).first()
        if not student:
            student = models.User(
                name="Aarav Sharma",
                email=student_email,
                hashed_password=hash_password("student123"),
                role="user",
            )
            db.add(student)
            db.commit()
            db.refresh(student)

            # Seed initial realistic grievances for the demo student
            sample_grievances = [
                {
                    "title": "Scholarship disbursement delay for semester 5",
                    "description": "My merit-cum-means scholarship was officially approved 3 months ago by the state portal, but the finance office hasn't disbursed the funds into my bank account.",
                    "category": "Scholarship",
                    "priority": "High",
                    "status": "In Progress",
                    "ai_summary": "Approved merit scholarship has not been disbursed for 3 months despite official portal approval.",
                },
                {
                    "title": "Frequent water outage in Block B 3rd Floor Hostel",
                    "description": "The water supply on the 3rd floor of Hostel B has been cutting out every morning between 7 AM and 10 AM for the past week, making it difficult for students to attend morning 8 AM lectures.",
                    "category": "Hostel",
                    "priority": "Medium",
                    "status": "Pending",
                    "ai_summary": "Hostel Block B 3rd floor experiences recurring morning water outages impacting class attendance.",
                },
                {
                    "title": "Re-evaluation grade mismatch on portal for Data Structures",
                    "description": "I applied for re-evaluation in Data Structures (CS301). The physical mark sheet shows a revised score of 82/100, but the student ERP portal still reflects the old score of 54.",
                    "category": "Examination",
                    "priority": "High",
                    "status": "Resolved",
                    "ai_summary": "ERP portal displays old grade (54) instead of updated physical re-evaluation score (82) in CS301.",
                },
            ]

            for item in sample_grievances:
                g = models.Grievance(
                    user_id=student.id,
                    title=item["title"],
                    description=item["description"],
                    category=item["category"],
                    priority=item["priority"],
                    status=item["status"],
                    ai_summary=item["ai_summary"],
                )
                db.add(g)
            db.commit()
    except Exception as e:
        print(f"Startup seeding error: {e}")
        db.rollback()
    finally:
        db.close()


# -------------------------------------------------------------
# Base & Health Endpoints
# -------------------------------------------------------------

@app.get("/")
def root():
    return {
        "system": "AI-Powered College Grievance Management System",
        "status": "operational",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/api/system-status")
def system_status(db: Session = Depends(get_db)):
    """Provides real-time diagnostic telemetry on DB, Ollama LLM, and grievance metrics."""
    # DB status
    db_connected = False
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    # Ollama status
    ollama_info = check_ollama_status()

    # Grievance counts
    total_g = db.query(models.Grievance).count()
    pending_g = db.query(models.Grievance).filter(models.Grievance.status == "Pending").count()
    in_progress_g = db.query(models.Grievance).filter(models.Grievance.status == "In Progress").count()
    resolved_g = db.query(models.Grievance).filter(models.Grievance.status == "Resolved").count()
    high_priority_g = db.query(models.Grievance).filter(models.Grievance.priority == "High").count()
    total_users = db.query(models.User).count()

    return {
        "database_connected": db_connected,
        "ollama": ollama_info,
        "stats": {
            "total_grievances": total_g,
            "pending": pending_g,
            "in_progress": in_progress_g,
            "resolved": resolved_g,
            "high_priority": high_priority_g,
            "total_users": total_users,
        },
    }


# -------------------------------------------------------------
# Authentication Endpoints
# -------------------------------------------------------------

@app.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_user(user: UserRegister, db: Session = Depends(get_db)):
    email_clean = user.email.strip().lower()
    existing = db.query(models.User).filter(models.User.email == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Normalize role
    user_role = "admin" if user.role and user.role.strip().lower() == "admin" else "user"

    new_user = models.User(
        name=user.name.strip(),
        email=email_clean,
        hashed_password=hash_password(user.password),
        role=user_role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role,
        },
    }


@app.post("/login", response_model=TokenResponse)
def login_json(credentials: UserLogin, db: Session = Depends(get_db)):
    email_clean = credentials.email.strip().lower()
    user = db.query(models.User).filter(models.User.email == email_clean).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "name": user.name,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at,
        },
    }


@app.post("/token", response_model=dict)
def login_oauth2(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 compatible token endpoint for OpenAPI Swagger UI."""
    email_clean = form_data.username.strip().lower()
    user = db.query(models.User).filter(models.User.email == email_clean).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "name": user.name,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }


@app.get("/users/me", response_model=UserResponse)
def get_current_user_profile(current_user: models.User = Depends(get_current_user)):
    return current_user


# -------------------------------------------------------------
# Grievance Endpoints (Student & Common)
# -------------------------------------------------------------

@app.post("/grievances", status_code=status.HTTP_201_CREATED)
def submit_grievance(
    payload: GrievanceCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submits a grievance:
    1. Sends title and description to Ollama Llama 3.2 3B for real-time analysis.
    2. Stores AI-detected category, priority, and summary in PostgreSQL.
    3. Initializes status to 'Pending'.
    """
    # Run Ollama AI analysis
    ai_result = analyze_grievance(payload.title, payload.description)

    detected_category = ai_result.get("category", payload.category or "Other")
    detected_priority = ai_result.get("priority", "Medium")
    detected_summary = ai_result.get("summary", payload.description[:150])

    new_grievance = models.Grievance(
        user_id=current_user.id,
        title=payload.title.strip(),
        description=payload.description.strip(),
        category=detected_category,
        priority=detected_priority,
        status="Pending",
        ai_summary=detected_summary,
    )

    db.add(new_grievance)
    db.commit()
    db.refresh(new_grievance)

    return {
        "message": "Grievance submitted and analyzed successfully by AI",
        "grievance": {
            "id": new_grievance.id,
            "user_id": new_grievance.user_id,
            "title": new_grievance.title,
            "description": new_grievance.description,
            "category": new_grievance.category,
            "priority": new_grievance.priority,
            "status": new_grievance.status,
            "ai_summary": new_grievance.ai_summary,
            "created_at": new_grievance.created_at,
            "updated_at": new_grievance.updated_at,
            "is_ai_fallback": ai_result.get("is_ai_fallback", False),
        },
    }


@app.get("/grievances", response_model=dict)
def get_student_grievances(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves all grievances created by the authenticated user."""
    grievances = (
        db.query(models.Grievance)
        .filter(models.Grievance.user_id == current_user.id)
        .order_by(desc(models.Grievance.created_at))
        .all()
    )

    result = []
    for g in grievances:
        result.append({
            "id": g.id,
            "user_id": g.user_id,
            "title": g.title,
            "description": g.description,
            "category": g.category,
            "status": g.status,
            "priority": g.priority,
            "ai_summary": g.ai_summary,
            "created_at": g.created_at,
            "updated_at": g.updated_at,
            "student_name": current_user.name,
            "student_email": current_user.email,
        })

    return {"grievances": result}


# Alias for legacy/convenience
@app.get("/my-grievances", response_model=dict)
def get_my_grievances_alias(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_student_grievances(current_user=current_user, db=db)


@app.get("/grievances/{grievance_id}", response_model=dict)
def get_grievance_detail(
    grievance_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves a single grievance if owned by the user or if user is admin."""
    grievance = db.query(models.Grievance).filter(models.Grievance.id == grievance_id).first()

    if not grievance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grievance not found.",
        )

    if current_user.role != "admin" and grievance.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this grievance.",
        )

    student = db.query(models.User).filter(models.User.id == grievance.user_id).first()

    return {
        "grievance": {
            "id": grievance.id,
            "user_id": grievance.user_id,
            "title": grievance.title,
            "description": grievance.description,
            "category": grievance.category,
            "status": grievance.status,
            "priority": grievance.priority,
            "ai_summary": grievance.ai_summary,
            "created_at": grievance.created_at,
            "updated_at": grievance.updated_at,
            "student_name": student.name if student else "Unknown",
            "student_email": student.email if student else "Unknown",
        }
    }


# -------------------------------------------------------------
# Admin Endpoints
# -------------------------------------------------------------

@app.get("/admin/grievances", response_model=dict)
def get_all_grievances_admin(
    status_filter: Optional[str] = Query(None, alias="status"),
    category_filter: Optional[str] = Query(None, alias="category"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    search: Optional[str] = Query(None),
    admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Admin-only endpoint to list all grievances with student details and filters."""
    query = (
        db.query(models.Grievance, models.User)
        .join(models.User, models.Grievance.user_id == models.User.id)
    )

    if status_filter and status_filter != "All":
        query = query.filter(models.Grievance.status == status_filter)
    if category_filter and category_filter != "All":
        query = query.filter(models.Grievance.category == category_filter)
    if priority_filter and priority_filter != "All":
        query = query.filter(models.Grievance.priority == priority_filter)
    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(
            (models.Grievance.title.ilike(search_fmt)) |
            (models.Grievance.description.ilike(search_fmt)) |
            (models.User.name.ilike(search_fmt)) |
            (models.User.email.ilike(search_fmt))
        )

    results = query.order_by(desc(models.Grievance.created_at)).all()

    grievance_list = []
    for g, u in results:
        grievance_list.append({
            "id": g.id,
            "user_id": g.user_id,
            "title": g.title,
            "description": g.description,
            "category": g.category,
            "status": g.status,
            "priority": g.priority,
            "ai_summary": g.ai_summary,
            "created_at": g.created_at,
            "updated_at": g.updated_at,
            "student_name": u.name,
            "student_email": u.email,
        })

    return {"grievances": grievance_list, "total": len(grievance_list)}


@app.put("/admin/grievances/{grievance_id}/status", response_model=dict)
def update_grievance_status(
    grievance_id: int,
    payload: GrievanceStatusUpdate,
    admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Admin-only endpoint to update the lifecycle status of a grievance."""
    allowed_statuses = ["Pending", "In Progress", "Resolved", "Rejected"]
    if payload.status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{payload.status}'. Allowed: {', '.join(allowed_statuses)}",
        )

    grievance = db.query(models.Grievance).filter(models.Grievance.id == grievance_id).first()
    if not grievance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grievance not found.",
        )

    grievance.status = payload.status
    grievance.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(grievance)

    student = db.query(models.User).filter(models.User.id == grievance.user_id).first()

    return {
        "message": f"Grievance #{grievance_id} status updated to {grievance.status}",
        "grievance": {
            "id": grievance.id,
            "user_id": grievance.user_id,
            "title": grievance.title,
            "description": grievance.description,
            "category": grievance.category,
            "status": grievance.status,
            "priority": grievance.priority,
            "ai_summary": grievance.ai_summary,
            "created_at": grievance.created_at,
            "updated_at": grievance.updated_at,
            "student_name": student.name if student else "Unknown",
            "student_email": student.email if student else "Unknown",
        },
    }


# -------------------------------------------------------------
# Direct AI Analysis Endpoint
# -------------------------------------------------------------

@app.post("/ai/analyze", response_model=dict)
def analyze_grievance_api(payload: AIAnalyzeRequest):
    """Direct testing/preview endpoint to analyze grievance text using Ollama Llama 3.2 3B."""
    if not payload.title or not payload.description:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both title and description are required.",
        )

    result = analyze_grievance(payload.title, payload.description)
    return {"analysis": result}