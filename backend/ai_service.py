import os
import re
import json
import logging
import requests
from dotenv import load_dotenv

from knowledge_base import retrieve_relevant_policies, check_policy_conflicts_and_uncertainty, INSTITUTIONAL_POLICIES

load_dotenv()

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "30"))

VALID_DOMAINS = ["Grievance", "Certificate", "Maintenance", "LabBooking"]
VALID_PRIORITIES = ["Low", "Medium", "High", "Urgent"]


def check_ollama_status() -> dict:
    """Checks whether the local Ollama service is reachable and has the required model."""
    try:
        base_url = OLLAMA_URL.rsplit("/api/", 1)[0]
        tags_url = f"{base_url}/api/tags"
        response = requests.get(tags_url, timeout=1)
        if response.status_code == 200:
            data = response.json()
            models = [m.get("name") for m in data.get("models", [])]
            has_model = any(OLLAMA_MODEL in m for m in models)
            return {
                "available": True,
                "url": OLLAMA_URL,
                "model": OLLAMA_MODEL,
                "models_installed": models,
                "target_model_ready": has_model,
            }
    except Exception as e:
        logger.warning(f"Ollama health check failed: {e}")

    return {
        "available": False,
        "url": OLLAMA_URL,
        "model": OLLAMA_MODEL,
        "models_installed": [],
        "target_model_ready": False,
    }


def detect_language(text: str) -> str:
    """Detects primary language of user input (English, Hindi, Odia, etc.)."""
    # Simple unicode range detection for Indic scripts
    hindi_devanagari = len(re.findall(r'[\u0900-\u097F]', text))
    odia_script = len(re.findall(r'[\u0B00-\u0B7F]', text))

    if hindi_devanagari > 3:
        return "hi"  # Hindi
    elif odia_script > 3:
        return "or"  # Odia

    # Romanized Hindi/Hinglish keywords
    hinglish_words = ["mujhe", "chahiye", "mera", "meri", "pani", "paani", "kaam", "nahi", "kar", "raha", "jaldi", "karo"]
    if any(w in text.lower().split() for w in hinglish_words):
        return "hi-Latn"

    return "en"


def _agentic_heuristic_fallback(title: str, description: str, preferred_domain: str = None) -> dict:
    """Intelligent rule-based fallback agent when Ollama is busy or unreachable."""
    text = f"{title} {description}".lower()
    lang = detect_language(f"{title} {description}")

    # Determine Domain
    if preferred_domain and preferred_domain in VALID_DOMAINS:
        domain = preferred_domain
    elif any(k in text for k in ["certificate", "bonafide", "transcript", "noc", "character", "mark sheet", "degree"]):
        domain = "Certificate"
    elif any(k in text for k in ["repair", "fix", "water", "leak", "light", "plumbing", "fan", "ac", "broken", "hostel mess", "cooler"]):
        domain = "Maintenance"
    elif any(k in text for k in ["lab", "booking", "gpu", "cluster", "slot", "reserve", "workstation", "cuda", "equipment"]):
        domain = "LabBooking"
    else:
        domain = "Grievance"

    # Determine Category
    if domain == "Certificate":
        if "bonafide" in text:
            category = "Bonafide Certificate"
        elif "transcript" in text:
            category = "Academic Transcript"
        elif "noc" in text:
            category = "No Objection Certificate"
        else:
            category = "Study Certificate"
    elif domain == "Maintenance":
        if any(w in text for w in ["water", "leak", "plumb", "cooler"]):
            category = "Hostel Plumbing"
        elif any(w in text for w in ["light", "fan", "electric", "power", "switch"]):
            category = "Electrical Maintenance"
        else:
            category = "Facility Repair"
    elif domain == "LabBooking":
        if any(w in text for w in ["gpu", "ai", "nvidia", "deep learning"]):
            category = "GPU Cluster (A100/H100)"
        elif "robot" in text:
            category = "Robotics Testbed"
        else:
            category = "General Computing Lab"
    else:
        # Grievance
        if any(w in text for w in ["scholarship", "fee", "payment", "stipend"]):
            category = "Scholarship"
        elif any(w in text for w in ["exam", "grade", "re-eval", "backlog"]):
            category = "Examination"
        elif any(w in text for w in ["hostel", "mess", "warden"]):
            category = "Hostel"
        else:
            category = "Academic"

    # Determine Priority
    if any(w in text for w in ["urgent", "emergency", "immediately", "hospital", "stomach", "short circuit", "flood", "harassment"]):
        priority = "Urgent" if domain == "Maintenance" or domain == "Grievance" else "High"
    elif any(w in text for w in ["delay", "broken", "not working", "three months", "deadline"]):
        priority = "High"
    else:
        priority = "Medium"

    # Retrieve verified policy rules
    policies = retrieve_relevant_policies(f"{title} {description}", domain)
    citations = [{"code": p["id"], "title": p["title"], "rule": p["content"]} for p in policies]

    # Evaluate Policy Conflicts & Human-in-the-Loop Need
    conflict_eval = check_policy_conflicts_and_uncertainty(f"{title} {description}", domain)

    # Multi-Step Action Plan
    plan_steps = [
        f"1. Deconstruct request intent & identify institutional domain ({domain} - {category})",
        f"2. Retrieve and cross-reference institutional policy constraints ({', '.join(p['id'] for p in policies) if policies else 'Standard Operating Procedures'})",
        "3. Evaluate safety risk and consequential impact threshold",
    ]

    if conflict_eval["requires_hitl"]:
        plan_steps.append("4. 🚨 Consequential Action Gate: Pause autonomous execution & route for Administrator Human Approval")
        plan_steps.append("5. Upon human signature, dispatch execution and record audit trail")
    else:
        plan_steps.append("4. Autonomous execution authorized: Dispatch service order directly")
        plan_steps.append("5. Issue tracking ticket and commit immutable audit log")

    # Short summary
    cleaned_desc = description.strip().replace("\n", " ")
    summary = cleaned_desc[:120] + "..." if len(cleaned_desc) > 120 else cleaned_desc

    return {
        "domain": domain,
        "category": category,
        "priority": priority,
        "summary": summary,
        "detected_language": lang,
        "plan_steps": plan_steps,
        "policy_citations": citations,
        "requires_hitl": conflict_eval["requires_hitl"],
        "hitl_reasons": conflict_eval["hitl_reasons"],
        "has_conflict": conflict_eval["has_policy_conflict"],
        "conflicts": conflict_eval["conflicts"],
        "is_ai_fallback": True,
    }


def plan_and_execute_agentic_service(title: str, description: str, preferred_domain: str = None) -> dict:
    """
    Full Agentic AI Reasoning Pipeline for SOAIDEATHON-S1:
    1. Multilingual parsing & intent decomposition
    2. Institutional Policy Retrieval (RAG)
    3. Conflict & Uncertainty Detection
    4. Consequential Action Risk Assessment (HITL Gate)
    5. Action Execution Graph Planning
    """
    lang = detect_language(f"{title} {description}")

    # Prompt Ollama with structured schema
    prompt = f"""You are the central Agentic AI Orchestrator for an autonomous Institutional Service Delivery platform at SOA University.
Analyze the following student/faculty service request:

Title: {title}
Description: {description}
Input Language: {lang}

Tasks:
1. "domain": Must be strictly one of ["Grievance", "Certificate", "Maintenance", "LabBooking"].
2. "category": Specific subcategory (e.g. "Bonafide Certificate", "Hostel Plumbing", "GPU Cluster", "Scholarship Delay", "Exam Re-evaluation").
3. "priority": Strictly one of ["Low", "Medium", "High", "Urgent"].
4. "summary": Concise 1-2 sentence executive summary of the issue.
5. "plan_steps": A step-by-step array of 4-5 actions the agent will take to resolve this request.
6. "requires_hitl": Boolean (true if this is a consequential action like issuing a certificate, spending budget, safety hazard, or escalating; false if routine autonomous action).
7. "hitl_reason": Short explanation of why human administrative approval is needed (or null if false).

Output ONLY valid JSON matching this schema:
{{
    "domain": "Certificate",
    "category": "Bonafide Certificate",
    "priority": "High",
    "summary": "Student requests urgent bonafide certificate for passport verification.",
    "plan_steps": [
        "1. Parse student identity and purpose",
        "2. Cross-verify minimum 75% attendance criteria against ERP",
        "3. Route to Registrar for digital signature approval (HITL)",
        "4. Generate verifiable PDF certificate upon approval",
        "5. Notify student and log immutable audit trail"
    ],
    "requires_hitl": true,
    "hitl_reason": "Certificate issuance requires Registrar/HOD digital authorization."
}}
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
            "num_predict": 200,
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
        if response.status_code == 200:
            result = response.json()
            raw_text = result.get("response", "").strip()

            if "```json" in raw_text:
                match = re.search(r"```json\s*(.*?)\s*```", raw_text, re.DOTALL)
                if match:
                    raw_text = match.group(1).strip()
            elif "```" in raw_text:
                match = re.search(r"```\s*(.*?)\s*```", raw_text, re.DOTALL)
                if match:
                    raw_text = match.group(1).strip()

            data = json.loads(raw_text)

            domain = data.get("domain", preferred_domain or "Grievance")
            if domain not in VALID_DOMAINS:
                domain = preferred_domain or "Grievance"

            category = data.get("category", "General")
            priority = data.get("priority", "Medium")
            if priority not in VALID_PRIORITIES:
                priority = "Medium"

            summary = data.get("summary", title)
            plan_steps = data.get("plan_steps", [
                "1. Intake request & verify institutional credentials",
                "2. Check policy compliance",
                "3. Execute service workflow",
                "4. Commit action to audit trail"
            ])

            # Cross-reference with verified institutional policies
            policies = retrieve_relevant_policies(f"{title} {description}", domain)
            citations = [{"code": p["id"], "title": p["title"], "rule": p["content"]} for p in policies]

            conflict_eval = check_policy_conflicts_and_uncertainty(f"{title} {description}", domain)

            requires_hitl = data.get("requires_hitl", False) or conflict_eval["requires_hitl"]
            hitl_reason = data.get("hitl_reason") or (conflict_eval["hitl_reasons"][0] if conflict_eval["hitl_reasons"] else None)

            return {
                "domain": domain,
                "category": category,
                "priority": priority,
                "summary": summary,
                "detected_language": lang,
                "plan_steps": plan_steps,
                "policy_citations": citations,
                "requires_hitl": requires_hitl,
                "hitl_reasons": [hitl_reason] if hitl_reason else [],
                "has_conflict": conflict_eval["has_policy_conflict"],
                "conflicts": conflict_eval["conflicts"],
                "is_ai_fallback": False,
            }
    except Exception as e:
        logger.warning(f"Ollama agentic planning error: {e}. Using intelligent fallback.")

    return _agentic_heuristic_fallback(title, description, preferred_domain)


# Backward compatibility helper
def analyze_grievance(title: str, description: str) -> dict:
    res = plan_and_execute_agentic_service(title, description, "Grievance")
    return {
        "category": res["category"],
        "priority": res["priority"] if res["priority"] in ["Low", "Medium", "High"] else "High",
        "summary": res["summary"],
        "is_ai_fallback": res["is_ai_fallback"],
    }