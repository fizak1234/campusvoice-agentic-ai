import React, { useState, useEffect, useMemo } from "react";
import axios from "axios";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// Domain Categories & Definitions for SOAIDEATHON-S1
const DOMAINS = [
  { id: "Certificate", icon: "📜", label: "Certificate Issuance", desc: "Bonafide, Transcripts, NOC & Character Certificates" },
  { id: "Maintenance", icon: "🔧", label: "Maintenance & Facilities", desc: "Hostel, Electrical, Plumbing & Campus repairs" },
  { id: "LabBooking", icon: "🔬", label: "Laboratory Bookings", desc: "GPU AI Clusters, Robotics & Research testbeds" },
  { id: "Grievance", icon: "⚖️", label: "Grievance Escalation", desc: "Academic, Scholarship & Evaluation redressal" },
];

const TEMPLATES = {
  Certificate: [
    {
      label: "Urgent Bonafide Certificate (Visa)",
      title: "Urgent Bonafide Certificate for US Visa Appointment",
      desc: "I have a US Visa interview scheduled this Friday and require an official Bonafide Certificate stating my full-time enrollment in 6th Sem B.Tech CSE. Roll No: 220101489.",
    },
    {
      label: "Official Transcript for Higher Studies",
      title: "Consolidated Grade Transcript for University Application",
      desc: "Requesting consolidated semester 1-6 official transcripts with university seal for master's degree application. All library and tuition dues cleared.",
    },
    {
      label: "NOC for Summer Internship (Bilingual/Hinglish)",
      title: "No Objection Certificate for Research Internship",
      desc: "Mujhe DRDO summer internship ke liye college se official NOC chahiye. Duration: June 15 to August 10. HoD approval attached.",
    },
  ],
  Maintenance: [
    {
      label: "Hostel B Water Outage (Emergency)",
      title: "Hostel Block B 3rd Floor drinking water cooler malfunction",
      desc: "Water cooler pipe burst on 3rd floor of Hostel B, flooding the corridor and cutting off drinking supply for 45 students.",
    },
    {
      label: "Lab AC Overheating Failure",
      title: "AI Lab 4 Main Air Conditioner Failure and Smoke",
      desc: "The primary 3-ton AC unit in AI Lab 4 stopped functioning and is emitting electrical smoke, causing GPU server racks to overheat.",
    },
  ],
  LabBooking: [
    {
      label: "4-Hour GPU Cluster Slot",
      title: "NVIDIA A100 GPU Cluster Slot for Llama 3.2 Fine-Tuning",
      desc: "Requesting reservation on GPU Node 02 from 2:00 PM to 6:00 PM for distributed deep learning capstone project training.",
    },
    {
      label: "Robotics Testbed Reservation",
      title: "Industrial Robotic Arm Testbed Access for Kinematics Lab",
      desc: "Requesting slot for 6-DOF robotic manipulator testing on Wednesday from 10:00 AM to 1:00 PM under Dr. Mishra's supervision.",
    },
  ],
  Grievance: [
    {
      label: "Scholarship Delayed 3 Months",
      title: "Approved Merit Scholarship not credited for 3 months",
      desc: "State Merit scholarship was approved on 14th May (App ID: NSP-2026-9014) but funds of ₹25,000 have not been disbursed by university finance office.",
    },
    {
      label: "Exam Mark Mismatch on ERP",
      title: "Re-evaluation grade mismatch in Operating Systems (CS302)",
      desc: "Physical re-evaluation marksheet shows revised 82/100, but online ERP portal still displays failing grade of 38.",
    },
  ],
};

export default function App() {
  // Auth State
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [user, setUser] = useState(null);
  const [isRegistering, setIsRegistering] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);

  // Form Fields for Auth
  const [authName, setAuthName] = useState("");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authRole, setAuthRole] = useState("user");

  // System Health
  const [systemStatus, setSystemStatus] = useState(null);
  const [knowledgeBase, setKnowledgeBase] = useState([]);

  // Selected Service Domain Tab
  const [activeDomain, setActiveDomain] = useState("Certificate");

  // Service Request Submission
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [agentSimulation, setAgentSimulation] = useState(null);
  const [simulating, setSimulating] = useState(false);

  // Lists & State
  const [serviceRequests, setServiceRequests] = useState([]);
  const [pendingHITL, setPendingHITL] = useState([]);
  const [loadingRequests, setLoadingRequests] = useState(false);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState("");
  const [filterDomain, setFilterDomain] = useState("All");
  const [filterStatus, setFilterStatus] = useState("All");

  // Navigation Mode (for Admin: 'hitl', 'all_requests', 'student_view', 'knowledge_base')
  const [adminTab, setAdminTab] = useState("hitl");

  // Selected Request for Full Auditable Action Trail Modal
  const [selectedAuditTrail, setSelectedAuditTrail] = useState(null);
  const [auditLoading, setAuditLoading] = useState(false);

  // HITL Decision Modal or Inline
  const [hitlNotes, setHitlNotes] = useState("");

  // Toast Notifications
  const [toasts, setToasts] = useState([]);

  const showToast = (message, type = "info") => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  };

  // -------------------------------------------------------------
  // Initial Lifecycle: Verify Session & Fetch Data
  // -------------------------------------------------------------
  useEffect(() => {
    fetchSystemStatus();
    fetchKnowledgeBase();
    if (token) {
      fetchCurrentUser(token);
    }
  }, [token]);

  const fetchSystemStatus = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/system-status`);
      setSystemStatus(res.data);
    } catch {
      setSystemStatus({ database_connected: false, ollama: { available: false } });
    }
  };

  const fetchKnowledgeBase = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/knowledge-base`);
      setKnowledgeBase(res.data.policies || []);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchCurrentUser = async (authToken) => {
    try {
      const res = await axios.get(`${API_BASE}/users/me`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      setUser(res.data);
      if (res.data.role === "admin") {
        fetchPendingHITL(authToken);
      }
      fetchServiceRequests(authToken);
    } catch {
      handleLogout();
    }
  };

  const fetchServiceRequests = async (authToken = token) => {
    if (!authToken) return;
    setLoadingRequests(true);
    try {
      const res = await axios.get(`${API_BASE}/api/service-requests`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      setServiceRequests(res.data.requests || []);
    } catch (err) {
      console.error("Error fetching service requests:", err);
    } finally {
      setLoadingRequests(false);
    }
  };

  const fetchPendingHITL = async (authToken = token) => {
    if (!authToken) return;
    try {
      const res = await axios.get(`${API_BASE}/api/hitl/pending`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      setPendingHITL(res.data.pending_approvals || []);
    } catch (err) {
      console.error("Error fetching pending HITL:", err);
    }
  };

  // -------------------------------------------------------------
  // Auth Handlers
  // -------------------------------------------------------------
  const handleLogin = async (e, customEmail, customPass) => {
    if (e) e.preventDefault();
    setAuthLoading(true);

    const emailToUse = customEmail || authEmail;
    const passToUse = customPass || authPassword;

    try {
      const res = await axios.post(`${API_BASE}/login`, {
        email: emailToUse,
        password: passToUse,
      });

      const authToken = res.data.access_token;
      localStorage.setItem("token", authToken);
      setToken(authToken);
      setUser(res.data.user);
      showToast(`Welcome back, ${res.data.user.name}!`, "success");

      if (res.data.user.role === "admin") {
        fetchPendingHITL(authToken);
      }
      fetchServiceRequests(authToken);
      fetchSystemStatus();
    } catch (err) {
      showToast(err.response?.data?.detail || "Login failed.", "error");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setAuthLoading(true);

    try {
      await axios.post(`${API_BASE}/register`, {
        name: authName,
        email: authEmail,
        password: authPassword,
        role: authRole,
      });

      showToast("Account registered! Logging in...", "success");
      await handleLogin(null, authEmail, authPassword);
      setAuthName("");
      setAuthEmail("");
      setAuthPassword("");
      setIsRegistering(false);
    } catch (err) {
      showToast(err.response?.data?.detail || "Registration failed.", "error");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    setToken("");
    setUser(null);
    setServiceRequests([]);
    setPendingHITL([]);
    showToast("Signed out successfully.", "info");
  };

  // -------------------------------------------------------------
  // Agentic AI Execution & Submission
  // -------------------------------------------------------------
  const handleSimulateAgent = async () => {
    if (!title || !description) {
      showToast("Please enter a title and description to simulate Agentic AI planning.", "error");
      return;
    }
    setSimulating(true);
    try {
      const res = await axios.post(`${API_BASE}/ai/analyze`, {
        title,
        description,
      });
      setAgentSimulation(res.data.analysis);
      showToast("Agentic AI multi-step plan & policy constraints resolved!", "success");
    } catch {
      showToast("Simulation failed.", "error");
    } finally {
      setSimulating(false);
    }
  };

  const handleSubmitServiceRequest = async (e) => {
    e.preventDefault();
    if (!title || !description) return;

    setSubmitting(true);
    try {
      const res = await axios.post(
        `${API_BASE}/api/agent/submit`,
        {
          title,
          description,
          domain: activeDomain,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const created = res.data.request;
      showToast(
        created.requires_hitl
          ? "🚨 Consequential Action Gate Triggered: Routed for Administrator Approval!"
          : "✓ Autonomous Workflow Dispatched Successfully!",
        "success"
      );

      setTitle("");
      setDescription("");
      setAgentSimulation(null);

      fetchServiceRequests(token);
      if (user?.role === "admin") {
        fetchPendingHITL(token);
      }
      fetchSystemStatus();

      // Open audit trail for the created request
      handleOpenAuditTrail(created.id);
    } catch (err) {
      showToast(err.response?.data?.detail || "Submission failed.", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const handleApplyTemplate = (tmpl) => {
    setTitle(tmpl.title);
    setDescription(tmpl.desc);
    setAgentSimulation(null);
  };

  // -------------------------------------------------------------
  // HITL Decision Handler (Admin Only)
  // -------------------------------------------------------------
  const handleHITLDecision = async (requestId, decision) => {
    try {
      const res = await axios.post(
        `${API_BASE}/api/hitl/decide`,
        {
          request_id: requestId,
          decision,
          notes: hitlNotes || `Decision marked as ${decision} by ${user.name}.`,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      showToast(`Decision '${decision}' executed for Request #${requestId}!`, "success");
      setHitlNotes("");

      fetchPendingHITL(token);
      fetchServiceRequests(token);
      fetchSystemStatus();

      if (selectedAuditTrail && selectedAuditTrail.request_id === requestId) {
        handleOpenAuditTrail(requestId);
      }
    } catch (err) {
      showToast(err.response?.data?.detail || "Action failed.", "error");
    }
  };

  // -------------------------------------------------------------
  // Audit Trail Inspector
  // -------------------------------------------------------------
  const handleOpenAuditTrail = async (requestId) => {
    setAuditLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/api/audit-trail/${requestId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSelectedAuditTrail(res.data);
    } catch (err) {
      showToast("Could not retrieve audit trail.", "error");
    } finally {
      setAuditLoading(false);
    }
  };

  // -------------------------------------------------------------
  // Filtered List Memo
  // -------------------------------------------------------------
  const filteredRequests = useMemo(() => {
    return serviceRequests.filter((r) => {
      const matchesSearch =
        searchQuery === "" ||
        r.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.student_name?.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesDomain = filterDomain === "All" || r.request_type === filterDomain;
      const matchesStatus = filterStatus === "All" || r.status === filterStatus;

      return matchesSearch && matchesDomain && matchesStatus;
    });
  }, [serviceRequests, searchQuery, filterDomain, filterStatus]);

  // Statistics
  const stats = useMemo(() => {
    return {
      total: serviceRequests.length,
      hitlPending: serviceRequests.filter((r) => r.status === "Awaiting Human Approval").length,
      inProgress: serviceRequests.filter((r) => r.status === "In Progress").length,
      executed: serviceRequests.filter((r) => ["Executed", "Approved", "Resolved"].includes(r.status)).length,
    };
  }, [serviceRequests]);

  // Badges
  const renderStatusBadge = (st) => {
    let cls = "badge-status-pending";
    if (st === "Awaiting Human Approval") cls = "badge-status-hitl";
    else if (st === "In Progress") cls = "badge-status-inprogress";
    else if (["Executed", "Approved", "Resolved"].includes(st)) cls = "badge-status-executed";
    else if (st === "Rejected") cls = "badge-status-rejected";

    return (
      <span className={`badge ${cls}`}>
        {st === "Awaiting Human Approval" && "🚨 "}
        {st === "Executed" && "✓ "}
        {st}
      </span>
    );
  };

  const renderPriorityBadge = (prio) => {
    let cls = "badge-prio-medium";
    if (prio === "Urgent" || prio === "High") cls = "badge-prio-urgent";
    if (prio === "Low") cls = "badge-prio-low";

    return (
      <span className={`badge ${cls}`}>
        {prio === "Urgent" && "⚡ "}
        {prio}
      </span>
    );
  };

  // -------------------------------------------------------------
  // RENDER: Auth Screen
  // -------------------------------------------------------------
  if (!user) {
    return (
      <div className="app-container">
        <header className="navbar">
          <div className="nav-brand">
            <div className="brand-icon">🏛️</div>
            <div>
              <div className="brand-title">
                CampusVoice Agentic AI
                <span className="hackathon-badge">SOAIDEATHON-S1</span>
              </div>
              <div className="brand-sub">Human-in-the-Loop Autonomous Institutional Service Delivery</div>
            </div>
          </div>

          <div className="nav-actions">
            <div className="system-status-pill">
              <span className={`status-dot ${systemStatus?.ollama?.available ? "" : "warning"}`}></span>
              <span>Ollama {systemStatus?.ollama?.model || "Llama 3.2 3B"}</span>
            </div>
          </div>
        </header>

        <div className="auth-wrapper">
          <div className="auth-card animate-fade-in">
            <div className="auth-header">
              <h1>{isRegistering ? "Register Institutional Account" : "Agentic Portal Login"}</h1>
              <p>Autonomous Institutional Service Delivery with Human-in-the-Loop Safeguards</p>
            </div>

            <div className="demo-credentials-banner">
              <div className="demo-title">⚡ Instant Demo Logins (Click to Test)</div>
              <div className="demo-buttons">
                <button
                  type="button"
                  className="demo-btn"
                  onClick={() => handleLogin(null, "student@college.edu", "student123")}
                  disabled={authLoading}
                >
                  🎓 Student Demo (Aarav)
                </button>
                <button
                  type="button"
                  className="demo-btn"
                  onClick={() => handleLogin(null, "admin@college.edu", "admin123")}
                  disabled={authLoading}
                >
                  🛡️ Dean / Admin (HITL)
                </button>
              </div>
            </div>

            <div className="auth-tabs">
              <button
                type="button"
                className={`auth-tab ${!isRegistering ? "active" : ""}`}
                onClick={() => setIsRegistering(false)}
              >
                Sign In
              </button>
              <button
                type="button"
                className={`auth-tab ${isRegistering ? "active" : ""}`}
                onClick={() => setIsRegistering(true)}
              >
                Create Account
              </button>
            </div>

            {!isRegistering ? (
              <form onSubmit={handleLogin}>
                <div className="form-group">
                  <label>Institutional Email</label>
                  <input
                    type="email"
                    className="form-control"
                    placeholder="student@college.edu or admin@college.edu"
                    value={authEmail}
                    onChange={(e) => setAuthEmail(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Password</label>
                  <input
                    type="password"
                    className="form-control"
                    placeholder="Enter password"
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                    required
                  />
                </div>

                <button type="submit" className="btn-primary" disabled={authLoading}>
                  {authLoading ? "Authenticating..." : "Sign In to Platform"}
                </button>
              </form>
            ) : (
              <form onSubmit={handleRegister}>
                <div className="form-group">
                  <label>Full Name</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. Aarav Sharma"
                    value={authName}
                    onChange={(e) => setAuthName(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Institutional Email</label>
                  <input
                    type="email"
                    className="form-control"
                    placeholder="student@college.edu"
                    value={authEmail}
                    onChange={(e) => setAuthEmail(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Password</label>
                  <input
                    type="password"
                    className="form-control"
                    placeholder="At least 6 characters"
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Account Role</label>
                  <select
                    className="form-control"
                    value={authRole}
                    onChange={(e) => setAuthRole(e.target.value)}
                  >
                    <option value="user">Student / Researcher</option>
                    <option value="admin">Administrator / Registrar / Dean (HITL Approver)</option>
                  </select>
                </div>

                <button type="submit" className="btn-primary" disabled={authLoading}>
                  {authLoading ? "Creating Account..." : "Register Account"}
                </button>
              </form>
            )}
          </div>
        </div>

        <div className="toast-container">
          {toasts.map((t) => (
            <div key={t.id} className={`toast ${t.type}`}>
              {t.message}
            </div>
          ))}
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // RENDER: Logged In Dashboard
  // -------------------------------------------------------------
  return (
    <div className="app-container">
      {/* Top Navbar */}
      <header className="navbar">
        <div className="nav-brand">
          <div className="brand-icon">🏛️</div>
          <div>
            <div className="brand-title">
              CampusVoice Agentic AI
              <span className="hackathon-badge">SOAIDEATHON-S1</span>
            </div>
            <div className="brand-sub">Human-in-the-Loop Autonomous Service Delivery</div>
          </div>
        </div>

        <div className="nav-actions">
          <div className="system-status-pill" title="Local Ollama AI Inference Engine">
            <span className={`status-dot ${systemStatus?.ollama?.available ? "" : "warning"}`}></span>
            <span>Ollama {systemStatus?.ollama?.model || "Llama 3.2 3B"}</span>
          </div>

          {/* Admin Navigation Tabs */}
          {user.role === "admin" && (
            <div className="auth-tabs" style={{ margin: 0, padding: "2px" }}>
              <button
                type="button"
                className={`auth-tab ${adminTab === "hitl" ? "active" : ""}`}
                style={{ padding: "0.3rem 0.75rem", fontSize: "0.75rem" }}
                onClick={() => setAdminTab("hitl")}
              >
                🚨 HITL Queue ({pendingHITL.length})
              </button>
              <button
                type="button"
                className={`auth-tab ${adminTab === "all_requests" ? "active" : ""}`}
                style={{ padding: "0.3rem 0.75rem", fontSize: "0.75rem" }}
                onClick={() => setAdminTab("all_requests")}
              >
                📋 All Requests
              </button>
              <button
                type="button"
                className={`auth-tab ${adminTab === "knowledge_base" ? "active" : ""}`}
                style={{ padding: "0.3rem 0.75rem", fontSize: "0.75rem" }}
                onClick={() => setAdminTab("knowledge_base")}
              >
                📖 Knowledge Base
              </button>
              <button
                type="button"
                className={`auth-tab ${adminTab === "student_view" ? "active" : ""}`}
                style={{ padding: "0.3rem 0.75rem", fontSize: "0.75rem" }}
                onClick={() => setAdminTab("student_view")}
              >
                ✍️ Submit Request
              </button>
            </div>
          )}

          {/* User Profile */}
          <div className="user-profile-pill">
            <div className={`user-avatar ${user.role === "admin" ? "admin" : ""}`}>
              {user.name?.charAt(0).toUpperCase()}
            </div>
            <div className="user-info">
              <span className="user-name">{user.name}</span>
              <span className={`role-badge ${user.role === "admin" ? "admin" : ""}`}>
                {user.role === "admin" ? "HITL Approver" : "Student"}
              </span>
            </div>
          </div>

          <button type="button" className="btn-secondary-sm" onClick={handleLogout}>
            Sign Out
          </button>
        </div>
      </header>

      <main className="main-content">
        {/* HITL Alert Banner if Admin has pending actions */}
        {user.role === "admin" && pendingHITL.length > 0 && adminTab !== "hitl" && (
          <div className="hitl-alert-banner animate-fade-in">
            <div>
              <div className="hitl-alert-title">
                <span>🚨</span> {pendingHITL.length} Consequential Action(s) Require Human Approval
              </div>
              <div className="hitl-alert-desc">
                High-impact certificate issuance, budget allocations, or safety clearances paused at HITL gates.
              </div>
            </div>
            <button
              type="button"
              className="btn-primary"
              style={{ width: "auto", padding: "0.5rem 1.25rem", background: "#f43f5e" }}
              onClick={() => setAdminTab("hitl")}
            >
              Review HITL Queue →
            </button>
          </div>
        )}

        {/* Metrics Grid */}
        <section className="metrics-grid">
          <div className="metric-card">
            <div>
              <div className="metric-label">Total Service Requests</div>
              <div className="metric-value">{stats.total}</div>
            </div>
            <div className="metric-icon blue">📁</div>
          </div>

          <div className="metric-card">
            <div>
              <div className="metric-label">🚨 HITL Human Approvals</div>
              <div className="metric-value" style={{ color: "#fb7185" }}>
                {stats.hitlPending}
              </div>
            </div>
            <div className="metric-icon rose">⏳</div>
          </div>

          <div className="metric-card">
            <div>
              <div className="metric-label">In Autonomous Progress</div>
              <div className="metric-value">{stats.inProgress}</div>
            </div>
            <div className="metric-icon amber">⚙️</div>
          </div>

          <div className="metric-card">
            <div>
              <div className="metric-label">Executed / Verified</div>
              <div className="metric-value">{stats.executed}</div>
            </div>
            <div className="metric-icon emerald">✓</div>
          </div>
        </section>

        {/* -------------------------------------------------------------
            ADMIN VIEW: HITL APPROVAL QUEUE
        ------------------------------------------------------------- */}
        {user.role === "admin" && adminTab === "hitl" && (
          <section className="card animate-fade-in">
            <div className="card-header">
              <h2 className="card-title">
                <span>🚨</span> Human-in-the-Loop Consequential Approval Queue ({pendingHITL.length})
              </h2>
              <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                Auditable Consequential Action Safeguard
              </span>
            </div>

            {pendingHITL.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">✓</div>
                <h3>All consequential actions cleared</h3>
                <p>No requests are currently paused at Human-in-the-Loop gates.</p>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                {pendingHITL.map((req) => (
                  <div
                    key={req.id}
                    style={{
                      background: "var(--bg-card)",
                      border: "1px solid rgba(244, 63, 94, 0.35)",
                      borderRadius: "var(--radius-lg)",
                      padding: "1.5rem",
                      display: "flex",
                      flexDirection: "column",
                      gap: "1rem",
                      textAlign: "left",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                      <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.35rem" }}>
                          <span className="badge badge-domain">{req.request_type}</span>
                          <span className="badge badge-category">{req.category}</span>
                          {renderPriorityBadge(req.priority)}
                          <span className="badge badge-status-hitl">🚨 Paused at HITL Gate</span>
                        </div>
                        <h3 style={{ fontSize: "1.15rem", color: "var(--text-main)", fontWeight: 700 }}>
                          #{req.id} — {req.title}
                        </h3>
                        <div style={{ fontSize: "0.8rem", color: "var(--text-dim)" }}>
                          Requested by: <strong>{req.student_name}</strong> ({req.student_email})
                        </div>
                      </div>

                      <button
                        type="button"
                        className="btn-secondary-sm"
                        onClick={() => handleOpenAuditTrail(req.id)}
                      >
                        Inspect Audit Trail 📜
                      </button>
                    </div>

                    <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", lineHeight: 1.5 }}>
                      {req.description}
                    </p>

                    {/* Consequential Reason Alert */}
                    <div
                      style={{
                        background: "rgba(244, 63, 94, 0.1)",
                        border: "1px solid rgba(244, 63, 94, 0.25)",
                        borderRadius: "var(--radius-md)",
                        padding: "0.75rem 1rem",
                        fontSize: "0.825rem",
                        color: "#fecdd3",
                      }}
                    >
                      <strong>🚨 Reason for Human Approval:</strong> {req.hitl_reason}
                    </div>

                    {/* Agent Multi-step Plan Preview */}
                    {req.agent_plan && req.agent_plan.length > 0 && (
                      <div className="agent-plan-box" style={{ margin: 0 }}>
                        <div className="agent-plan-header">
                          <span>Multi-Step Planned Action Execution Graph</span>
                        </div>
                        {req.agent_plan.map((step, idx) => (
                          <div key={idx} className="plan-step-item">
                            <span>🔹</span> {step}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* HITL Decision Controls */}
                    <div
                      style={{
                        display: "flex",
                        flexWrap: "wrap",
                        justifyContent: "space-between",
                        alignItems: "center",
                        paddingTop: "0.85rem",
                        borderTop: "1px solid var(--border-color)",
                        gap: "0.75rem",
                      }}
                    >
                      <input
                        type="text"
                        className="form-control"
                        placeholder="Add approver verification notes (optional)..."
                        style={{ maxWidth: "380px" }}
                        value={hitlNotes}
                        onChange={(e) => setHitlNotes(e.target.value)}
                      />

                      <div style={{ display: "flex", gap: "0.5rem" }}>
                        <button
                          type="button"
                          className="btn-primary"
                          style={{ width: "auto", background: "var(--status-resolved)", padding: "0.55rem 1.25rem" }}
                          onClick={() => handleHITLDecision(req.id, "Approved")}
                        >
                          ✓ Approve & Execute Workflow
                        </button>
                        <button
                          type="button"
                          className="btn-secondary-sm"
                          onClick={() => handleHITLDecision(req.id, "Modified")}
                        >
                          ✍️ Request Modification
                        </button>
                        <button
                          type="button"
                          className="btn-secondary-sm"
                          style={{ color: "#fb7185", borderColor: "rgba(244, 63, 94, 0.3)" }}
                          onClick={() => handleHITLDecision(req.id, "Rejected")}
                        >
                          ✕ Decline Request
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {/* -------------------------------------------------------------
            ADMIN VIEW: ALL REQUESTS EXPLORER
        ------------------------------------------------------------- */}
        {user.role === "admin" && adminTab === "all_requests" && (
          <section className="card animate-fade-in">
            <div className="card-header">
              <h2 className="card-title">
                <span>📋</span> Master Institutional Service Requests ({filteredRequests.length})
              </h2>
            </div>

            <div className="filter-toolbar">
              <div className="search-input-wrapper">
                <span className="search-icon">🔍</span>
                <input
                  type="text"
                  className="search-input"
                  placeholder="Search student, title, or keyword..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              <select className="filter-select" value={filterDomain} onChange={(e) => setFilterDomain(e.target.value)}>
                <option value="All">All Service Domains</option>
                <option value="Certificate">📜 Certificate Requests</option>
                <option value="Maintenance">🔧 Maintenance Tickets</option>
                <option value="LabBooking">🔬 Lab Bookings</option>
                <option value="Grievance">⚖️ Grievance Escalation</option>
              </select>

              <select className="filter-select" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
                <option value="All">All Statuses</option>
                <option value="Awaiting Human Approval">🚨 Awaiting Human Approval</option>
                <option value="In Progress">⚙️ In Progress</option>
                <option value="Executed">✓ Executed</option>
                <option value="Rejected">✕ Rejected</option>
              </select>
            </div>

            <div className="admin-table-wrapper">
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Domain</th>
                    <th>Student</th>
                    <th>Request Title & Category</th>
                    <th>AI Priority</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRequests.map((r) => (
                    <tr key={r.id}>
                      <td><strong>#{r.id}</strong></td>
                      <td><span className="badge badge-domain">{r.request_type}</span></td>
                      <td>
                        <div style={{ display: "flex", flexDirection: "column" }}>
                          <span style={{ fontWeight: 600, color: "var(--text-main)" }}>{r.student_name}</span>
                          <span style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>{r.student_email}</span>
                        </div>
                      </td>
                      <td style={{ maxWidth: "260px" }}>
                        <div style={{ fontWeight: 600, color: "var(--text-main)", marginBottom: "3px" }}>{r.title}</div>
                        <span className="badge badge-category">{r.category}</span>
                      </td>
                      <td>{renderPriorityBadge(r.priority)}</td>
                      <td>{renderStatusBadge(r.status)}</td>
                      <td>
                        <button
                          type="button"
                          className="btn-secondary-sm"
                          onClick={() => handleOpenAuditTrail(r.id)}
                        >
                          Audit Trail 📜
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* -------------------------------------------------------------
            ADMIN VIEW: INSTITUTIONAL KNOWLEDGE BASE
        ------------------------------------------------------------- */}
        {user.role === "admin" && adminTab === "knowledge_base" && (
          <section className="card animate-fade-in">
            <div className="card-header">
              <h2 className="card-title">
                <span>📖</span> Institutional Policy Knowledge Base (RAG Rules)
              </h2>
              <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                Verified Institutional Constraints
              </span>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1rem", textAlign: "left" }}>
              {knowledgeBase.map((pol) => (
                <div key={pol.id} className="card" style={{ background: "var(--bg-card)", padding: "1.25rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                    <span className="policy-citation-pill">{pol.id}</span>
                    <span className="badge badge-domain">{pol.domain}</span>
                  </div>
                  <h4 style={{ fontSize: "0.95rem", color: "var(--text-main)", marginBottom: "0.5rem" }}>{pol.title}</h4>
                  <p style={{ fontSize: "0.825rem", color: "var(--text-muted)", lineHeight: 1.5 }}>{pol.content}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* -------------------------------------------------------------
            STUDENT PORTAL & SERVICE REQUEST LAUNCHER
        ------------------------------------------------------------- */}
        {(user.role === "user" || adminTab === "student_view") && (
          <div className="student-layout">
            {/* Request Submission Panel */}
            <section className="card animate-fade-in">
              <div className="card-header">
                <h2 className="card-title">
                  <span>🤖</span> Autonomous Service Dispatcher
                </h2>
              </div>

              {/* 4 Interactive Service Domain Tabs */}
              <div className="domain-selector-grid">
                {DOMAINS.map((d) => (
                  <button
                    key={d.id}
                    type="button"
                    className={`domain-card-btn ${activeDomain === d.id ? "active" : ""}`}
                    onClick={() => {
                      setActiveDomain(d.id);
                      setAgentSimulation(null);
                    }}
                  >
                    <div className="domain-btn-header">
                      <span>{d.icon}</span>
                      <span>{d.label}</span>
                    </div>
                    <div className="domain-btn-sub">{d.desc}</div>
                  </button>
                ))}
              </div>

              {/* Quick Template Chips */}
              <div style={{ textAlign: "left", marginBottom: "0.5rem" }}>
                <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", marginBottom: "0.35rem" }}>
                  Example Service Scenarios (Click to auto-fill):
                </div>
                <div className="template-chips">
                  {(TEMPLATES[activeDomain] || []).map((t, idx) => (
                    <button
                      key={idx}
                      type="button"
                      className="chip-btn"
                      onClick={() => handleApplyTemplate(t)}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>
              </div>

              <form onSubmit={handleSubmitServiceRequest}>
                <div className="form-group">
                  <label>Request Title *</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="State your institutional request clearly..."
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Natural Language Description (Multilingual Supported: EN / HI / OR) *</label>
                  <textarea
                    className="form-control"
                    rows="4"
                    placeholder="Provide full context, registration numbers, slot timings, or problem details in any language..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    required
                  />
                </div>

                {/* Agent Simulation Output Box */}
                {agentSimulation && (
                  <div className="agent-plan-box animate-fade-in">
                    <div className="agent-plan-header">
                      <span>✨ Ollama Llama 3.2 3B Plan & Policy Verification</span>
                      <span>{agentSimulation.detected_language.toUpperCase()}</span>
                    </div>

                    <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.65rem" }}>
                      <span className="badge badge-domain">{agentSimulation.domain}</span>
                      <span className="badge badge-category">{agentSimulation.category}</span>
                      {renderPriorityBadge(agentSimulation.priority)}
                      {agentSimulation.requires_hitl ? (
                        <span className="badge badge-status-hitl">🚨 HITL Consequential Gate</span>
                      ) : (
                        <span className="badge badge-status-executed">✓ Autonomous Dispatch</span>
                      )}
                    </div>

                    {/* Policy Citations */}
                    {agentSimulation.policy_citations?.length > 0 && (
                      <div style={{ marginBottom: "0.5rem" }}>
                        <div style={{ fontSize: "0.72rem", color: "#a78bfa", marginBottom: "0.25rem" }}>
                          Verified Policy Rules Cited:
                        </div>
                        <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
                          {agentSimulation.policy_citations.map((c, idx) => (
                            <span key={idx} className="policy-citation-pill">
                              {c.code}: {c.title}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Multi-step Plan */}
                    <div style={{ fontSize: "0.75rem", color: "#c4b5fd", marginTop: "0.5rem", marginBottom: "0.25rem" }}>
                      Planned Action Steps:
                    </div>
                    {agentSimulation.plan_steps?.map((step, idx) => (
                      <div key={idx} className="plan-step-item">
                        <span>🔹</span> {step}
                      </div>
                    ))}
                  </div>
                )}

                <div style={{ display: "flex", gap: "0.75rem", marginTop: "1rem" }}>
                  <button
                    type="button"
                    className="btn-secondary-sm"
                    style={{ flex: 1, padding: "0.75rem", justifyContent: "center" }}
                    onClick={handleSimulateAgent}
                    disabled={simulating || !title || !description}
                  >
                    {simulating ? "Simulating..." : "⚡ Test Agent Plan (Pre-submit)"}
                  </button>

                  <button
                    type="submit"
                    className="btn-primary"
                    style={{ flex: 1.2 }}
                    disabled={submitting || !title || !description}
                  >
                    {submitting ? "Orchestrating..." : "Submit to Agentic AI"}
                  </button>
                </div>
              </form>
            </section>

            {/* My Service Requests Tracker */}
            <section className="card">
              <div className="card-header">
                <h2 className="card-title">
                  <span>📜</span> My Institutional Requests ({filteredRequests.length})
                </h2>
              </div>

              <div className="filter-toolbar">
                <div className="search-input-wrapper">
                  <span className="search-icon">🔍</span>
                  <input
                    type="text"
                    className="search-input"
                    placeholder="Search by keyword..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>

                <select className="filter-select" value={filterDomain} onChange={(e) => setFilterDomain(e.target.value)}>
                  <option value="All">All Domains</option>
                  <option value="Certificate">📜 Certificate</option>
                  <option value="Maintenance">🔧 Maintenance</option>
                  <option value="LabBooking">🔬 Lab Booking</option>
                  <option value="Grievance">⚖️ Grievance</option>
                </select>
              </div>

              {loadingRequests ? (
                <div className="empty-state">Loading requests...</div>
              ) : filteredRequests.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-state-icon">📭</div>
                  <h3>No service requests found</h3>
                  <p>Choose a service module on the left to dispatch your request.</p>
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  {filteredRequests.map((r) => (
                    <div key={r.id} className="card" style={{ background: "var(--bg-card)", padding: "1.25rem", textAlign: "left" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem" }}>
                        <div>
                          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
                            <span className="badge badge-domain">{r.request_type}</span>
                            <span className="badge badge-category">{r.category}</span>
                            {renderPriorityBadge(r.priority)}
                          </div>
                          <h3 style={{ fontSize: "1.05rem", color: "var(--text-main)", fontWeight: 600 }}>
                            #{r.id} — {r.title}
                          </h3>
                        </div>
                        <div>{renderStatusBadge(r.status)}</div>
                      </div>

                      <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", margin: "0.65rem 0", lineHeight: 1.5 }}>
                        {r.description}
                      </p>

                      {/* Execution Result Banner */}
                      {r.execution_result && (
                        <div
                          style={{
                            background: "rgba(16, 185, 129, 0.08)",
                            border: "1px solid rgba(16, 185, 129, 0.25)",
                            borderRadius: "var(--radius-md)",
                            padding: "0.65rem 0.85rem",
                            fontSize: "0.8rem",
                            color: "#a7f3d0",
                            marginBottom: "0.65rem",
                          }}
                        >
                          <strong>⚡ Action Outcome:</strong> {r.execution_result}
                        </div>
                      )}

                      <div style={{ display: "flex", justifyContent: "flex-end" }}>
                        <button
                          type="button"
                          className="btn-secondary-sm"
                          onClick={() => handleOpenAuditTrail(r.id)}
                        >
                          Inspect Auditable Action Trail →
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}
      </main>

      {/* -------------------------------------------------------------
          AUDITABLE ACTION TRAIL MODAL (EXPLAINABILITY & AUDIT LOGS)
      ------------------------------------------------------------- */}
      {selectedAuditTrail && (
        <div className="modal-backdrop animate-fade-in" onClick={() => setSelectedAuditTrail(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">
                📜 Auditable Action Trail — Request #{selectedAuditTrail.request_id}
              </div>
              <button type="button" className="btn-close" onClick={() => setSelectedAuditTrail(null)}>
                ✕
              </button>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ fontSize: "0.9rem", color: "var(--text-main)", fontWeight: 600 }}>
                {selectedAuditTrail.title}
              </div>
              <div>{renderStatusBadge(selectedAuditTrail.status)}</div>
            </div>

            {/* Audit Log Timeline */}
            <div className="audit-timeline">
              {selectedAuditTrail.audit_logs.map((log) => (
                <div key={log.id} className="timeline-item">
                  <div
                    className={`timeline-marker ${
                      log.action.includes("HITL") ? "hitl" : log.action.includes("Executed") ? "executed" : ""
                    }`}
                  ></div>
                  <div className="timeline-header">
                    <span>Step {log.step}: {log.action}</span>
                    <span className="timeline-actor">{log.actor}</span>
                    {log.policy_ref && <span className="policy-citation-pill">{log.policy_ref}</span>}
                  </div>
                  <div className="timeline-desc">{log.details}</div>
                  {log.timestamp && (
                    <div style={{ fontSize: "0.7rem", color: "var(--text-dim)" }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", paddingTop: "0.75rem", borderTop: "1px solid var(--border-color)" }}>
              <button type="button" className="btn-primary" style={{ width: "auto" }} onClick={() => setSelectedAuditTrail(null)}>
                Close Audit View
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast Notifications */}
      <div className="toast-container">
        {toasts.map((t) => (
          <div key={t.id} className={`toast ${t.type}`}>
            {t.message}
          </div>
        ))}
      </div>
    </div>
  );
}