# 🏛️ CampusVoice Agentic AI — SOA Institutional Service Delivery

### 🏆 Winning Solution for **SOAIDEATHON 2026** (Problem Statement: **SOAIDEATHON-S1**)
**Human-in-the-Loop Agentic AI for Autonomous Institutional Service Delivery**

---

## 🌟 Key Pillars & Features

1. **🤖 Multi-Step Agentic Reasoning (Ollama Llama 3.2 3B)**:
   - Evaluates natural language intent, decomposes requests into sequential action graphs, checks policy constraints, and orchestrates workflows with zero paid API dependencies.

2. **📜 Four Core Institutional Service Modules**:
   - 📜 **Certificate Issuance**: Bonafide Certificates, Transcripts, NOC, and Character Certificates with attendance verification.
   - 🔧 **Maintenance & Facilities**: Emergency plumbing, electrical, HVAC, and campus asset maintenance dispatch.
   - 🔬 **Laboratory Bookings**: High-Performance NVIDIA A100 GPU Cluster and Robotics testbed reservations with conflict checks.
   - ⚖️ **Grievance Escalation**: Scholarship fund delays, evaluation grade discrepancies, and academic redressal.

3. **🚨 Human-in-the-Loop (HITL) Consequential Safeguards**:
   - Safe operations execute autonomously.
   - Consequential / high-risk operations (certificate issuance, budget spending, safety clearances) automatically pause at a **HITL Gate** awaiting administrator sign-off.

4. **📜 Immutable Auditable Action Trail**:
   - Full explainability ledger logging every agent thought, tool action, policy citation, timestamp, and human approver signature.

5. **📖 Verified Policy Knowledge Base & Zero-Hallucination Guardrails**:
   - RAG engine verifies institutional rules (`POL-CERT-01`, `POL-LAB-01`, etc.) and flags conflicts/uncertainties instead of fabricating answers.

6. **🌐 Multilingual Natural Language Support**:
   - Native input & template support for **English, Hindi, and Odia**.

---

## 🌐 Live Application URLs

| Service | Live URL | Description |
|---|---|---|
| **🎨 Web Application (Frontend)** | [http://localhost:5173](http://localhost:5173) | Interactive student & administrator portal |
| **⚡ FastAPI Backend** | [http://127.0.0.1:8000](http://127.0.0.1:8000) | Agentic AI gateway & orchestration engine |
| **📖 Interactive API Docs** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Swagger UI for endpoint testing |

---

## 🔑 Pre-Seeded Demo Accounts

| Role | Email | Password | Role Description |
|---|---|---|---|
| **Student** | `student@college.edu` | `student123` | Submit requests, simulate agent plans, view audit trails |
| **Dean / Admin (HITL)** | `admin@college.edu` | `admin123` | Authorize consequential actions, view master requests & policy base |

---

## 📚 Documentation
- [Architecture & Design](docs/ARCHITECTURE.md)
- [REST API Reference](docs/API_DOCUMENTATION.md)
- [Cloud Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
