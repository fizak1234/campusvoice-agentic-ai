# 🎓 CampusVoice AI — College Grievance Management System

A full-stack, AI-powered College Grievance Management System built with **React**, **FastAPI**, **PostgreSQL**, and local **Ollama Llama 3.2 3B**.

---

## 🌟 Key Features

1. **Student Grievance Intake**:
   - Submit grievances with titles, detailed descriptions, and quick-fill templates.
   - Real-time pre-submission AI analysis preview.
   - Comprehensive status tracking (`Pending`, `In Progress`, `Resolved`, `Rejected`).
   - Search, filter by category, priority, and status.

2. **Local AI Intelligence (Ollama + Llama 3.2 3B)**:
   - **Zero paid APIs**: 100% local privacy-preserving LLM inference.
   - **Automated Categorization**: `Academic`, `Scholarship`, `Hostel`, `Examination`, `Fees`, `Other`.
   - **Automated Priority Detection**: `Low`, `Medium`, `High`.
   - **Executive Summaries**: Synthesizes grievances into concise 1-2 sentence briefs for administrators.
   - **Resilient Fallback**: Automatic graceful fallback if Ollama is unreachable.

3. **Role-Based Admin Console**:
   - Review grievances from all students with full contact context.
   - Fast status transition controls (`Pending` → `In Progress` → `Resolved` → `Rejected`).
   - Detailed inspection modal.
   - Real-time resolution metrics.

4. **Security & Authentication**:
   - JWT access tokens with expiration.
   - Password hashing with Argon2 / modern crypto.
   - Role-based authorization guardrails.
   - Fully decoupled secrets managed through `.env`.

---

## 🛠️ Tech Stack

- **Frontend**: React 19, Vite, Axios, Custom Modern CSS Design System.
- **Backend**: Python 3, FastAPI, SQLAlchemy ORM, PyJWT, Pydantic v2.
- **Database**: PostgreSQL (`ai_grievance_db`).
- **AI Engine**: Ollama running `llama3.2:3b` at `http://localhost:11434`.

---

## 🚀 Quick Start Guide

### 1. Database Setup
Ensure PostgreSQL is running locally and create the database:
```sql
CREATE DATABASE ai_grievance_db;
```

### 2. Ollama Local LLM
Ensure Ollama is running and download the model:
```bash
ollama run llama3.2:3b
```

### 3. Backend Setup
```bash
cd backend
# Activate virtual environment
.\venv\Scripts\activate
# Install requirements if needed
pip install -r requirements.txt  # (or pip install fastapi uvicorn sqlalchemy psycopg2-binary pyjwt pwdlib argon2-cffi python-dotenv requests email-validator)

# Run FastAPI server
uvicorn main:app --reload --port 8000
```
API runs at: `http://127.0.0.1:8000` (Swagger UI at `/docs`).

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at: `http://localhost:5173`.

---

## 🔑 Pre-Seeded Demo Accounts

| Role | Email | Password |
|---|---|---|
| **Student Demo** | `student@college.edu` | `student123` |
| **Admin Demo** | `admin@college.edu` | `admin123` |

---

## 📚 Documentation
- [Architecture & System Design](docs/ARCHITECTURE.md)
- [REST API Reference](docs/API_DOCUMENTATION.md)
