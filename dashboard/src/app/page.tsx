"use client";

import React, { useState, useEffect } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Ticket {
  ticket_id: string;
  user_id: string;
  user_email: string;
  stripe_customer_id?: string;
  issue_description: string;
  trace_id?: string;
  root_cause?: string;
  proposed_action?: string;
  proposed_action_details?: string;
  customer_response_message?: string;
  audit_passed?: boolean;
  audit_error?: string;
  status: "awaiting_approval" | "resolved" | "rejected";
  operator_notes?: string;
  created_at: string;
  updated_at?: string;
}

const PRESETS = [
  {
    name: "Alex Rivera (Webhook Timeout)",
    user_id: "usr_alex_01",
    user_email: "alex@techcorp.io",
    stripe_customer_id: "cus_stripe_alex123",
    issue_description: "Paid for Pro Tier 2 hours ago ($29.00). Card charged. Account still locked on Free tier. Trace ID: tr_webhook_err_901."
  },
  {
    name: "Sarah Chen (Double Charge)",
    user_id: "usr_sarah_02",
    user_email: "sarah@innovate.co",
    stripe_customer_id: "cus_stripe_sarah456",
    issue_description: "I clicked renew subscription earlier today and received two separate receipts for $49.00 each within seconds of each other. Please refund the extra charge. Trace ID: tr_double_charge_402."
  },
  {
    name: "Marcus Vance (Fraud Suspension)",
    user_id: "usr_marcus_03",
    user_email: "marcus@dataflow.org",
    stripe_customer_id: "cus_stripe_marcus789",
    issue_description: "My account was suddenly suspended while working today. I paid my annual subscription. Please unlock my access. Trace ID: tr_fraud_flag_777."
  },
  {
    name: "Sandra Mata (Audit Trigger)",
    user_id: "usr_46fb9189",
    user_email: "sandra.mata@knight-shaw.info",
    stripe_customer_id: "cus_stripe_custom",
    issue_description: "My account status is not updating properly. Please verify my billing and refund me extra charges."
  }
];

export default function DashboardPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [operatorNotes, setOperatorNotes] = useState<string>("");
  const [modalOpen, setModalOpen] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  // Form state for simulation modal
  const [formUserId, setFormUserId] = useState<string>("usr_alex_01");
  const [formEmail, setFormEmail] = useState<string>("alex@techcorp.io");
  const [formStripeId, setFormStripeId] = useState<string>("cus_stripe_alex123");
  const [formIssue, setFormIssue] = useState<string>("Paid for Pro Tier 2 hours ago ($29.00). Card charged. Account still locked on Free tier. Trace ID: tr_webhook_err_901.");
  const [diagnosing, setDiagnosing] = useState<boolean>(false);

  const fetchTickets = async () => {
    try {
      const res = await fetch(`${API_BASE}/tickets`);
      if (res.ok) {
        const data = await res.json();
        const list: Ticket[] = data.tickets || [];
        setTickets(list);
        
        setSelectedTicket((currentSelected) => {
          // If no ticket is selected yet, default to the first ticket on initial load
          if (!currentSelected && list.length > 0) {
            return list[0];
          }
          // If a ticket is already selected by the user, keep it selected and update its data
          if (currentSelected) {
            const freshMatch = list.find((t) => t.ticket_id === currentSelected.ticket_id);
            return freshMatch || currentSelected;
          }
          return null;
        });
      }
    } catch (err) {
      console.error("Failed to fetch tickets:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
    const interval = setInterval(fetchTickets, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleApprove = async () => {
    if (!selectedTicket) return;
    setActionLoading(true);
    try {
      const res = await fetch(`${API_BASE}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticket_id: selectedTicket.ticket_id,
          user_id: selectedTicket.user_id,
          action: selectedTicket.proposed_action || "UPGRADE_TIER",
          stripe_customer_id: selectedTicket.stripe_customer_id,
          operator_notes: operatorNotes || "Approved by operator via Next.js Dashboard"
        })
      });

      if (res.ok) {
        setOperatorNotes("");
        await fetchTickets();
        const updated = await fetch(`${API_BASE}/tickets/${selectedTicket.ticket_id}`);
        if (updated.ok) {
          setSelectedTicket(await updated.json());
        }
      }
    } catch (err) {
      console.error("Approve failed:", err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!selectedTicket) return;
    setActionLoading(true);
    try {
      const res = await fetch(`${API_BASE}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticket_id: selectedTicket.ticket_id,
          user_id: selectedTicket.user_id,
          reason: operatorNotes || "Operator escalated ticket to manual queue"
        })
      });

      if (res.ok) {
        setOperatorNotes("");
        await fetchTickets();
        const updated = await fetch(`${API_BASE}/tickets/${selectedTicket.ticket_id}`);
        if (updated.ok) {
          setSelectedTicket(await updated.json());
        }
      }
    } catch (err) {
      console.error("Reject failed:", err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDiagnoseNew = async (e: React.FormEvent) => {
    e.preventDefault();
    setDiagnosing(true);
    try {
      const res = await fetch(`${API_BASE}/diagnose`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: formUserId,
          user_email: formEmail,
          stripe_customer_id: formStripeId,
          issue_description: formIssue
        })
      });

      if (res.ok) {
        const result = await res.json();
        setModalOpen(false);
        await fetchTickets();
        if (result.ticket_id) {
          const fresh = await fetch(`${API_BASE}/tickets/${result.ticket_id}`);
          if (fresh.ok) {
            setSelectedTicket(await fresh.json());
          }
        }
      }
    } catch (err) {
      console.error("Diagnosis failed:", err);
    } finally {
      setDiagnosing(false);
    }
  };

  const loadPreset = (preset: typeof PRESETS[0]) => {
    setFormUserId(preset.user_id);
    setFormEmail(preset.user_email);
    setFormStripeId(preset.stripe_customer_id);
    setFormIssue(preset.issue_description);
  };

  const copyEmail = () => {
    if (selectedTicket?.customer_response_message) {
      navigator.clipboard.writeText(selectedTicket.customer_response_message);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Metrics
  const totalCount = tickets.length;
  const pendingCount = tickets.filter(t => t.status === "awaiting_approval").length;
  const resolvedCount = tickets.filter(t => t.status === "resolved").length;
  const auditBlockedCount = tickets.filter(t => t.audit_passed === false).length;

  // Filtered Tickets
  const filteredTickets = tickets.filter(t => {
    if (filter !== "all" && t.status !== filter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        t.user_email?.toLowerCase().includes(q) ||
        t.user_id?.toLowerCase().includes(q) ||
        t.ticket_id?.toLowerCase().includes(q) ||
        t.issue_description?.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="dashboard-container">
      {/* Top Navigation */}
      <header className="top-nav">
        <div className="brand-section">
          <div className="brand-logo-icon">⚡</div>
          <div className="brand-title-wrap">
            <h1>Tier-2 AI Support Diagnostic Engine</h1>
            <div className="brand-subtitle">Autonomous Root-Cause Synthesis &amp; Operator Approval Portal</div>
          </div>
        </div>

        <div className="system-status-pills">
          <div className="status-chip online">
            <span className="status-dot"></span>
            <span>API Online (:8000)</span>
          </div>
          <div className="status-chip postgres">
            <span className="status-dot"></span>
            <span>Neon Cloud PostgreSQL Connected</span>
          </div>
        </div>

        <div className="nav-actions">
          <button id="btn-refresh-queue" className="btn-secondary" onClick={fetchTickets}>
            ↻ Refresh
          </button>
          <button id="btn-open-simulate-modal" className="btn-primary" onClick={() => setModalOpen(true)}>
            + Simulate Ticket
          </button>
        </div>
      </header>

      {/* Metrics Row */}
      <section className="metrics-grid">
        <div className="metric-card" id="kpi-total-tickets">
          <div>
            <div className="metric-label">Total Ingested Tickets</div>
            <div className="metric-value">{totalCount}</div>
          </div>
          <div className="metric-icon-wrap indigo">📑</div>
        </div>

        <div className="metric-card" id="kpi-awaiting-approval">
          <div>
            <div className="metric-label">Awaiting 1-Click Approval</div>
            <div className="metric-value" style={{ color: "#fbbf24" }}>{pendingCount}</div>
          </div>
          <div className="metric-icon-wrap amber">⏸️</div>
        </div>

        <div className="metric-card" id="kpi-resolved">
          <div>
            <div className="metric-label">Approved &amp; Resolved</div>
            <div className="metric-value" style={{ color: "#34d399" }}>{resolvedCount}</div>
          </div>
          <div className="metric-icon-wrap emerald">✅</div>
        </div>

        <div className="metric-card" id="kpi-audit-blocks">
          <div>
            <div className="metric-label">Hallucinations Blocked</div>
            <div className="metric-value" style={{ color: "#fb7185" }}>{auditBlockedCount}</div>
          </div>
          <div className="metric-icon-wrap rose">🛡️</div>
        </div>
      </section>

      {/* Main Content Workspace */}
      <main className="main-workspace">
        {/* Left: Tickets Queue */}
        <section className="queue-panel">
          <div className="queue-header">
            <div className="queue-title-row">
              <span className="queue-title">Ticket Queue ({filteredTickets.length})</span>
            </div>
            <input
              id="input-search-tickets"
              type="text"
              className="queue-search-input"
              placeholder="Filter by email, ID, or keywords..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="queue-filters">
            <button
              id="filter-all"
              className={`filter-btn ${filter === "all" ? "active" : ""}`}
              onClick={() => setFilter("all")}
            >
              All
            </button>
            <button
              id="filter-awaiting"
              className={`filter-btn ${filter === "awaiting_approval" ? "active" : ""}`}
              onClick={() => setFilter("awaiting_approval")}
            >
              Pending ({pendingCount})
            </button>
            <button
              id="filter-resolved"
              className={`filter-btn ${filter === "resolved" ? "active" : ""}`}
              onClick={() => setFilter("resolved")}
            >
              Resolved ({resolvedCount})
            </button>
            <button
              id="filter-rejected"
              className={`filter-btn ${filter === "rejected" ? "active" : ""}`}
              onClick={() => setFilter("rejected")}
            >
              Rejected
            </button>
          </div>

          <div className="tickets-scroll-list" id="ticket-queue-list">
            {filteredTickets.map((t) => (
              <div
                key={t.ticket_id}
                id={`ticket-card-${t.ticket_id}`}
                className={`ticket-item-card ${selectedTicket?.ticket_id === t.ticket_id ? "active" : ""}`}
                onClick={() => setSelectedTicket(t)}
              >
                <div className="ticket-top-meta">
                  <span className={`ticket-badge ${t.status}`}>
                    {t.status.replace("_", " ")}
                  </span>
                  <span className="ticket-timestamp">
                    {new Date(t.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <div className="ticket-user-email">{t.user_email || t.user_id}</div>
                <div className="ticket-issue-preview">{t.issue_description}</div>
                <div className="ticket-action-pill">
                  ⚙️ {t.proposed_action || "ANALYZING"}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Right: Diagnostic & Action Inspector */}
        <section className="inspector-panel" id="ticket-inspector-panel">
          {selectedTicket ? (
            <>
              {/* Header */}
              <div className="inspector-header">
                <div className="ticket-meta-headline">
                  <h2>{selectedTicket.user_email}</h2>
                  <div className="customer-chips-row">
                    <span className="ticket-id-tag">{selectedTicket.ticket_id}</span>
                    <span className="cust-chip">User ID: <strong>{selectedTicket.user_id}</strong></span>
                    {selectedTicket.stripe_customer_id && (
                      <span className="cust-chip">Stripe: <strong>{selectedTicket.stripe_customer_id}</strong></span>
                    )}
                    {selectedTicket.trace_id && (
                      <span className="cust-chip" style={{ color: "var(--accent-cyan)" }}>
                        Trace: <strong>{selectedTicket.trace_id}</strong>
                      </span>
                    )}
                  </div>
                </div>

                <span className={`ticket-badge ${selectedTicket.status}`} style={{ fontSize: "0.85rem", padding: "0.4rem 0.8rem" }}>
                  {selectedTicket.status.replace("_", " ")}
                </span>
              </div>

              {/* Customer Complaint */}
              <div className="complaint-box">
                <div className="section-label">📩 Customer Ticket Description</div>
                <div className="complaint-text">"{selectedTicket.issue_description}"</div>
              </div>

              {/* AI Diagnostic Reasoning Card */}
              <div className="ai-diagnosis-card">
                <div className="section-label" style={{ color: "#a5b4fc" }}>
                  🤖 Google Gemini Root-Cause Synthesis
                </div>
                <div className="root-cause-text">
                  {selectedTicket.root_cause || "Analyzing microservice error telemetry and payment records..."}
                </div>

                <div className="proposed-action-display">
                  <div className="action-pill-large">
                    {selectedTicket.proposed_action || "MANUAL_REVIEW"}
                  </div>
                  <div className="action-explanation">
                    {selectedTicket.proposed_action_details || "Action synthesized strictly based on ground-truth SQL FactSheet evidence."}
                  </div>
                </div>
              </div>

              {/* Anti-Hallucination Audit Card */}
              <div className={`audit-card ${selectedTicket.audit_passed ? "passed" : "rejected"}`} id="audit-verification-card">
                <div className="audit-icon">{selectedTicket.audit_passed ? "🛡️" : "🚨"}</div>
                <div>
                  <div className="audit-title">
                    {selectedTicket.audit_passed
                      ? "Anti-Hallucination Audit PASSED"
                      : "Anti-Hallucination Audit REJECTED"}
                  </div>
                  <div className="audit-desc">
                    {selectedTicket.audit_passed
                      ? "Proposed action is 100% mathematically grounded in PostgreSQL FactSheet data. Zero hallucination detected."
                      : (selectedTicket.audit_error || "Action violates FactSheet invariant safety rules. Safety override triggered.")}
                  </div>
                </div>
              </div>

              {/* Customer Email Draft */}
              {selectedTicket.customer_response_message && (
                <div className="customer-draft-box">
                  <div className="draft-header">
                    <div className="section-label">✉️ Pre-Drafted Customer Resolution Message</div>
                    <button id="btn-copy-email" className="copy-btn" onClick={copyEmail}>
                      {copied ? "✓ Copied!" : "📋 Copy Message"}
                    </button>
                  </div>
                  <div className="draft-content">{selectedTicket.customer_response_message}</div>
                </div>
              )}

              {/* Operator Action Bar */}
              <div className="operator-action-bar">
                <div className="action-bar-title">
                  <span>⚡ Human-in-the-Loop Operator Gate</span>
                </div>

                {selectedTicket.status === "awaiting_approval" ? (
                  <>
                    <input
                      id="input-operator-notes"
                      type="text"
                      className="operator-input"
                      placeholder="Optional operator notes or sign-off remarks..."
                      value={operatorNotes}
                      onChange={(e) => setOperatorNotes(e.target.value)}
                    />
                    <div className="operator-btn-row">
                      <button
                        id="btn-approve-action"
                        className="btn-approve"
                        onClick={handleApprove}
                        disabled={actionLoading}
                      >
                        {actionLoading ? "Executing Database Mutation..." : `✓ 1-Click Approve (${selectedTicket.proposed_action})`}
                      </button>
                      <button
                        id="btn-reject-action"
                        className="btn-reject"
                        onClick={handleReject}
                        disabled={actionLoading}
                      >
                        ✕ Reject &amp; Escalate
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="resolved-stamp-box">
                    <div className="resolved-stamp-text">
                      {selectedTicket.status === "resolved" ? "✓ Resolved & Applied to PostgreSQL" : "✕ Escalated to Tier-3"}
                    </div>
                    {selectedTicket.operator_notes && (
                      <div className="resolved-stamp-notes">
                        Notes: {selectedTicket.operator_notes}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="inspector-empty">
              <div className="inspector-empty-icon">📂</div>
              <h3>No Ticket Selected</h3>
              <p>Select a ticket from the left queue or click "+ Simulate Ticket" to ingest a new issue.</p>
            </div>
          )}
        </section>
      </main>

      {/* Simulate Modal */}
      {modalOpen && (
        <div className="modal-overlay" onClick={() => setModalOpen(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Simulate Customer Ticket</h2>
              <button className="modal-close-btn" onClick={() => setModalOpen(false)}>✕</button>
            </div>

            <div className="presets-container">
              <div className="form-label">Quick Scenario Presets:</div>
              <div className="preset-btn-grid">
                {PRESETS.map((p, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className="preset-chip"
                    onClick={() => loadPreset(p)}
                  >
                    ⚡ {p.name}
                  </button>
                ))}
              </div>
            </div>

            <form onSubmit={handleDiagnoseNew}>
              <div className="form-field">
                <label className="form-label">User ID</label>
                <input
                  id="form-user-id"
                  type="text"
                  className="form-input"
                  value={formUserId}
                  onChange={(e) => setFormUserId(e.target.value)}
                  required
                />
              </div>

              <div className="form-field">
                <label className="form-label">Customer Email</label>
                <input
                  id="form-user-email"
                  type="email"
                  className="form-input"
                  value={formEmail}
                  onChange={(e) => setFormEmail(e.target.value)}
                  required
                />
              </div>

              <div className="form-field">
                <label className="form-label">Stripe Customer ID</label>
                <input
                  id="form-stripe-id"
                  type="text"
                  className="form-input"
                  value={formStripeId}
                  onChange={(e) => setFormStripeId(e.target.value)}
                />
              </div>

              <div className="form-field">
                <label className="form-label">Issue Description (Include Trace ID)</label>
                <textarea
                  id="form-issue-desc"
                  className="form-input"
                  rows={3}
                  value={formIssue}
                  onChange={(e) => setFormIssue(e.target.value)}
                  required
                />
              </div>

              <button
                id="btn-submit-diagnose"
                type="submit"
                className="modal-submit-btn"
                disabled={diagnosing}
              >
                {diagnosing ? "Reasoning with Google Gemini & Auditing..." : "Run AI Diagnosis & Audit →"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
