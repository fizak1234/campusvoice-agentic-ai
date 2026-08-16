from datetime import datetime, timezone
import json
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from database import Base


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="user")  # "user" or "admin"
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    service_requests = relationship("ServiceRequest", back_populates="user", cascade="all, delete-orphan")
    grievances = relationship("Grievance", back_populates="user", cascade="all, delete-orphan")


class ServiceRequest(Base):
    """
    Unified Institutional Service Request model:
    Supports Grievances, Certificate Issuance, Maintenance Tickets, and Lab Bookings.
    """
    __tablename__ = "service_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Request domain: 'Grievance', 'Certificate', 'Maintenance', 'LabBooking'
    request_type = Column(String(50), nullable=False, default="Grievance", index=True)
    
    title = Column(String(250), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    
    # Status lifecycle: 'Pending', 'Awaiting Human Approval', 'In Progress', 'Approved', 'Executed', 'Resolved', 'Rejected'
    status = Column(String(50), default="Pending", index=True)
    priority = Column(String(50), default="Medium")  # Low, Medium, High, Urgent
    
    # Agentic AI & Multilingual metadata
    detected_language = Column(String(20), default="en")
    agent_plan = Column(Text, nullable=True)  # JSON array of planned steps
    policy_citations = Column(Text, nullable=True)  # JSON array of cited policies
    
    # Human-in-the-Loop (HITL) Consequential Action fields
    requires_hitl = Column(Boolean, default=False)
    hitl_reason = Column(Text, nullable=True)
    hitl_decision = Column(String(50), nullable=True)  # 'Approved', 'Rejected', 'Modified'
    hitl_approver = Column(String(100), nullable=True)
    hitl_notes = Column(Text, nullable=True)
    
    # Autonomous workflow outcome
    execution_result = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    user = relationship("User", back_populates="service_requests")
    audit_logs = relationship("AuditLog", back_populates="service_request", cascade="all, delete-orphan", order_by="AuditLog.step_number")


class AuditLog(Base):
    """
    Immutable Auditable Action Trail:
    Tracks every reasoning step, tool call, policy check, human approval, and execution.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("service_requests.id"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    actor = Column(String(50), nullable=False)  # 'Agentic AI', 'Student', 'Administrator', 'System'
    action = Column(String(100), nullable=False)  # 'Intent Decomposed', 'Policy Verified', 'HITL Paused', etc.
    details = Column(Text, nullable=False)
    policy_ref = Column(String(100), nullable=True)
    timestamp = Column(DateTime, default=utc_now)

    # Relationships
    service_request = relationship("ServiceRequest", back_populates="audit_logs")


# Backward compatibility table
class Grievance(Base):
    __tablename__ = "grievances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    status = Column(String(50), default="Pending")
    priority = Column(String(50), default="Medium")
    ai_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    user = relationship("User", back_populates="grievances")