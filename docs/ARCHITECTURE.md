# SOAIDEATHON-S1: Human-in-the-Loop Agentic AI for Autonomous Institutional Service Delivery

## 1. Executive Summary & Problem Mapping
This platform directly addresses **SOAIDEATHON-S1** by providing an enterprise-grade **Human-in-the-Loop (HITL) Agentic AI** ecosystem for autonomous institutional service delivery at SOA University.

### Key Capabilities:
1. **Multi-Step Action Planning**: Breaks natural language intent into deterministic execution graphs (`Parse` → `RAG Policy Verification` → `Constraint Check` → `HITL Gate` → `Execute`).
2. **Four Unified Institutional Workflows**:
   - 📜 **Certificate Requests** (Bonafide, Transcripts, NOC, Character Certificate with digital authorization)
   - 🔧 **Maintenance Tickets** (Hostel plumbing, electrical emergencies, lab AC & asset repair)
   - 🔬 **Laboratory Bookings** (GPU Cluster, Robotics testbeds, Chemistry analyzers with conflict detection)
   - ⚖️ **Grievance Escalation** (Scholarship fund delays, Exam re-evaluation discrepancies, Academic issues)
3. **Human-in-the-Loop (HITL) Safeguard**:
   - Autonomous execution is permitted for safe, non-consequential operations (e.g. routine plumbing work orders, compliant GPU cluster slots).
   - High-impact / consequential actions (certificate digital seal, budget authorizations, high-priority escalations) automatically pause at a **HITL Gate** and require administrator sign-off.
4. **Auditable Action Trail**:
   - An immutable chronological ledger records every agent thought, tool call, cited policy code, human approver signature, and execution outcome.
5. **Verified Knowledge Retrieval (RAG) & Policy Conflict / Uncertainty Detection**:
   - Cross-references requests against institutional guidelines (e.g. `POL-CERT-01`, `POL-LAB-01`, `POL-MAINT-01`, `POL-GRIEV-01`).
   - Detects policy contradictions or ambiguous student requests instead of hallucinating answers.
6. **Multilingual Interaction**:
   - Supports natural language inputs and prompt templates in **English, Hindi, and Odia**.

---

## 2. Agentic Architecture & Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student / Faculty
    participant UI as CampusVoice Frontend
    participant Agent as Agentic AI Orchestrator (Llama 3.2 3B)
    participant KB as Institutional Knowledge Base (RAG)
    participant DB as PostgreSQL Database
    actor Admin as HITL Administrator (Dean/Registrar)

    Student->>UI: Submits Request (e.g. "Urgent Bonafide Certificate for Visa")
    UI->>Agent: POST /api/agent/submit (Natural Language)
    Agent->>Agent: Step 1: Detect Language & Decompose Intent
    Agent->>KB: Step 2: Retrieve Relevant Policies (e.g. POL-CERT-01)
    KB-->>Agent: Returns Policy Rules (>75% attendance, Dean signature)
    Agent->>Agent: Step 3: Check for Policy Conflicts & Uncertainties
    Agent->>Agent: Step 4: Evaluate Consequential Impact Threshold
    
    alt Safe Autonomous Action (e.g. Compliant GPU Slot)
        Agent->>DB: Execute Workflow & Commit Audit Trail
        DB-->>UI: Return Confirmed Ticket + Booking Token
    else High-Impact Consequential Action (e.g. Certificate Issuance / Budget)
        Agent->>DB: Pause Execution -> Status: "Awaiting Human Approval"
        Agent->>DB: Log HITL Gate Triggered into Audit Trail
        DB-->>Admin: Alert: New Consequential Action in HITL Queue
        Admin->>UI: Review Student Context, Policy Compliance & Agent Plan
        Admin->>DB: POST /api/hitl/decide (Decision: "Approved" / "Rejected")
        DB->>DB: Execute Workflow (Generate Certificate / Dispatch Order)
        DB->>DB: Append Human Approver Signature to Audit Trail
        DB-->>Student: Update Status: "Executed" (Ready for Download)
    end
```

---

## 3. Database Schema

- **`users`**: User identities, roles (`user`, `admin`), password hashes.
- **`service_requests`**: Unified domain records (`request_type`, `title`, `description`, `category`, `status`, `priority`, `detected_language`, `agent_plan`, `policy_citations`, `requires_hitl`, `hitl_reason`, `execution_result`).
- **`audit_logs`**: Immutable step-by-step reasoning and decision trail (`step_number`, `actor`, `action`, `details`, `policy_ref`, `timestamp`).
- **`knowledge_base`**: Institutional policy codes, constraints, and SLA rules.
