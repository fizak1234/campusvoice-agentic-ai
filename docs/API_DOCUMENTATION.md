# SOAIDEATHON-S1: API Specification & Endpoint Reference

**Base URL**: `http://127.0.0.1:8000`
**Interactive Swagger UI**: `http://127.0.0.1:8000/docs`

---

## 1. Agentic AI Service Gateway

### `POST /api/agent/submit`
*Protected (Bearer Token)*: Natural language entry point for any institutional request (`Certificate`, `Maintenance`, `LabBooking`, `Grievance`).

**Request Body**:
```json
{
  "title": "Emergency Bonafide Certificate for Visa Interview",
  "description": "I have a US Visa interview scheduled this Friday and require an official Bonafide Certificate stating my full-time enrollment in 6th Sem B.Tech CSE. Roll No: 220101489.",
  "domain": "Certificate"
}
```

**Response (201 Created)**:
```json
{
  "message": "Service request parsed, planned, and orchestrated by Agentic AI",
  "request": {
    "id": 1,
    "user_id": 5,
    "request_type": "Certificate",
    "title": "Emergency Bonafide Certificate for Visa Interview",
    "category": "Bonafide Certificate",
    "status": "Awaiting Human Approval",
    "priority": "High",
    "detected_language": "en",
    "requires_hitl": true,
    "hitl_reason": "Consequential action: Official institutional document issuance requires Registrar / HOD digital authorization.",
    "agent_plan": [
      "1. Identify student Reg No. 220101489 and verified active enrollment",
      "2. Verified 84.5% semester attendance (Complies with >75% requirement in POL-CERT-01)",
      "3. Cross-checked Library and Accounts clearance (No pending holds)",
      "4. 🚨 Consequential Action: Route to Academic Registrar for digital seal sign-off (HITL)",
      "5. Auto-generate cryptographic QR-coded Bonafide PDF upon approval"
    ],
    "policy_citations": [
      {
        "code": "POL-CERT-01",
        "title": "Bonafide & Character Certificate Issuance Policy",
        "rule": "Requires verified >75% attendance and Registrar approval."
      }
    ]
  }
}
```

---

## 2. Human-in-the-Loop (HITL) Administration

### `GET /api/hitl/pending`
*Admin Only (Bearer Token)*: Returns all consequential actions currently paused at Human-in-the-Loop gates.

### `POST /api/hitl/decide`
*Admin Only (Bearer Token)*: Executes human approval, modification, or rejection with immutable audit signature.

**Request Body**:
```json
{
  "request_id": 1,
  "decision": "Approved",
  "notes": "Verified attendance record (84.5%) and academic standing. Digital seal authorized."
}
```

**Response (200 OK)**:
```json
{
  "message": "Human-in-the-Loop decision 'Approved' successfully executed for Request #1.",
  "request": {
    "id": 1,
    "status": "Executed",
    "hitl_decision": "Approved",
    "hitl_approver": "Dean of Student Affairs",
    "execution_result": "Certificate issued with verified digital signature of Dean of Student Affairs (Registrar/HOD). Ready for download."
  }
}
```

---

## 3. Auditable Action Trail & Explainability

### `GET /api/audit-trail/{request_id}`
*Protected (Bearer Token)*: Returns the step-by-step chronological audit trail for the specified request.

**Response (200 OK)**:
```json
{
  "request_id": 1,
  "title": "Emergency Bonafide Certificate for Visa Interview",
  "domain": "Certificate",
  "status": "Executed",
  "audit_logs": [
    {
      "id": 1,
      "step": 1,
      "actor": "Agentic AI",
      "action": "Language & Intent Decomposition",
      "details": "Detected language: en. Identified domain as Certificate (Bonafide Certificate) with High priority."
    },
    {
      "id": 2,
      "step": 2,
      "actor": "Agentic AI",
      "action": "Institutional Policy Check",
      "details": "Cross-referenced against verified institutional policies: POL-CERT-01.",
      "policy_ref": "POL-CERT-01"
    },
    {
      "id": 3,
      "step": 3,
      "actor": "Agentic AI",
      "action": "🚨 Consequential Action Gate Paused",
      "details": "High-impact institutional action requires human approval. Reason: Certificate issuance requires Registrar/HOD digital authorization."
    },
    {
      "id": 4,
      "step": 4,
      "actor": "Human Approver (Dean of Student Affairs)",
      "action": "HITL Decision: Approved",
      "details": "Administrator recorded 'Approved' decision. Notes: Verified attendance record (84.5%)."
    },
    {
      "id": 5,
      "step": 5,
      "actor": "System Workflow Engine",
      "action": "Workflow Status Updated (Executed)",
      "details": "Certificate issued with verified digital signature of Dean of Student Affairs. Ready for download."
    }
  ]
}
```

---

## 4. Institutional Knowledge Base

### `GET /api/knowledge-base`
Returns verified institutional handbook policy documents (`POL-CERT-01`, `POL-MAINT-01`, `POL-LAB-01`, `POL-GRIEV-01`, etc.).
