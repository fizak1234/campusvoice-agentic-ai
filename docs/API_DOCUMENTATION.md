# API Reference — AI-Powered College Grievance Management System

**Base URL**: `http://127.0.0.1:8000`
**Swagger UI**: `http://127.0.0.1:8000/docs`

---

## 1. System & Health

### `GET /`
Returns basic service health and metadata.

### `GET /api/system-status`
Returns real-time diagnostics on PostgreSQL database, local Ollama LLM, and grievance metrics.

**Response (200 OK)**:
```json
{
  "database_connected": true,
  "ollama": {
    "available": true,
    "url": "http://localhost:11434/api/generate",
    "model": "llama3.2:3b",
    "models_installed": ["llama3.2:3b"],
    "target_model_ready": true
  },
  "stats": {
    "total_grievances": 12,
    "pending": 4,
    "in_progress": 3,
    "resolved": 5,
    "high_priority": 2,
    "total_users": 6
  }
}
```

---

## 2. Authentication

### `POST /register`
Creates a new student or admin account.

**Request Body**:
```json
{
  "name": "Aarav Sharma",
  "email": "aarav@college.edu",
  "password": "password123",
  "role": "user"
}
```

### `POST /login`
Authenticates credentials and returns a JWT access token.

**Request Body**:
```json
{
  "email": "student@college.edu",
  "password": "student123"
}
```

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "id": 5,
    "name": "Aarav Sharma",
    "email": "student@college.edu",
    "role": "user"
  }
}
```

### `GET /users/me`
*Protected (Bearer Token)*: Returns authenticated user profile.

---

## 3. Grievances

### `POST /grievances`
*Protected (Bearer Token)*: Submits a new grievance. Triggers local Ollama AI analysis and persists record.

**Request Body**:
```json
{
  "title": "Scholarship disbursement delay for semester 5",
  "description": "My merit-cum-means scholarship was approved 3 months ago but funds have not been credited.",
  "category": "Scholarship"
}
```

**Response (201 Created)**:
```json
{
  "message": "Grievance submitted and analyzed successfully by AI",
  "grievance": {
    "id": 14,
    "user_id": 5,
    "title": "Scholarship disbursement delay for semester 5",
    "description": "...",
    "category": "Scholarship",
    "priority": "High",
    "status": "Pending",
    "ai_summary": "Approved merit scholarship has not been disbursed for 3 months.",
    "created_at": "2026-08-16T11:05:12.682116Z",
    "is_ai_fallback": false
  }
}
```

### `GET /grievances` (or `GET /my-grievances`)
*Protected (Bearer Token)*: Returns all grievances submitted by the logged-in student.

### `GET /grievances/{id}`
*Protected (Bearer Token)*: Retrieves full details of a specific grievance.

---

## 4. Admin Management

### `GET /admin/grievances`
*Admin Only (Bearer Token)*: Lists all grievances across all students with filter parameters (`category`, `priority`, `status`, `search`).

### `PUT /admin/grievances/{id}/status`
*Admin Only (Bearer Token)*: Updates the grievance status (`Pending`, `In Progress`, `Resolved`, `Rejected`).

**Request Body**:
```json
{
  "status": "In Progress"
}
```

---

## 5. AI Diagnostics

### `POST /ai/analyze`
Direct testing endpoint to run grievance text through Ollama Llama 3.2 3B.

**Request Body**:
```json
{
  "title": "Hostel room water outage",
  "description": "No drinking water in hostel block B."
}
```

**Response (200 OK)**:
```json
{
  "analysis": {
    "category": "Hostel",
    "priority": "High",
    "summary": "Hostel Block B is facing a complete lack of drinking water.",
    "is_ai_fallback": false
  }
}
```
