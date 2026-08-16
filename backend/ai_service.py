import os
import re
import json
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "30"))

VALID_CATEGORIES = ["Academic", "Scholarship", "Hostel", "Examination", "Fees", "Other"]
VALID_PRIORITIES = ["Low", "Medium", "High"]


def check_ollama_status() -> dict:
    """Checks whether the local Ollama service is reachable and has the required model."""
    try:
        base_url = OLLAMA_URL.rsplit("/api/", 1)[0]
        tags_url = f"{base_url}/api/tags"
        response = requests.get(tags_url, timeout=3)
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


def _heuristic_fallback(title: str, description: str) -> dict:
    """Fallback classifier when Ollama is unreachable or returns invalid format."""
    text = f"{title} {description}".lower()

    # Category heuristics
    if any(k in text for k in ["scholarship", "fellowship", "stipend", "grant", "financial aid", "nsp"]):
        category = "Scholarship"
    elif any(k in text for k in ["hostel", "room", "mess", "warden", "dorm", "bed", "bathroom", "water", "electricity"]):
        category = "Hostel"
    elif any(k in text for k in ["exam", "hall ticket", "re-eval", "grade", "marks", "result", "semester", "backlog", "admit card"]):
        category = "Examination"
    elif any(k in text for k in ["fee", "payment", "dues", "tuition", "challan", "refund", "receipt", "fine"]):
        category = "Fees"
    elif any(k in text for k in ["professor", "faculty", "class", "lecture", "attendance", "course", "syllabus", "lab", "assignment", "teacher", "academic"]):
        category = "Academic"
    else:
        category = "Other"

    # Priority heuristics
    if any(k in text for k in ["urgent", "emergency", "immediately", "severe", "threat", "harassment", "hospital", "deadline today", "failed payment", "debarred"]):
        priority = "High"
    elif any(k in text for k in ["important", "delayed", "not received", "pending for months", "issue", "problem", "broken"]):
        priority = "High" if "three months" in text or "long time" in text else "Medium"
    elif any(k in text for k in ["minor", "query", "question", "feedback", "suggestion"]):
        priority = "Low"
    else:
        priority = "Medium"

    # Clean short summary
    cleaned_desc = description.strip().replace("\n", " ")
    if len(cleaned_desc) > 120:
        summary = cleaned_desc[:117] + "..."
    else:
        summary = cleaned_desc if cleaned_desc else f"Grievance regarding {title}"

    return {
        "category": category,
        "priority": priority,
        "summary": summary,
        "is_ai_fallback": True,
    }


def _normalize_category(val: str) -> str:
    if not val:
        return "Other"
    for cat in VALID_CATEGORIES:
        if cat.lower() == val.strip().lower():
            return cat
    return "Other"


def _normalize_priority(val: str) -> str:
    if not val:
        return "Medium"
    for prio in VALID_PRIORITIES:
        if prio.lower() == val.strip().lower():
            return prio
    return "Medium"


def analyze_grievance(title: str, description: str) -> dict:
    """
    Sends grievance title & description to local Ollama Llama 3.2 3B model.
    Parses and returns:
        {
            "category": "Academic" | "Scholarship" | "Hostel" | "Examination" | "Fees" | "Other",
            "priority": "Low" | "Medium" | "High",
            "summary": "Short concise summary string",
            "is_ai_fallback": bool
        }
    """
    prompt = f"""You are an expert AI assistant for a College Grievance Management System.
Analyze the following college student grievance and output a structured JSON assessment.

Title: {title}
Description: {description}

Requirements:
1. "category": Must be strictly one of ["Academic", "Scholarship", "Hostel", "Examination", "Fees", "Other"].
2. "priority": Must be strictly one of ["Low", "Medium", "High"] based on urgency, academic impact, or safety/financial distress.
3. "summary": A clear, concise 1-2 sentence professional summary of the student's issue.

Output ONLY valid JSON matching this structure without any markdown explanations:
{{
    "category": "Scholarship",
    "priority": "High",
    "summary": "Student has not received their approved scholarship payment for three months."
}}
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
        }
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=OLLAMA_TIMEOUT
        )

        if response.status_code == 200:
            result = response.json()
            raw_text = result.get("response", "").strip()

            # Clean any potential markdown wrapping
            if "```json" in raw_text:
                match = re.search(r"```json\s*(.*?)\s*```", raw_text, re.DOTALL)
                if match:
                    raw_text = match.group(1).strip()
            elif "```" in raw_text:
                match = re.search(r"```\s*(.*?)\s*```", raw_text, re.DOTALL)
                if match:
                    raw_text = match.group(1).strip()

            data = json.loads(raw_text)

            cat = _normalize_category(data.get("category", ""))
            prio = _normalize_priority(data.get("priority", ""))
            summary = data.get("summary", "").strip() or f"Grievance concerning {title}"

            return {
                "category": cat,
                "priority": prio,
                "summary": summary,
                "is_ai_fallback": False,
            }
        else:
            logger.warning(f"Ollama returned non-200 status {response.status_code}: {response.text}")
    except requests.RequestException as e:
        logger.warning(f"Ollama connection error: {e}. Utilizing smart fallback.")
    except Exception as e:
        logger.error(f"Error parsing Ollama output: {e}. Utilizing smart fallback.")

    # Graceful heuristic fallback
    return _heuristic_fallback(title, description)