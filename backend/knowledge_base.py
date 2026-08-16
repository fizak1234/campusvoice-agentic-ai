"""
Institutional Policy Knowledge Base & Conflict Detection Engine
Verified rules for SOA University / Institutional Service Delivery.
"""

INSTITUTIONAL_POLICIES = [
    # ---------------- Certificate Policies ----------------
    {
        "id": "POL-CERT-01",
        "domain": "Certificate",
        "title": "Bonafide & Character Certificate Issuance Policy",
        "content": "Bonafide and Character certificates require a verified minimum 75% semester attendance and no disciplinary hold. Consequential action: Requires Registrar/HOD digital approval before official seal issuance. Standard processing SLA: 24-48 hours.",
        "consequential": True,
        "keywords": ["bonafide", "character certificate", "study certificate", "attendance"],
    },
    {
        "id": "POL-CERT-02",
        "domain": "Certificate",
        "title": "Official Transcript & NOC Issuance",
        "content": "Official transcripts and No Objection Certificates (NOC) require clearance of all semester tuition fees and library books. Consequential action: Requires Academic Section verification. Issued with cryptographic verification stamp.",
        "consequential": True,
        "keywords": ["transcript", "noc", "no objection", "grade sheet", "marksheet"],
    },

    # ---------------- Maintenance Policies ----------------
    {
        "id": "POL-MAINT-01",
        "domain": "Maintenance",
        "title": "Hostel & Campus Emergency Maintenance SLA",
        "content": "Water supply failure, electrical short circuits, or sewer leaks are designated as Emergency Priority. The Estate Office dispatches duty technicians within 2 hours. Routine furniture or lighting repairs are scheduled within 24 hours.",
        "consequential": False,
        "keywords": ["water", "electric", "leak", "hostel", "cooler", "light", "plumbing", "fan", "ac"],
    },
    {
        "id": "POL-MAINT-02",
        "domain": "Maintenance",
        "title": "High-Value Campus Asset Replacement",
        "content": "Equipment replacement costing over ₹5,000 (such as lab air conditioners, main switchboards, or server UPS) requires Dean/Estate Officer budget authorization before purchasing.",
        "consequential": True,
        "keywords": ["replace", "broken server", "expensive", "equipment replacement", "switchboard"],
    },

    # ---------------- Laboratory Booking Policies ----------------
    {
        "id": "POL-LAB-01",
        "domain": "LabBooking",
        "title": "High-Performance GPU Cluster & AI Lab Access",
        "content": "GPU Lab (NVIDIA A100/H100 clusters) slots are permitted between 08:00 AM and 09:00 PM for enrolled project students. Maximum booking duration: 4 hours per slot. Booking during overnight maintenance hours (10:00 PM - 06:00 AM) is strictly prohibited.",
        "consequential": False,
        "keywords": ["gpu", "ai lab", "cluster", "cuda", "deep learning", "workstation"],
    },
    {
        "id": "POL-LAB-02",
        "domain": "LabBooking",
        "title": "Chemical & Advanced Robotics Lab Safety Clearance",
        "content": "Access to hazardous chemical synthesis or industrial robotics testbeds requires Lab In-Charge safety approval and presence of a certified lab assistant. Consequential action: Human approval required.",
        "consequential": True,
        "keywords": ["chemical", "chemistry", "robotics", "hazardous", "laser", "cleanroom"],
    },

    # ---------------- Grievance Policies ----------------
    {
        "id": "POL-GRIEV-01",
        "domain": "Grievance",
        "title": "Academic & Evaluation Grievance Redressal",
        "content": "Grade discrepancies or re-evaluation requests must be filed within 15 days of result declaration. Discrepancies between physical marksheet and ERP portal are prioritized for Controller of Examinations review.",
        "consequential": False,
        "keywords": ["exam", "marks", "grade", "re-evaluation", "portal error", "backlog"],
    },
    {
        "id": "POL-GRIEV-02",
        "domain": "Grievance",
        "title": "Scholarship & Financial Aid Escalation",
        "content": "Delayed government or institutional scholarship funds approved over 60 days ago must be escalated directly to the University Finance Officer with state application reference.",
        "consequential": True,
        "keywords": ["scholarship", "financial aid", "stipend", "disbursement", "fee refund"],
    },
]


def retrieve_relevant_policies(text: str, domain: str = None) -> list:
    """Retrieves verified institutional policy citations relevant to the user request."""
    query = text.lower()
    matches = []

    for policy in INSTITUTIONAL_POLICIES:
        score = 0
        if domain and policy["domain"].lower() == domain.lower():
            score += 3

        for kw in policy["keywords"]:
            if kw in query:
                score += 2

        if score > 0:
            matches.append((score, policy))

    matches.sort(key=lambda x: x[0], reverse=True)
    return [m[1] for m in matches[:3]]


def check_policy_conflicts_and_uncertainty(text: str, domain: str) -> dict:
    """
    Evaluates whether the request violates any institutional constraints,
    contains ambiguities, or requires human-in-the-loop approval.
    """
    query = text.lower()
    conflicts = []
    uncertainties = []
    consequential_reasons = []

    # Check Lab Booking timing violations
    if "lab" in domain.lower() or "booking" in domain.lower():
        if any(w in query for w in ["midnight", "11 pm", "12 am", "2 am", "3 am", "night slot", "overnight"]):
            conflicts.append("Policy POL-LAB-01 violation: Lab operations are strictly prohibited during maintenance hours (10:00 PM - 06:00 AM).")

    # Check Attendance / Disciplinary ambiguity for Certificates
    if "certificate" in domain.lower():
        consequential_reasons.append("Certificate issuance requires Registrar/HOD digital verification per institutional policy POL-CERT-01.")
        if not any(w in query for w in ["roll", "reg", "id", "semester", "year", "branch", "purpose"]):
            uncertainties.append("Missing student enrollment specifics or purpose of certificate.")

    # Check High-Value Maintenance
    if "maintenance" in domain.lower():
        if any(w in query for w in ["replace", "new unit", "buy", "purchase", "burned out completely"]):
            consequential_reasons.append("High-value equipment replacement requires Estate Officer budget sign-off per POL-MAINT-02.")

    # Check Grievance Escalations
    if "grievance" in domain.lower():
        if any(w in query for w in ["scholarship", "fee", "refund", "harassment", "urgent"]):
            consequential_reasons.append("High-impact financial/disciplinary grievance requires administrative escalation.")

    has_conflict = len(conflicts) > 0
    has_uncertainty = len(uncertainties) > 0
    requires_hitl = len(consequential_reasons) > 0 or has_conflict

    return {
        "has_policy_conflict": has_conflict,
        "conflicts": conflicts,
        "has_uncertainty": has_uncertainty,
        "uncertainties": uncertainties,
        "requires_hitl": requires_hitl,
        "hitl_reasons": consequential_reasons,
    }
