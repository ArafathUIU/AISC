"use client";

export default function ProjectsPage() {
  return (
    <div>
      <header className="page-header">
        <div>
          <h2>Projects</h2>
          <p>Manage autonomous software projects</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-primary">+ New Project</button>
        </div>
      </header>

      <div className="card">
        <div className="card-body no-padding">
          <table>
            <thead>
              <tr><th>Project</th><th>Status</th><th>Phase</th><th>Agents</th><th>Quality</th><th>Progress</th></tr>
            </thead>
            <tbody>
              <ProjectRow name="SaaS Dashboard App" status="active" phase="Phase 3: Development" agents={3} score={93.5} progress={67} />
              <ProjectRow name="E-Commerce API" status="active" phase="Phase 2: Architecture" agents={2} score={91.2} progress={33} />
              <ProjectRow name="Chat Application" status="completed" phase="Phase 6: Learning" agents={6} score={95.8} progress={100} />
              <ProjectRow name="Analytics Pipeline" status="active" phase="Phase 1: Requirements" agents={1} score={88.0} progress={15} />
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function ProjectRow({ name, status, phase, agents, score, progress }: {
  name: string; status: string; phase: string; agents: number; score: number; progress: number;
}) {
  return (
    <tr>
      <td style={{ fontWeight: 600 }}>{name}</td>
      <td>
        <span className={`badge ${status === "active" ? "badge-primary" : "badge-success"}`}>
          {status}
        </span>
      </td>
      <td style={{ color: "var(--text-secondary)", fontSize: "0.82rem" }}>{phase}</td>
      <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem" }}>{agents} active</td>
      <td>
        <div style={{ display: "flex", alignItems: "center", gap: "0.65rem" }}>
          <div className="score-bar" style={{ width: 100 }}>
            <div
              className={`score-bar-fill ${score >= 90 ? "high" : score >= 80 ? "mid" : "low"}`}
              style={{ width: `${score}%` }}
            />
          </div>
          <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: "0.85rem",
            color: score >= 90 ? "var(--accent-success)" : "var(--accent-warning)" }}>
            {score}
          </span>
        </div>
      </td>
      <td>
        <div style={{ display: "flex", alignItems: "center", gap: "0.65rem" }}>
          <div className="score-bar" style={{ width: 80 }}>
            <div className="score-bar-fill high" style={{ width: `${progress}%` }} />
          </div>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem", color: "var(--text-tertiary)" }}>
            {progress}%
          </span>
        </div>
      </td>
    </tr>
  );
}
