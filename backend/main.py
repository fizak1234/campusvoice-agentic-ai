import os
import json
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
from ai_service import (
    analyze_grievance,
    plan_and_execute_agentic_service,
    check_ollama_status,
)
from knowledge_base import INSTITUTIONAL_POLICIES, retrieve_relevant_policies

# Initialize database schema and columns
init_db_schema()

app = FastAPI(
    title="CampusVoice Agentic AI — SOA Institutional Service Delivery (SOAIDEATHON-S1)",
    description="Human-in-the-Loop Agentic AI for Autonomous Institutional Service Delivery with Local Ollama Llama 3.2 3B & PostgreSQL.",
    version="2.0.0",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------
# Pydantic Request & Response Schemas
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


class AgentServiceSubmit(BaseModel):
    title: str = Field(..., min_length=3, max_length=250)
    description: str = Field(..., min_length=5)
    domain: Optional[str] = None  # 'Certificate', 'Maintenance', 'LabBooking', 'Grievance'
    preferred_category: Optional[str] = None


class HITLDecisionRequest(BaseModel):
    request_id: int
    decision: str = Field(..., description="'Approved', 'Rejected', 'Modified'")
    notes: Optional[str] = ""


class GrievanceCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    category: Optional[str] = None


class GrievanceStatusUpdate(BaseModel):
    status: str


class AIAnalyzeRequest(BaseModel):
    title: str
    description: str


# -------------------------------------------------------------
# Database Seeding & Startup Event (Rich Demo Data)
# -------------------------------------------------------------

@app.on_event("startup")
def seed_default_accounts_and_workflows():
    db = SessionLocal()
    try:
        # 1. Seed Admin
        admin_email = "admin@college.edu"
        admin = db.query(models.User).filter(models.User.email == admin_email).first()
        if not admin:
            admin = models.User(
                name="Dean of Student Affairs",
                email=admin_email,
                hashed_password=hash_password("admin123"),
                role="admin",
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        # 2. Seed Student
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

        # 3. Seed Service Requests if table is empty
        existing_req_count = db.query(models.ServiceRequest).count()
        if existing_req_count == 0:
            sample_workflows = [
                # Certificate Request with HITL
                {
                    "request_type": "Certificate",
                    "title": "Urgent Bonafide Certificate for Passport & Visa Application",
                    "description": "I need an official Bonafide Certificate with institutional seal stating that I am a full-time 6th Semester B.Tech Computer Science student for my upcoming US visa appointment on Friday. Reg No: 220101489.",
                    "category": "Bonafide Certificate",
                    "status": "Awaiting Human Approval",
                    "priority": "High",
                    "detected_language": "en",
                    "agent_plan": json.dumps([
                        "1. Identify student Reg No. 220101489 and verified active enrollment",
                        "2. Verified 84.5% semester attendance (Complies with >75% requirement in POL-CERT-01)",
                        "3. Cross-checked Library and Accounts clearance (No pending holds)",
                        "4. 🚨 Consequential Action: Route to Academic Registrar for digital seal sign-off (HITL)",
                        "5. Auto-generate cryptographic QR-coded Bonafide PDF upon approval"
                    ]),
                    "policy_citations": json.dumps([
                        {"code": "POL-CERT-01", "title": "Bonafide & Character Certificate Issuance Policy", "rule": "Requires verified >75% attendance and Registrar approval."}
                    ]),
                    "requires_hitl": True,
                    "hitl_reason": "Consequential action: Official institutional document issuance requires Registrar / HOD digital authorization.",
                    "ai_summary": "Student requests urgent Bonafide Certificate for visa verification. Attendance and dues cleared.",
                    "audit_logs": [
                        {"step": 1, "actor": "Agentic AI", "action": "Intent Deconstruction", "details": "Classified domain as Certificate / Subcategory Bonafide Certificate."},
                        {"step": 2, "actor": "Agentic AI", "action": "Policy Knowledge Retrieval", "details": "Retrieved POL-CERT-01. Verified student attendance (84.5%) complies with >75% threshold.", "policy_ref": "POL-CERT-01"},
                        {"step": 3, "actor": "Agentic AI", "action": "Consequential Action Gate Triggered", "details": "Autonomous execution paused. Routed to Dean / Registrar Approval Queue (HITL Gate)."}
                    ]
                },

                # Maintenance Emergency Ticket
                {
                    "request_type": "Maintenance",
                    "title": "Hostel Block B 3rd Floor Water Outage & Broken Cooler",
                    "description": "Drinking water cooler pipe in Hostel B 3rd floor burst, leaking dirty water and cutting off drinking supply for 45 students.",
                    "category": "Hostel Plumbing",
                    "status": "In Progress",
                    "priority": "Urgent",
                    "detected_language": "en",
                    "agent_plan": json.dumps([
                        "1. Deconstruct request location: Hostel B 3rd Floor",
                        "2. Classified as Emergency Maintenance per Policy POL-MAINT-01 (2-hour SLA)",
                        "3. Dispatched automated job order to Duty Plumber Team #4",
                        "4. Alerted Hostel Warden and scheduled physical inspection"
                    ]),
                    "policy_citations": json.dumps([
                        {"code": "POL-MAINT-01", "title": "Hostel & Campus Emergency Maintenance SLA", "rule": "Water supply issues dispatched within 2 hours."}
                    ]),
                    "requires_hitl": False,
                    "execution_result": "Automated Work Order #MW-8012 dispatched to Duty Plumbing Crew. ETA: 45 minutes.",
                    "ai_summary": "Burst drinking water pipe in Hostel B 3rd Floor. Emergency maintenance dispatched.",
                    "audit_logs": [
                        {"step": 1, "actor": "Agentic AI", "action": "Urgency Assessment", "details": "Evaluated as Urgent Priority (Water supply failure)."},
                        {"step": 2, "actor": "Agentic AI", "action": "Autonomous Dispatch", "details": "Dispatched emergency work order #MW-8012 without requiring manual pause per POL-MAINT-01.", "policy_ref": "POL-MAINT-01"}
                    ]
                },

                # Laboratory Booking
                {
                    "request_type": "LabBooking",
                    "title": "NVIDIA A100 GPU Cluster Slot for Deep Learning Capstone",
                    "description": "Requesting 4-hour reservation on GPU Workstation Cluster Node 02 for distributed fine-tuning of Llama 3.2 3B model for B.Tech Major Project from 2:00 PM to 6:00 PM.",
                    "category": "GPU Cluster (A100/H100)",
                    "status": "Executed",
                    "priority": "Medium",
                    "detected_language": "en",
                    "agent_plan": json.dumps([
                        "1. Parsed slot: 2:00 PM to 6:00 PM (4 hours duration)",
                        "2. Checked Policy POL-LAB-01 compliance (Within permitted 08:00 AM - 09:00 PM window; duration <= 4 hrs)",
                        "3. Checked cluster calendar for node conflicts: Node 02 available",
                        "4. Allocated GPU compute credentials and SSH token",
                        "5. Committed booking to audit ledger"
                    ]),
                    "policy_citations": json.dumps([
                        {"code": "POL-LAB-01", "title": "High-Performance GPU Cluster Access", "rule": "Permitted 8 AM - 9 PM, max 4 hours per slot."}
                    ]),
                    "requires_hitl": False,
                    "execution_result": "Slot Reserved: Node-02 (4x A100 80GB) from 14:00 to 18:00. SSH Access token generated.",
                    "ai_summary": "4-hour GPU cluster slot reserved on Node 02 for deep learning model fine-tuning.",
                    "audit_logs": [
                        {"step": 1, "actor": "Agentic AI", "action": "Conflict Verification", "details": "Verified timing (14:00-18:00) falls within allowed hours and duration <= 4 hours.", "policy_ref": "POL-LAB-01"},
                        {"step": 2, "actor": "Agentic AI", "action": "Autonomous Slot Allocation", "details": "Provisioned GPU Node-02 compute instance and committed access grant."}
                    ]
                },

                # Grievance Escalation
                {
                    "request_type": "Grievance",
                    "title": "State Scholarship approved 3 months ago but funds not credited",
                    "description": "My National Scholarship Scheme award was officially approved on 14th May with App ID NSP-2026-9014, but university bursar office has not disbursed the ₹25,000 credit.",
                    "category": "Scholarship",
                    "status": "Awaiting Human Approval",
                    "priority": "High",
                    "detected_language": "en",
                    "agent_plan": json.dumps([
                        "1. Identify financial distress indicator (>60 days delay)",
                        "2. Cross-reference POL-GRIEV-02 (Delayed scholarship escalation policy)",
                        "3. 🚨 Consequential Action Gate: Escalate directly to University Finance Officer (HITL)",
                        "4. Request expedited fund verification from Finance Section"
                    ]),
                    "policy_citations": json.dumps([
                        {"code": "POL-GRIEV-02", "title": "Scholarship & Financial Aid Escalation", "rule": "Scholarships delayed >60 days require Finance Officer review."}
                    ]),
                    "requires_hitl": True,
                    "hitl_reason": "Financial escalation: Delayed scholarship >60 days requires University Finance Officer review.",
                    "ai_summary": "Delayed disbursement of approved ₹25,000 NSP scholarship. Escalation routed to Finance Officer.",
                    "audit_logs": [
                        {"step": 1, "actor": "Agentic AI", "action": "Financial Triage", "details": "Identified 3-month disbursement delay on NSP award #NSP-2026-9014."},
                        {"step": 2, "actor": "Agentic AI", "action": "Administrative Escalation Gate", "details": "Paused autonomous resolution; routed to Finance Officer for fund release sign-off.", "policy_ref": "POL-GRIEV-02"}
                    ]
                }
            ]

            for item in sample_workflows:
                sr = models.ServiceRequest(
                    user_id=student.id,
                    request_type=item["request_type"],
                    title=item["title"],
                    description=item["description"],
                    category=item["category"],
                    status=item["status"],
                    priority=item["priority"],
                    detected_language=item["detected_language"],
                    agent_plan=item["agent_plan"],
                    policy_citations=item["policy_citations"],
                    requires_hitl=item["requires_hitl"],
                    hitl_reason=item.get("hitl_reason"),
                    execution_result=item.get("execution_result"),
                    ai_summary=item["ai_summary"],
                )
                db.add(sr)
                db.flush()

                for log in item.get("audit_logs", []):
                    al = models.AuditLog(
                        request_id=sr.id,
                        step_number=log["step"],
                        actor=log["actor"],
                        action=log["action"],
                        details=log["details"],
                        policy_ref=log.get("policy_ref"),
                    )
                    db.add(al)

            db.commit()
    except Exception as e:
        print(f"Startup seeding error: {e}")
        db.rollback()
    finally:
        db.close()


# -------------------------------------------------------------
# System & Diagnostic Endpoints
# -------------------------------------------------------------

@app.get("/")
def root():
    return {
        "system": "CampusVoice Agentic AI — SOA Institutional Service Delivery (SOAIDEATHON-S1)",
        "theme": "Smart Automation & Human-in-the-Loop Autonomous Service Delivery",
        "status": "operational",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/api/system-status")
def system_status(db: Session = Depends(get_db)):
    """Provides real-time diagnostic telemetry on DB, Ollama LLM, and HITL metrics."""
    db_connected = False
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    ollama_info = check_ollama_status()

    total_requests = db.query(models.ServiceRequest).count()
    pending_hitl = db.query(models.ServiceRequest).filter(models.ServiceRequest.status == "Awaiting Human Approval").count()
    in_progress = db.query(models.ServiceRequest).filter(models.ServiceRequest.status == "In Progress").count()
    resolved = db.query(models.ServiceRequest).filter(models.ServiceRequest.status.in_(["Executed", "Resolved", "Approved"])).count()
    total_users = db.query(models.User).count()

    return {
        "database_connected": db_connected,
        "ollama": ollama_info,
        "theme": "SOAIDEATHON-S1: Human-in-the-Loop Agentic AI",
        "stats": {
            "total_requests": total_requests,
            "pending_human_approvals": pending_hitl,
            "in_progress": in_progress,
            "resolved": resolved,
            "total_users": total_users,
        },
    }


@app.get("/api/knowledge-base")
def get_knowledge_base():
    """Returns verified institutional policies used by RAG retrieval."""
    return {"policies": INSTITUTIONAL_POLICIES}


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

    return {"access_token": token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserResponse)
def get_current_user_profile(current_user: models.User = Depends(get_current_user)):
    return current_user


# -------------------------------------------------------------
# AGENTIC SERVICE WORKFLOW ENDPOINTS (SOAIDEATHON-S1)
# -------------------------------------------------------------

@app.post("/api/agent/submit", status_code=status.HTTP_201_CREATED)
def submit_agentic_service_request(
    payload: AgentServiceSubmit,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Core Agentic AI Service Gateway:
    1. Multilingual parsing & intent decomposition.
    2. Institutional Policy Retrieval & Conflict/Uncertainty detection.
    3. Multi-Step Execution Planning.
    4. Consequential Action Risk Assessment (HITL Gate vs Autonomous Execution).
    5. Immutable Audit Log generation.
    """
    agent_output = plan_and_execute_agentic_service(
        payload.title,
        payload.description,
        payload.domain
    )

    domain = agent_output["domain"]
    category = agent_output["category"]
    priority = agent_output["priority"]
    requires_hitl = agent_output["requires_hitl"]
    hitl_reasons = agent_output.get("hitl_reasons", [])
    hitl_reason_str = hitl_reasons[0] if hitl_reasons else None
    
    # Determine initial status
    if requires_hitl:
        initial_status = "Awaiting Human Approval"
        exec_result = "Execution paused at Consequential Action Gate. Awaiting Administrator Authorization."
    else:
        initial_status = "Executed" if domain in ["LabBooking", "Maintenance"] else "In Progress"
        if domain == "LabBooking":
            exec_result = f"Autonomous Slot Confirmed for {category}. Access tokens provisioned."
        elif domain == "Maintenance":
            exec_result = f"Maintenance Job Order dispatched automatically to Duty Technician Crew."
        else:
            exec_result = "Request acknowledged and queued for automated processing."

    # Create ServiceRequest
    new_request = models.ServiceRequest(
        user_id=current_user.id,
        request_type=domain,
        title=payload.title.strip(),
        description=payload.description.strip(),
        category=category,
        status=initial_status,
        priority=priority,
        detected_language=agent_output.get("detected_language", "en"),
        agent_plan=json.dumps(agent_output.get("plan_steps", [])),
        policy_citations=json.dumps(agent_output.get("policy_citations", [])),
        requires_hitl=requires_hitl,
        hitl_reason=hitl_reason_str,
        execution_result=exec_result,
        ai_summary=agent_output.get("summary"),
    )
    db.add(new_request)
    db.flush()

    # Generate Auditable Action Trail Logs
    step_num = 1
    # Step 1: Language & Intent Parsing
    db.add(models.AuditLog(
        request_id=new_request.id,
        step_number=step_num,
        actor="Agentic AI",
        action="Language & Intent Decomposition",
        details=f"Detected language: {agent_output.get('detected_language')}. Identified domain as {domain} ({category}) with {priority} priority."
    ))

    # Step 2: Policy Verification
    step_num += 1
    citations = agent_output.get("policy_citations", [])
    cite_str = ", ".join([c["code"] for c in citations]) if citations else "Standard Operating Procedures"
    db.add(models.AuditLog(
        request_id=new_request.id,
        step_number=step_num,
        actor="Agentic AI",
        action="Institutional Policy Check",
        details=f"Cross-referenced against verified institutional policies: {cite_str}.",
        policy_ref=citations[0]["code"] if citations else None
    ))

    # Step 3: Conflict & Uncertainty Evaluation
    step_num += 1
    if agent_output.get("has_conflict"):
        conflict_msg = "; ".join(agent_output.get("conflicts", []))
        db.add(models.AuditLog(
            request_id=new_request.id,
            step_number=step_num,
            actor="Agentic AI",
            action="Policy Conflict Flagged",
            details=f"Detected policy constraint conflict: {conflict_msg}"
        ))
    else:
        db.add(models.AuditLog(
            request_id=new_request.id,
            step_number=step_num,
            actor="Agentic AI",
            action="Constraint & Uncertainty Verification",
            details="No policy conflicts detected. Constraints verified compliant."
        ))

    # Step 4: Consequential Action Gate
    step_num += 1
    if requires_hitl:
        db.add(models.AuditLog(
            request_id=new_request.id,
            step_number=step_num,
            actor="Agentic AI",
            action="🚨 Consequential Action Gate Paused",
            details=f"High-impact institutional action requires human approval. Reason: {hitl_reason_str}"
        ))
    else:
        db.add(models.AuditLog(
            request_id=new_request.id,
            step_number=step_num,
            actor="Agentic AI",
            action="Autonomous Execution Permitted",
            details=f"Action cleared for automated dispatch: {exec_result}"
        ))

    db.commit()
    db.refresh(new_request)

    return {
        "message": "Service request parsed, planned, and orchestrated by Agentic AI",
        "request": _serialize_service_request(new_request, db),
    }


@app.get("/api/service-requests")
def get_service_requests(
    domain_filter: Optional[str] = Query(None, alias="domain"),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves service requests with filtering and role isolation."""
    query = db.query(models.ServiceRequest)

    if current_user.role != "admin":
        query = query.filter(models.ServiceRequest.user_id == current_user.id)

    if domain_filter and domain_filter != "All":
        query = query.filter(models.ServiceRequest.request_type == domain_filter)

    if status_filter and status_filter != "All":
        query = query.filter(models.ServiceRequest.status == status_filter)

    requests = query.order_by(desc(models.ServiceRequest.created_at)).all()
    return {"requests": [_serialize_service_request(r, db) for r in requests]}


@app.get("/api/service-requests/{request_id}")
def get_service_request_detail(
    request_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    req = db.query(models.ServiceRequest).filter(models.ServiceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Service request not found.")

    if current_user.role != "admin" and req.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied.")

    return {"request": _serialize_service_request(req, db)}


@app.get("/api/audit-trail/{request_id}")
def get_audit_trail(
    request_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns the immutable step-by-step audit trail for explainability."""
    req = db.query(models.ServiceRequest).filter(models.ServiceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Service request not found.")

    if current_user.role != "admin" and req.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied.")

    logs = db.query(models.AuditLog).filter(models.AuditLog.request_id == request_id).order_by(models.AuditLog.step_number).all()

    return {
        "request_id": request_id,
        "title": req.title,
        "domain": req.request_type,
        "status": req.status,
        "audit_logs": [
            {
                "id": log.id,
                "step": log.step_number,
                "actor": log.actor,
                "action": log.action,
                "details": log.details,
                "policy_ref": log.policy_ref,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            }
            for log in logs
        ]
    }


# -------------------------------------------------------------
# HUMAN-IN-THE-LOOP (HITL) APPROVAL CENTER (Admin Only)
# -------------------------------------------------------------

@app.get("/api/hitl/pending")
def get_pending_hitl_approvals(
    admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Admin queue for all consequential actions awaiting human approval."""
    pending_items = (
        db.query(models.ServiceRequest)
        .filter(models.ServiceRequest.status == "Awaiting Human Approval")
        .order_by(desc(models.ServiceRequest.created_at))
        .all()
    )
    return {"pending_approvals": [_serialize_service_request(r, db) for r in pending_items], "count": len(pending_items)}


@app.post("/api/hitl/decide")
def make_hitl_decision(
    payload: HITLDecisionRequest,
    admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Executes Human-in-the-Loop decision on consequential action:
    - 'Approved' -> Triggers autonomous workflow execution & document generation.
    - 'Rejected' -> Halts action and notifies student with administrator feedback.
    - 'Modified' -> Adjusts scope and queues with revised parameters.
    """
    req = db.query(models.ServiceRequest).filter(models.ServiceRequest.id == payload.request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Service request not found.")

    decision = payload.decision.strip().capitalize()
    if decision not in ["Approved", "Rejected", "Modified"]:
        raise HTTPException(status_code=400, detail="Decision must be 'Approved', 'Rejected', or 'Modified'.")

    req.hitl_decision = decision
    req.hitl_approver = admin.name
    req.hitl_notes = payload.notes or "Decision recorded by administrator."
    req.updated_at = datetime.now(timezone.utc)

    # Determine execution outcome
    if decision == "Approved":
        req.status = "Executed"
        if req.request_type == "Certificate":
            req.execution_result = f"Certificate issued with verified digital signature of {admin.name} (Registrar/HOD). Ready for download."
        elif req.request_type == "Maintenance":
            req.execution_result = f"Emergency repair budget authorized by {admin.name}. Technician dispatched."
        elif req.request_type == "LabBooking":
            req.execution_result = f"Lab access safety clearance approved by {admin.name}. Slot confirmed."
        else:
            req.execution_result = f"Grievance escalation authorized and forwarded to University Executive Committee by {admin.name}."
    elif decision == "Rejected":
        req.status = "Rejected"
        req.execution_result = f"Request declined by {admin.name}. Reason: {payload.notes or 'Does not meet criteria'}"
    else:
        req.status = "In Progress"
        req.execution_result = f"Modification requested by {admin.name}: {payload.notes}"

    # Log human decision to immutable audit trail
    current_step_count = db.query(models.AuditLog).filter(models.AuditLog.request_id == req.id).count()
    db.add(models.AuditLog(
        request_id=req.id,
        step_number=current_step_count + 1,
        actor=f"Human Approver ({admin.name})",
        action=f"HITL Decision: {decision}",
        details=f"Administrator recorded '{decision}' decision. Notes: {payload.notes or 'None'}"
    ))

    # Log final execution step
    db.add(models.AuditLog(
        request_id=req.id,
        step_number=current_step_count + 2,
        actor="System Workflow Engine",
        action=f"Workflow Status Updated ({req.status})",
        details=req.execution_result
    ))

    db.commit()
    db.refresh(req)

    return {
        "message": f"Human-in-the-Loop decision '{decision}' successfully executed for Request #{req.id}.",
        "request": _serialize_service_request(req, db),
    }


# -------------------------------------------------------------
# Backward-Compatible Grievance Endpoints
# -------------------------------------------------------------

@app.post("/grievances", status_code=status.HTTP_201_CREATED)
def legacy_submit_grievance(
    payload: GrievanceCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Route through unified agentic endpoint
    res = submit_agentic_service_request(
        AgentServiceSubmit(
            title=payload.title,
            description=payload.description,
            domain="Grievance",
            preferred_category=payload.category,
        ),
        current_user=current_user,
        db=db,
    )
    req = res["request"]
    return {
        "message": "Grievance submitted and analyzed successfully by AI",
        "grievance": {
            "id": req["id"],
            "user_id": req["user_id"],
            "title": req["title"],
            "description": req["description"],
            "category": req["category"],
            "priority": req["priority"],
            "status": req["status"],
            "ai_summary": req["ai_summary"],
            "created_at": req["created_at"],
        }
    }


@app.get("/grievances")
@app.get("/my-grievances")
def legacy_get_grievances(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    res = get_service_requests(domain_filter="All", status_filter="All", current_user=current_user, db=db)
    return {"grievances": res["requests"]}


@app.get("/admin/grievances")
def legacy_admin_grievances(
    status_filter: Optional[str] = Query(None, alias="status"),
    category_filter: Optional[str] = Query(None, alias="category"),
    search: Optional[str] = Query(None),
    admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = get_service_requests(domain_filter="All", status_filter=status_filter, current_user=admin, db=db)
    return {"grievances": res["requests"], "total": len(res["requests"])}


@app.put("/admin/grievances/{grievance_id}/status")
def legacy_update_status(
    grievance_id: int,
    payload: GrievanceStatusUpdate,
    admin: models.User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    req = db.query(models.ServiceRequest).filter(models.ServiceRequest.id == grievance_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Grievance not found.")

    req.status = payload.status
    req.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(req)

    return {
        "message": f"Grievance #{grievance_id} status updated to {req.status}",
        "grievance": _serialize_service_request(req, db),
    }


@app.post("/ai/analyze")
def analyze_grievance_api(payload: AIAnalyzeRequest):
    result = plan_and_execute_agentic_service(payload.title, payload.description)
    return {"analysis": result}


# -------------------------------------------------------------
# Internal Serialization Helper
# -------------------------------------------------------------

def _serialize_service_request(r: models.ServiceRequest, db: Session) -> dict:
    student = db.query(models.User).filter(models.User.id == r.user_id).first()
    
    plan_steps = []
    if r.agent_plan:
        try:
            plan_steps = json.loads(r.agent_plan)
        except:
            plan_steps = [r.agent_plan]

    citations = []
    if r.policy_citations:
        try:
            citations = json.loads(r.policy_citations)
        except:
            citations = []

    return {
        "id": r.id,
        "user_id": r.user_id,
        "request_type": r.request_type,
        "title": r.title,
        "description": r.description,
        "category": r.category,
        "status": r.status,
        "priority": r.priority,
        "detected_language": r.detected_language,
        "agent_plan": plan_steps,
        "policy_citations": citations,
        "requires_hitl": r.requires_hitl,
        "hitl_reason": r.hitl_reason,
        "hitl_decision": r.hitl_decision,
        "hitl_approver": r.hitl_approver,
        "hitl_notes": r.hitl_notes,
        "execution_result": r.execution_result,
        "ai_summary": r.ai_summary,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        "student_name": student.name if student else "Unknown",
        "student_email": student.email if student else "Unknown",
    }