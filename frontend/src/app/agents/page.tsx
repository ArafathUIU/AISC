"use client";

const AGENTS = [
  { name: "orchestrator", type: "Orchestrator", status: "busy", task: "Managing SaaS Dashboard workflow", metrics: { tasks: 18, score: 94 } },
  { name: "pm-agent", type: "Product Manager", status: "idle", task: "Awaiting next project", metrics: { tasks: 12, score: 93 } },
  { name: "research-agent", type: "Research", status: "idle", task: "Research complete", metrics: { tasks: 8, score: 91 } },
  { name: "architect-agent", type: "Architect", status: "busy", task: "Designing user-service topology", metrics: { tasks: 15, score: 90 } },
  { name: "developer-agent", type: "Developer", status: "busy", task: "Generating API endpoints for /users", metrics: { tasks: 22, score: 92 } },
  { name: "qa-agent", type: "QA", status: "busy", task: "Running mutation tests on user-service", metrics: { tasks: 19, score: 96 } },
  { name: "security-agent", type: "Security", status: "idle", task: "Last scan: 0 critical findings", metrics: { tasks: 14, score: 99 } },
  { name: "devops-agent", type: "DevOps", status: "idle", task: "Deployment ready for staging", metrics: { tasks: 10, score: 95 } },
  { name: "monitoring-agent", type: "Monitoring", status: "idle", task: "Watching 12 services", metrics: { tasks: 0, score: 100 } },
  { name: "self-healing-agent", type: "Self-Healing", status: "idle", task: "No active incidents", metrics: { tasks: 3, score: 97 } },
  { name: "learning-agent", type: "Learning", status: "busy", task: "Extracting patterns from 500 records", metrics: { tasks: 6, score: 89 } },
  { name: "knowledge-agent", type: "Knowledge", status: "idle", task: "Graph updated 5min ago", metrics: { tasks: 4, score: 94 } },
];

export default function AgentsPage() {
  return (
    <div>
      <header className="page-header">
        <div>
          <h2>Agents</h2>
          <p>12 agents · 8 idle · 4 busy · 0 errors</p>
        </div>
        <div className="header-actions">
          <span className="badge badge-success">All Systems Operational</span>
        </div>
      </header>

      <div className="agent-grid">
        {AGENTS.map((agent) => (
          <div className="agent-card" key={agent.name}>
            <div className="agent-header">
              <div>
                <div className="agent-name">{agent.name}</div>
                <div className="agent-type">{agent.type}</div>
              </div>
              <span className={`badge ${agent.status === "busy" ? "badge-primary" : "badge-success"}`}>
                <span className={`status-dot ${agent.status === "busy" ? "busy" : "online"}`} />
                {agent.status}
              </span>
            </div>
            {agent.task !== "None" && (
              <div className="agent-task">{agent.task}</div>
            )}
            <div style={{ display: "flex", gap: "1.5rem", marginTop: "0.75rem" }}>
              <div>
                <div style={{ fontSize: "0.6rem", color: "var(--text-tertiary)", textTransform: "uppercase", letterSpacing: "0.1em" }}>
                  Tasks
                </div>
                <div style={{ fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: "0.9rem" }}>
                  {agent.metrics.tasks}
                </div>
              </div>
              <div>
                <div style={{ fontSize: "0.6rem", color: "var(--text-tertiary)", textTransform: "uppercase", letterSpacing: "0.1em" }}>
                  Avg Score
                </div>
                <div style={{
                  fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: "0.9rem",
                  color: agent.metrics.score >= 90 ? "var(--accent-success)" : "var(--accent-warning)",
                }}>
                  {agent.metrics.score}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
