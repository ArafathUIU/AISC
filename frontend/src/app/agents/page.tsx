const MOCK_AGENTS = [
  { name: "pm-agent", type: "Product Manager", status: "idle", task: "None" },
  { name: "research-agent", type: "Research", status: "idle", task: "None" },
  { name: "architect-agent", type: "Architect", status: "busy", task: "Design user service" },
  { name: "developer-agent", type: "Developer", status: "busy", task: "Generate API code" },
  { name: "qa-agent", type: "QA", status: "idle", task: "None" },
  { name: "security-agent", type: "Security", status: "busy", task: "Audit dependencies" },
  { name: "devops-agent", type: "DevOps", status: "idle", task: "None" },
  { name: "monitoring-agent", type: "Monitoring", status: "idle", task: "Watching metrics" },
  { name: "self-healing-agent", type: "Self-Healing", status: "idle", task: "None" },
  { name: "learning-agent", type: "Learning", status: "busy", task: "Extracting patterns" },
  { name: "knowledge-agent", type: "Knowledge", status: "idle", task: "None" },
  { name: "orchestrator", type: "Orchestrator", status: "busy", task: "Managing workflow" },
];

export default function AgentsPage() {
  return (
    <div>
      <h2 className="page-title">Agents</h2>
      <div className="agent-grid">
        {MOCK_AGENTS.map((agent) => (
          <div className="agent-card" key={agent.name}>
            <div className="name">{agent.name}</div>
            <div className="type">{agent.type}</div>
            <span className={`badge ${agent.status === "busy" ? "blue" : agent.status === "idle" ? "green" : "yellow"}`}>
              {agent.status}
            </span>
            {agent.task !== "None" && (
              <div style={{ marginTop: "0.75rem", fontSize: "0.85rem", color: "var(--text-muted)" }}>
                {agent.task}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
