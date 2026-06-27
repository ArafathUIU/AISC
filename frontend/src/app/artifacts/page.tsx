"use client";

const ARTIFACTS = [
  { name: "PRD: SaaS Dashboard App", type: "prd", gate: "requirements", score: 94, status: "approved", iterations: 2, agent: "pm-agent" },
  { name: "User Stories: SaaS Dashboard", type: "user_story", gate: "requirements", score: 91, status: "approved", iterations: 1, agent: "pm-agent" },
  { name: "Research: React vs Vue Comparison", type: "research_report", gate: "requirements", score: 88, status: "in_review", iterations: 3, agent: "research-agent" },
  { name: "Architecture: User Service Design", type: "architecture_doc", gate: "architecture", score: 91, status: "approved", iterations: 2, agent: "architect-agent" },
  { name: "API Contract: User Service (OpenAPI)", type: "api_spec", gate: "architecture", score: 93, status: "approved", iterations: 1, agent: "architect-agent" },
  { name: "Generated Code: models/user.py", type: "source_code", gate: "code", score: 88, status: "in_review", iterations: 4, agent: "developer-agent" },
  { name: "Generated Code: routes/users.py", type: "source_code", gate: "code", score: 92, status: "approved", iterations: 2, agent: "developer-agent" },
  { name: "Test Suite: user-endpoints", type: "test_file", gate: "testing", score: 96, status: "approved", iterations: 1, agent: "qa-agent" },
  { name: "Security Report: user-service", type: "security_report", gate: "security", score: 99, status: "approved", iterations: 1, agent: "security-agent" },
  { name: "Deployment Config: user-service", type: "deployment_config", gate: "deployment", score: 95, status: "approved", iterations: 1, agent: "devops-agent" },
];

export default function ArtifactsPage() {
  const gateColors: Record<string, string> = {
    requirements: "var(--accent-primary)",
    architecture: "#a78bfa",
    code: "var(--accent-warning)",
    testing: "var(--accent-success)",
    security: "var(--accent-danger)",
    deployment: "var(--accent-secondary)",
  };

  return (
    <div>
      <header className="page-header">
        <div>
          <h2>Artifacts</h2>
          <p>10 artifacts · 8 approved · 2 in review</p>
        </div>
      </header>

      <div className="card">
        <div className="card-body no-padding">
          <table>
            <thead>
              <tr><th>Artifact</th><th>Type</th><th>Gate</th><th>Score</th><th>Iterations</th><th>Status</th></tr>
            </thead>
            <tbody>
              {ARTIFACTS.map((a) => (
                <tr key={a.name}>
                  <td style={{ fontWeight: 500 }}>{a.name}</td>
                  <td>
                    <span className="badge badge-neutral" style={{
                      borderLeft: `3px solid ${gateColors[a.gate] || "var(--text-tertiary)"}`,
                    }}>
                      {a.type}
                    </span>
                  </td>
                  <td style={{ fontSize: "0.8rem", color: gateColors[a.gate] || "var(--text-secondary)" }}>
                    {a.gate}
                  </td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <div className="score-bar" style={{ width: 80 }}>
                        <div
                          className={`score-bar-fill ${a.score >= 90 ? "high" : a.score >= 80 ? "mid" : "low"}`}
                          style={{ width: `${a.score}%` }}
                        />
                      </div>
                      <span style={{
                        fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: "0.82rem",
                        color: a.score >= 90 ? "var(--accent-success)" : "var(--accent-warning)",
                      }}>
                        {a.score}
                      </span>
                    </div>
                  </td>
                  <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem", textAlign: "center" }}>
                    {a.iterations}
                  </td>
                  <td>
                    <span className={`badge ${a.status === "approved" ? "badge-success" : "badge-warning"}`}>
                      {a.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
