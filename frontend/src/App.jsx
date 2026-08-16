import React, { useState, useEffect, useMemo } from "react";
import axios from "axios";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

// Predefined quick templates for students
const TEMPLATES = [
  {
    label: "Scholarship Delay",
    title: "Scholarship payment not received for 3 months",
    desc: "My state merit scholarship was approved 3 months ago by the scholarship cell, but the funds have still not been credited to my bank account. Reference No: SC-2026-8941.",
    cat: "Scholarship",
  },
  {
    label: "Hostel Water Issue",
    title: "Hostel Block C drinking water cooler malfunction",
    desc: "The drinking water cooler on the 2nd floor of Hostel C has been broken for over a week and emitting a burning smell. Students currently have to walk to Block A for water.",
    cat: "Hostel",
  },
  {
    label: "Exam Marks Mismatch",
    title: "Re-evaluation mark discrepancy on ERP student portal",
    desc: "I received my revised paper review marksheet for Operating Systems showing 78 marks, but the online grade portal still displays the failing grade of 38.",
    cat: "Examination",
  },
  {
    label: "Lab Broken Equipment",
    title: "Computer Lab 4 malfunctioning GPU workstations",
    desc: "Workstations 12 through 16 in AI Lab 4 are shutting down randomly during practical sessions due to overheating and faulty power supply units.",
    cat: "Academic",
  },
];

export default function App() {
  // Auth State
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [user, setUser] = useState(null);
  const [isRegistering, setIsRegistering] = useState(false);
  const [authLoading, setAuthLoading] = useState(false);

  // Auth Form Fields
  const [authName, setAuthName] = useState("");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authRole, setAuthRole] = useState("user");

  // System Health / Diagnostics
  const [systemStatus, setSystemStatus] = useState(null);

  // Student Grievance Submission Fields
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [aiPreviewLoading, setAiPreviewLoading] = useState(false);
  const [aiPreviewData, setAiPreviewData] = useState(null);

  // Grievance Lists
  const [studentGrievances, setStudentGrievances] = useState([]);
  const [adminGrievances, setAdminGrievances] = useState([]);
  const [loadingGrievances, setLoadingGrievances] = useState(false);

  // Filtering & Search
  const [searchQuery, setSearchQuery] = useState("");
  const [filterCategory, setFilterCategory] = useState("All");
  const [filterStatus, setFilterStatus] = useState("All");
  const [filterPriority, setFilterPriority] = useState("All");

  // Active View (for Admin: 'admin' or 'student_view')
  const [adminActiveTab, setAdminActiveTab] = useState("admin");

  // Selected Grievance for Detail Modal
  const [selectedGrievance, setSelectedGrievance] = useState(null);

  // Toast Notifications
  const [toasts, setToasts] = useState([]);

  const showToast = (message, type = "info") => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  };

  // -------------------------------------------------------------
  // Initial Lifecycle: Verify Token & Fetch Diagnostics
  // -------------------------------------------------------------
  useEffect(() => {
    fetchSystemStatus();
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

  const fetchCurrentUser = async (authToken) => {
    try {
      const res = await axios.get(`${API_BASE}/users/me`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      setUser(res.data);
      if (res.data.role === "admin") {
        fetchAdminGrievances(authToken);
      }
      fetchStudentGrievances(authToken);
    } catch (err) {
      console.error("Token verification failed:", err);
      handleLogout();
    }
  };

  const fetchStudentGrievances = async (authToken = token) => {
    if (!authToken) return;
    setLoadingGrievances(true);
    try {
      const res = await axios.get(`${API_BASE}/grievances`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      setStudentGrievances(res.data.grievances || []);
    } catch (err) {
      console.error("Error fetching student grievances:", err);
    } finally {
      setLoadingGrievances(false);
    }
  };

  const fetchAdminGrievances = async (authToken = token) => {
    if (!authToken) return;
    setLoadingGrievances(true);
    try {
      const res = await axios.get(`${API_BASE}/admin/grievances`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      setAdminGrievances(res.data.grievances || []);
    } catch (err) {
      console.error("Error fetching admin grievances:", err);
    } finally {
      setLoadingGrievances(false);
    }
  };

  // -------------------------------------------------------------
  // Authentication Handlers
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
        fetchAdminGrievances(authToken);
      }
      fetchStudentGrievances(authToken);
      fetchSystemStatus();
    } catch (err) {
      const msg = err.response?.data?.detail || "Login failed. Check your credentials.";
      showToast(msg, "error");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setAuthLoading(true);

    try {
      const res = await axios.post(`${API_BASE}/register`, {
        name: authName,
        email: authEmail,
        password: authPassword,
        role: authRole,
      });

      showToast("Account registered successfully! Logging you in...", "success");
      // Auto login after registration
      await handleLogin(null, authEmail, authPassword);
      setAuthName("");
      setAuthEmail("");
      setAuthPassword("");
      setIsRegistering(false);
    } catch (err) {
      const msg = err.response?.data?.detail || "Registration failed.";
      showToast(msg, "error");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    setToken("");
    setUser(null);
    setStudentGrievances([]);
    setAdminGrievances([]);
    showToast("Signed out successfully.", "info");
  };

  // Fast Demo Login Helpers
  const fillAndLoginStudent = () => {
    setAuthEmail("student@college.edu");
    setAuthPassword("student123");
    handleLogin(null, "student@college.edu", "student123");
  };

  const fillAndLoginAdmin = () => {
    setAuthEmail("admin@college.edu");
    setAuthPassword("admin123");
    handleLogin(null, "admin@college.edu", "admin123");
  };

  // -------------------------------------------------------------
  // AI Preview & Grievance Submission
  // -------------------------------------------------------------
  const handleAiPreview = async () => {
    if (!title || !description) {
      showToast("Please enter a title and description first.", "error");
      return;
    }
    setAiPreviewLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/ai/analyze`, {
        title,
        description,
      });
      setAiPreviewData(res.data.analysis);
      showToast("Ollama Llama 3.2 3B analyzed grievance successfully!", "success");
    } catch {
      showToast("Could not contact AI analyzer.", "error");
    } finally {
      setAiPreviewLoading(false);
    }
  };

  const handleGrievanceSubmit = async (e) => {
    e.preventDefault();
    if (!title || !description) return;

    setSubmitting(true);
    try {
      const res = await axios.post(
        `${API_BASE}/grievances`,
        {
          title,
          description,
          category: category || undefined,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      const created = res.data.grievance;
      showToast("Grievance analyzed by AI and submitted successfully!", "success");

      setTitle("");
      setDescription("");
      setCategory("");
      setAiPreviewData(null);

      // Refresh listings
      fetchStudentGrievances(token);
      if (user?.role === "admin") {
        fetchAdminGrievances(token);
      }
      fetchSystemStatus();

      // Show detail popup for the newly created grievance
      setSelectedGrievance(created);
    } catch (err) {
      const msg = err.response?.data?.detail || "Submission failed.";
      showToast(msg, "error");
    } finally {
      setSubmitting(false);
    }
  };

  const handleApplyTemplate = (tmpl) => {
    setTitle(tmpl.title);
    setDescription(tmpl.desc);
    setCategory(tmpl.cat);
    setAiPreviewData(null);
  };

  // -------------------------------------------------------------
  // Admin Status Update Handler
  // -------------------------------------------------------------
  const handleUpdateStatus = async (grievanceId, newStatus) => {
    try {
      const res = await axios.put(
        `${API_BASE}/admin/grievances/${grievanceId}/status`,
        { status: newStatus },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      showToast(`Grievance #${grievanceId} marked as ${newStatus}`, "success");

      // Update in admin state
      setAdminGrievances((prev) =>
        prev.map((g) => (g.id === grievanceId ? { ...g, status: newStatus, updated_at: res.data.grievance.updated_at } : g))
      );

      // Update modal if open
      if (selectedGrievance && selectedGrievance.id === grievanceId) {
        setSelectedGrievance((prev) => ({ ...prev, status: newStatus }));
      }

      fetchSystemStatus();
    } catch (err) {
      const msg = err.response?.data?.detail || "Status update failed.";
      showToast(msg, "error");
    }
  };

  // -------------------------------------------------------------
  // Filtered Grievances Memo
  // -------------------------------------------------------------
  const activeGrievancesList = user?.role === "admin" && adminActiveTab === "admin" ? adminGrievances : studentGrievances;

  const filteredGrievances = useMemo(() => {
    return activeGrievancesList.filter((g) => {
      const matchesSearch =
        searchQuery === "" ||
        g.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        g.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        g.student_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        g.student_email?.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesCat = filterCategory === "All" || g.category === filterCategory;
      const matchesStatus = filterStatus === "All" || g.status === filterStatus;
      const matchesPrio = filterPriority === "All" || g.priority === filterPriority;

      return matchesSearch && matchesCat && matchesStatus && matchesPrio;
    });
  }, [activeGrievancesList, searchQuery, filterCategory, filterStatus, filterPriority]);

  // Statistics Calculation
  const stats = useMemo(() => {
    const list = user?.role === "admin" ? adminGrievances : studentGrievances;
    return {
      total: list.length,
      pending: list.filter((g) => g.status === "Pending").length,
      inProgress: list.filter((g) => g.status === "In Progress").length,
      resolved: list.filter((g) => g.status === "Resolved").length,
      highPriority: list.filter((g) => g.priority === "High").length,
    };
  }, [studentGrievances, adminGrievances, user]);

  // Helper Badge Renderers
  const renderStatusBadge = (statusVal) => {
    let cls = "badge-status-pending";
    if (statusVal === "In Progress") cls = "badge-status-inprogress";
    if (statusVal === "Resolved") cls = "badge-status-resolved";
    if (statusVal === "Rejected") cls = "badge-status-rejected";

    return <span className={`badge ${cls}`}>{statusVal}</span>;
  };

  const renderPriorityBadge = (prio) => {
    let cls = "badge-prio-medium";
    if (prio === "High") cls = "badge-prio-high";
    if (prio === "Low") cls = "badge-prio-low";

    return (
      <span className={`badge ${cls}`}>
        {prio === "High" && "⚡ "}
        {prio} Priority
      </span>
    );
  };

  // -------------------------------------------------------------
  // RENDER: Not Logged In (Auth View)
  // -------------------------------------------------------------
  if (!user) {
    return (
      <div className="app-container">
        {/* Navigation / Header */}
        <header className="navbar">
          <div className="nav-brand">
            <div className="brand-icon">🎓</div>
            <div>
              <div className="brand-title">CampusVoice AI</div>
              <div className="brand-sub">College Grievance Management System</div>
            </div>
          </div>

          <div className="nav-actions">
            <div className="system-status-pill">
              <span className={`status-dot ${systemStatus?.ollama?.available ? "" : "warning"}`}></span>
              <span>Ollama {systemStatus?.ollama?.model || "Llama 3.2 3B"}</span>
            </div>
          </div>
        </header>

        {/* Authentication Card */}
        <div className="auth-wrapper">
          <div className="auth-card animate-fade-in">
            <div className="auth-header">
              <h1>{isRegistering ? "Student / Faculty Registration" : "Portal Login"}</h1>
              <p>
                {isRegistering
                  ? "Create your grievance management account"
                  : "Sign in to submit complaints or manage college grievances"}
              </p>
            </div>

            {/* Quick Demo Logins */}
            <div className="demo-credentials-banner">
              <div className="demo-title">⚡ Instant Demo Logins (Click to Enter)</div>
              <div className="demo-buttons">
                <button
                  type="button"
                  className="demo-btn"
                  onClick={fillAndLoginStudent}
                  disabled={authLoading}
                >
                  🎓 Student Demo
                </button>
                <button
                  type="button"
                  className="demo-btn"
                  onClick={fillAndLoginAdmin}
                  disabled={authLoading}
                >
                  🛡️ Admin Demo
                </button>
              </div>
            </div>

            {/* Toggle Tabs */}
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

            {/* Login Form */}
            {!isRegistering ? (
              <form onSubmit={handleLogin}>
                <div className="form-group">
                  <label>Institutional Email</label>
                  <input
                    type="email"
                    className="form-control"
                    placeholder="e.g. student@college.edu"
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
                    placeholder="Enter your password"
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                    required
                  />
                </div>

                <button type="submit" className="btn-primary" disabled={authLoading}>
                  {authLoading ? "Authenticating..." : "Sign In to Portal"}
                </button>
              </form>
            ) : (
              /* Registration Form */
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
                    placeholder="e.g. student@college.edu"
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
                    className="form-control form-select"
                    value={authRole}
                    onChange={(e) => setAuthRole(e.target.value)}
                  >
                    <option value="user">Student (Submit & View Grievances)</option>
                    <option value="admin">Administrator (Review & Resolve All)</option>
                  </select>
                </div>

                <button type="submit" className="btn-primary" disabled={authLoading}>
                  {authLoading ? "Creating Account..." : "Register Account"}
                </button>
              </form>
            )}
          </div>
        </div>

        {/* Toast Alerts */}
        <div className="toast-container">
          {toasts.map((t) => (
            <div key={t.id} className={`toast ${t.type}`}>
              {t.type === "success" && "✓ "}
              {t.type === "error" && "✕ "}
              {t.message}
            </div>
          ))}
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // RENDER: Logged In (Student & Admin Dashboard)
  // -------------------------------------------------------------
  return (
    <div className="app-container">
      {/* Top Navbar */}
      <header className="navbar">
        <div className="nav-brand">
          <div className="brand-icon">🎓</div>
          <div>
            <div className="brand-title">CampusVoice AI</div>
            <div className="brand-sub">College Grievance Management System</div>
          </div>
        </div>

        <div className="nav-actions">
          {/* AI / System Badge */}
          <div className="system-status-pill" title="Local Ollama AI Model Engine">
            <span className={`status-dot ${systemStatus?.ollama?.available ? "" : "warning"}`}></span>
            <span>Ollama {systemStatus?.ollama?.model || "llama3.2:3b"}</span>
          </div>

          {/* Admin Tab Switcher */}
          {user.role === "admin" && (
            <div className="auth-tabs" style={{ margin: 0, padding: "2px" }}>
              <button
                type="button"
                className={`auth-tab ${adminActiveTab === "admin" ? "active" : ""}`}
                style={{ padding: "0.3rem 0.75rem", fontSize: "0.75rem" }}
                onClick={() => setAdminActiveTab("admin")}
              >
                🛡️ Admin Console
              </button>
              <button
                type="button"
                className={`auth-tab ${adminActiveTab === "student_view" ? "active" : ""}`}
                style={{ padding: "0.3rem 0.75rem", fontSize: "0.75rem" }}
                onClick={() => setAdminActiveTab("student_view")}
              >
                📝 Submit Form
              </button>
            </div>
          )}

          {/* User Profile Pill */}
          <div className="user-profile-pill">
            <div className={`user-avatar ${user.role === "admin" ? "admin" : ""}`}>
              {user.name ? user.name.charAt(0).toUpperCase() : "U"}
            </div>
            <div className="user-info">
              <span className="user-name">{user.name}</span>
              <span className={`role-badge ${user.role === "admin" ? "admin" : ""}`}>
                {user.role === "admin" ? "Administrator" : "Student"}
              </span>
            </div>
          </div>

          <button type="button" className="btn-secondary-sm" onClick={handleLogout}>
            Sign Out
          </button>
        </div>
      </header>

      {/* Main Workspace */}
      <main className="main-content">
        {/* Metrics Grid */}
        <section className="metrics-grid">
          <div className="metric-card">
            <div>
              <div className="metric-label">
                {user.role === "admin" && adminActiveTab === "admin" ? "Total Grievances" : "My Submissions"}
              </div>
              <div className="metric-value">{stats.total}</div>
            </div>
            <div className="metric-icon blue">📁</div>
          </div>

          <div className="metric-card">
            <div>
              <div className="metric-label">Pending Action</div>
              <div className="metric-value">{stats.pending}</div>
            </div>
            <div className="metric-icon amber">⏳</div>
          </div>

          <div className="metric-card">
            <div>
              <div className="metric-label">In Progress</div>
              <div className="metric-value">{stats.inProgress}</div>
            </div>
            <div className="metric-icon blue">⚙️</div>
          </div>

          <div className="metric-card">
            <div>
              <div className="metric-label">Resolved</div>
              <div className="metric-value">{stats.resolved}</div>
            </div>
            <div className="metric-icon emerald">✓</div>
          </div>

          {stats.highPriority > 0 && (
            <div className="metric-card">
              <div>
                <div className="metric-label">High Priority Urgent</div>
                <div className="metric-value">{stats.highPriority}</div>
              </div>
              <div className="metric-icon rose">⚡</div>
            </div>
          )}
        </section>

        {/* -------------------------------------------------------------
            STUDENT VIEW (OR ADMIN IN STUDENT MODE)
        ------------------------------------------------------------- */}
        {(user.role === "user" || adminActiveTab === "student_view") && (
          <div className="student-layout">
            {/* Submit Grievance Form */}
            <section className="card animate-fade-in">
              <div className="card-header">
                <h2 className="card-title">
                  <span>✍️</span> Submit a Grievance
                </h2>
              </div>

              {/* Quick Template Chips */}
              <div style={{ marginBottom: "0.5rem" }}>
                <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", marginBottom: "0.35rem" }}>
                  Quick Fill Templates:
                </div>
                <div className="template-chips">
                  {TEMPLATES.map((t, idx) => (
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

              {/* AI Badge Note */}
              <div className="ai-notice-box">
                <span>✨</span>
                <span>
                  <strong>Local Ollama Llama 3.2 3B</strong> will automatically categorize, estimate priority, and
                  generate an executive summary for college administrators upon submission.
                </span>
              </div>

              <form onSubmit={handleGrievanceSubmit}>
                <div className="form-group">
                  <label>Grievance Title *</label>
                  <input
                    type="text"
                    className="form-control"
                    placeholder="e.g. Scholarship not received for semester 4"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Detailed Description *</label>
                  <textarea
                    className="form-control"
                    rows="4"
                    placeholder="Explain the issue thoroughly, mentioning dates, locations, or reference numbers..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Preferred Category (Optional)</label>
                  <select
                    className="form-control form-select"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                  >
                    <option value="">Let AI Automatically Determine Category</option>
                    <option value="Academic">Academic</option>
                    <option value="Scholarship">Scholarship</option>
                    <option value="Hostel">Hostel</option>
                    <option value="Examination">Examination</option>
                    <option value="Fees">Fees</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                {/* AI Live Preview Card if triggered */}
                {aiPreviewData && (
                  <div className="ai-preview-card animate-fade-in">
                    <div className="ai-preview-header">
                      <span>✨ Ollama Llama 3.2 Assessment</span>
                      <span>AI Model Verified</span>
                    </div>
                    <div className="ai-badge-row">
                      <span className="badge badge-category">{aiPreviewData.category}</span>
                      {renderPriorityBadge(aiPreviewData.priority)}
                    </div>
                    <div className="ai-summary-text">"{aiPreviewData.summary}"</div>
                  </div>
                )}

                <div className="form-actions">
                  <button
                    type="button"
                    className="btn-ai-preview"
                    onClick={handleAiPreview}
                    disabled={aiPreviewLoading || !title || !description}
                  >
                    {aiPreviewLoading ? "Analyzing..." : "⚡ Test AI Preview"}
                  </button>

                  <button
                    type="submit"
                    className="btn-primary"
                    style={{ flex: 1 }}
                    disabled={submitting || !title || !description}
                  >
                    {submitting ? "Analyzing & Submitting..." : "Submit Grievance"}
                  </button>
                </div>
              </form>
            </section>

            {/* My Grievances Explorer */}
            <section className="card">
              <div className="card-header">
                <h2 className="card-title">
                  <span>📋</span> My Grievances ({filteredGrievances.length})
                </h2>
              </div>

              {/* Filters */}
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

                <select
                  className="filter-select"
                  value={filterCategory}
                  onChange={(e) => setFilterCategory(e.target.value)}
                >
                  <option value="All">All Categories</option>
                  <option value="Academic">Academic</option>
                  <option value="Scholarship">Scholarship</option>
                  <option value="Hostel">Hostel</option>
                  <option value="Examination">Examination</option>
                  <option value="Fees">Fees</option>
                  <option value="Other">Other</option>
                </select>

                <select
                  className="filter-select"
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                >
                  <option value="All">All Statuses</option>
                  <option value="Pending">Pending</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Resolved">Resolved</option>
                  <option value="Rejected">Rejected</option>
                </select>
              </div>

              {/* Grievances List */}
              {loadingGrievances ? (
                <div className="empty-state">Loading grievances...</div>
              ) : filteredGrievances.length === 0 ? (
                <div className="empty-state">
                  <div className="empty-state-icon">📭</div>
                  <h3>No grievances found</h3>
                  <p>Submit a new complaint using the form on the left.</p>
                </div>
              ) : (
                <div className="grievance-list">
                  {filteredGrievances.map((g) => (
                    <div key={g.id} className="grievance-item-card">
                      <div className="grievance-top-row">
                        <div className="grievance-title-area">
                          <div className="grievance-heading">{g.title}</div>
                          <div className="grievance-meta">
                            <span>#{g.id}</span>
                            <span>•</span>
                            <span className="badge badge-category">{g.category}</span>
                            <span>•</span>
                            <span>
                              {g.created_at ? new Date(g.created_at).toLocaleDateString() : "Recent"}
                            </span>
                          </div>
                        </div>

                        <div className="grievance-badges">
                          {renderPriorityBadge(g.priority)}
                          {renderStatusBadge(g.status)}
                        </div>
                      </div>

                      <p className="grievance-desc-text">{g.description}</p>

                      {/* AI Summary Block */}
                      {g.ai_summary && (
                        <div className="ai-summary-callout">
                          <div className="ai-summary-title">
                            <span>✨</span> AI Executive Summary
                          </div>
                          <div>{g.ai_summary}</div>
                        </div>
                      )}

                      <div style={{ display: "flex", justifyContent: "flex-end" }}>
                        <button
                          type="button"
                          className="btn-secondary-sm"
                          onClick={() => setSelectedGrievance(g)}
                        >
                          View Full Details →
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}

        {/* -------------------------------------------------------------
            ADMIN MANAGEMENT CONSOLE
        ------------------------------------------------------------- */}
        {user.role === "admin" && adminActiveTab === "admin" && (
          <section className="card animate-fade-in">
            <div className="card-header">
              <h2 className="card-title">
                <span>🛡️</span> Grievance Resolution Center ({filteredGrievances.length})
              </h2>
            </div>

            {/* Filter Bar */}
            <div className="filter-toolbar">
              <div className="search-input-wrapper">
                <span className="search-icon">🔍</span>
                <input
                  type="text"
                  className="search-input"
                  placeholder="Search student, email, or issue title..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              <select
                className="filter-select"
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
              >
                <option value="All">All Categories</option>
                <option value="Academic">Academic</option>
                <option value="Scholarship">Scholarship</option>
                <option value="Hostel">Hostel</option>
                <option value="Examination">Examination</option>
                <option value="Fees">Fees</option>
                <option value="Other">Other</option>
              </select>

              <select
                className="filter-select"
                value={filterPriority}
                onChange={(e) => setFilterPriority(e.target.value)}
              >
                <option value="All">All Priorities</option>
                <option value="High">High Priority</option>
                <option value="Medium">Medium Priority</option>
                <option value="Low">Low Priority</option>
              </select>

              <select
                className="filter-select"
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
              >
                <option value="All">All Statuses</option>
                <option value="Pending">Pending</option>
                <option value="In Progress">In Progress</option>
                <option value="Resolved">Resolved</option>
                <option value="Rejected">Rejected</option>
              </select>
            </div>

            {/* Table View */}
            {filteredGrievances.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">🛡️</div>
                <h3>No grievances match the current filter</h3>
              </div>
            ) : (
              <div className="admin-table-wrapper">
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Student</th>
                      <th>Grievance Title & Category</th>
                      <th>AI Priority</th>
                      <th>AI Summary</th>
                      <th>Status Action</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredGrievances.map((g) => (
                      <tr key={g.id}>
                        <td>
                          <strong>#{g.id}</strong>
                        </td>
                        <td>
                          <div className="student-col">
                            <span className="student-col-name">{g.student_name || "Student"}</span>
                            <span className="student-col-email">{g.student_email || "N/A"}</span>
                          </div>
                        </td>
                        <td style={{ maxWidth: "260px" }}>
                          <div style={{ fontWeight: 600, color: "var(--text-main)", marginBottom: "4px" }}>
                            {g.title}
                          </div>
                          <span className="badge badge-category">{g.category}</span>
                        </td>
                        <td>{renderPriorityBadge(g.priority)}</td>
                        <td style={{ maxWidth: "280px", fontSize: "0.8rem", color: "var(--text-muted)" }}>
                          {g.ai_summary || g.description?.slice(0, 80) + "..."}
                        </td>
                        <td>
                          <select
                            className="status-dropdown"
                            value={g.status}
                            onChange={(e) => handleUpdateStatus(g.id, e.target.value)}
                          >
                            <option value="Pending">⏳ Pending</option>
                            <option value="In Progress">⚙️ In Progress</option>
                            <option value="Resolved">✓ Resolved</option>
                            <option value="Rejected">✕ Rejected</option>
                          </select>
                        </td>
                        <td>
                          <button
                            type="button"
                            className="btn-secondary-sm"
                            onClick={() => setSelectedGrievance(g)}
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}
      </main>

      {/* -------------------------------------------------------------
          GRIEVANCE DETAIL MODAL
      ------------------------------------------------------------- */}
      {selectedGrievance && (
        <div className="modal-backdrop animate-fade-in" onClick={() => setSelectedGrievance(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">Grievance #{selectedGrievance.id} Details</div>
              <button
                type="button"
                className="btn-close"
                onClick={() => setSelectedGrievance(null)}
              >
                ✕
              </button>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <span className="badge badge-category">{selectedGrievance.category}</span>
                {renderPriorityBadge(selectedGrievance.priority)}
              </div>
              <div>{renderStatusBadge(selectedGrievance.status)}</div>
            </div>

            <div>
              <h3 style={{ fontSize: "1.15rem", color: "var(--text-main)", marginBottom: "0.5rem" }}>
                {selectedGrievance.title}
              </h3>
              <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", lineHeight: "1.6" }}>
                {selectedGrievance.description}
              </p>
            </div>

            {/* AI Assessment Diagnostic Box */}
            <div className="ai-summary-callout">
              <div className="ai-summary-title">
                <span>✨</span> Local Ollama AI Assessment (Llama 3.2 3B)
              </div>
              <div style={{ color: "var(--text-main)", marginBottom: "0.35rem" }}>
                "{selectedGrievance.ai_summary}"
              </div>
              <div style={{ fontSize: "0.72rem", color: "#a78bfa" }}>
                Classification: {selectedGrievance.category} • Urgency Rating: {selectedGrievance.priority}
              </div>
            </div>

            {/* Metadata Info */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "0.75rem",
                padding: "0.85rem",
                background: "var(--bg-card)",
                borderRadius: "var(--radius-md)",
                fontSize: "0.8rem",
              }}
            >
              <div>
                <span style={{ color: "var(--text-dim)" }}>Submitted By:</span>
                <div style={{ fontWeight: 600 }}>{selectedGrievance.student_name || user.name}</div>
              </div>
              <div>
                <span style={{ color: "var(--text-dim)" }}>Student Email:</span>
                <div style={{ fontWeight: 600 }}>{selectedGrievance.student_email || user.email}</div>
              </div>
              <div>
                <span style={{ color: "var(--text-dim)" }}>Submission Date:</span>
                <div>
                  {selectedGrievance.created_at
                    ? new Date(selectedGrievance.created_at).toLocaleString()
                    : "Recent"}
                </div>
              </div>
              <div>
                <span style={{ color: "var(--text-dim)" }}>Last Status Update:</span>
                <div>
                  {selectedGrievance.updated_at
                    ? new Date(selectedGrievance.updated_at).toLocaleString()
                    : "Recent"}
                </div>
              </div>
            </div>

            {/* Admin Status Changer if Admin */}
            {user.role === "admin" && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  paddingTop: "0.75rem",
                  borderTop: "1px solid var(--border-color)",
                }}
              >
                <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>Update Status:</span>
                <div style={{ display: "flex", gap: "0.4rem" }}>
                  {["Pending", "In Progress", "Resolved", "Rejected"].map((st) => (
                    <button
                      key={st}
                      type="button"
                      className="btn-secondary-sm"
                      style={{
                        background:
                          selectedGrievance.status === st ? "var(--primary)" : "var(--bg-card)",
                        color: selectedGrievance.status === st ? "#fff" : "var(--text-muted)",
                      }}
                      onClick={() => handleUpdateStatus(selectedGrievance.id, st)}
                    >
                      {st}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Toast Notification Container */}
      <div className="toast-container">
        {toasts.map((t) => (
          <div key={t.id} className={`toast ${t.type}`}>
            {t.type === "success" && "✓ "}
            {t.type === "error" && "✕ "}
            {t.message}
          </div>
        ))}
      </div>
    </div>
  );
}