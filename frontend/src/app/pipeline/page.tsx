"use client";

const STEPS = [
  { label: "Requirements", status: "completed", agent: "pm-agent", score: 94 },
  { label: "Research", status: "completed", agent: "research-agent", score: 88 },
  { label: "Architecture", status: "completed", agent: "architect-agent", score: 91 },
  { label: "Development", status: "active", agent: "developer-agent", score: 88 },
  { label: "Testing", status: "pending", agent: "qa-agent", score: 0 },
  { label: "Security", status: "pending", agent: "security-agent", score: 0 },
  { label: "Deployment", status: "pending", agent: "devops-agent", score: 0 },
];

const GATES = [
  { name: "Requirements Gate", threshold: 90, score: 94, passed: true, metrics: [
    { name: "Completeness", value: 95 },
    { name: "Clarity", value: 92 },
    { name: "Consistency", value: 90 },
    { name: "Feasibility", value: 91 },
    { name: "Business Alignment", value: 94 },
  ]},
  { name: "Architecture Gate", threshold: 90, score: 91, passed: true, metrics: [
    { name: "Scalability", value: 88 },
    { name: "Reliability", value: 92 },
    { name: "Security", value: 90 },
    { name: "Maintainability", value: 93 },
    { name: "Cost Efficiency", value: 90 },
  ]},
  { name: "Code Gate", threshold: 92, score: 88, passed: false, metrics: [
    { name: "Complexity", value: 90 },
    { name: "Maintainability", value: 92 },
    { name: "Testability", value: 85 },
    { name: "Performance", value: 88 },
    { name: "Security", value: 86 },
  ]},
];

export default function PipelinePage() {
  return (
    <div>
      <header className="page-header">
        <div>
          <h2>Pipeline</h2>
          <p>SaaS Dashboard App · Workflow execution</p>
        </div>
        <div className="header-actions">
          <span className="badge badge-primary">Phase 3: Development</span>
        </div>
      </header>

      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <div className="card-body">
          <div className="pipeline-steps">
            {STEPS.map((step, i) => (
              <div key={step.label} className="pipeline-step" style={{ flex: 1 }}>
                <div
                  className={`pipeline-connector ${step.status === "completed" ? "completed" : ""}`}
                  style={{ display: i < STEPS.length - 1 ? "block" : "none" }}
                />
                <div className={`step-icon ${step.status}`}>
                  {step.status === "completed" ? "✓" : step.status === "active" ? "⟳" : "○"}
                </div>
                <div className={`step-label ${step.status}`}>{step.label}</div>
                <div style={{ fontSize: "0.65rem", color: "var(--text-tertiary)", marginTop: "0.2rem" }}>
                  {step.agent}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <h3>Quality Gates</h3>
            <span className="card-subtitle">3 of 7 passed</span>
          </div>
          <div className="card-body no-padding">
            <table>
              <thead>
                <tr><th>Gate</th><th>Threshold</th><th>Score</th><th>Status</th></tr>
              </thead>
              <tbody>
                {STEPS.filter(s => s.status !== "pending").map(s => (
                  <tr key={s.label}>
                    <td style={{ fontWeight: 500 }}>{s.label} Gate</td>
                    <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem" }}>≥ 90</td>
                    <td style={{ fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: "0.9rem",
                      color: s.score >= 90 ? "var(--accent-success)" : "var(--accent-warning)",
                    }}>
                      {s.score || "—"}
                    </td>
                    <td>
                      <span className={`badge ${s.score >= 90 ? "badge-success" : s.score > 0 ? "badge-warning" : "badge-neutral"}`}>
                        {s.score >= 90 ? "passed" : s.score > 0 ? "looping" : "pending"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Active Gate: Code</h3>
            <span className="badge badge-warning">Looping · 4/7</span>
          </div>
          <div className="card-body">
            {GATES[2].metrics.map(m => (
              <div className="metric-row" key={m.name}>
                <div className="metric-name">{m.name}</div>
                <div className="metric-bar">
                  <div
                    className="metric-fill"
                    style={{
                      width: `${m.value}%`,
                      background: m.value >= 90 ? "var(--accent-success)" : m.value >= 85 ? "var(--accent-warning)" : "var(--accent-danger)",
                    }}
                  />
                </div>
                <div className="metric-value" style={{
                  color: m.value >= 90 ? "var(--accent-success)" : m.value >= 85 ? "var(--accent-warning)" : "var(--accent-danger)",
                }}>
                  {m.value}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
