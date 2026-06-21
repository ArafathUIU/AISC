export default function DashboardPage() {
  return (
    <div>
      <h2 className="page-title">Dashboard</h2>
      <div className="stats-grid">
        <StatCard label="Active Projects" value="3" cls="blue" />
        <StatCard label="Agents Running" value="8" cls="green" />
        <StatCard label="Tests Passing" value="177" cls="green" />
        <StatCard label="Alerts" value="1" cls="yellow" />
      </div>
      <div className="card">
        <h3>System Status</h3>
        <table>
          <thead>
            <tr><th>Service</th><th>Status</th><th>Uptime</th></tr>
          </thead>
          <tbody>
            <ServiceRow name="auth-service" status="healthy" uptime="4h 23m" />
            <ServiceRow name="orchestrator-service" status="healthy" uptime="4h 22m" />
            <ServiceRow name="agent-runtime" status="healthy" uptime="4h 21m" />
            <ServiceRow name="memory-service" status="degraded" uptime="4h 20m" />
            <ServiceRow name="scoring-engine" status="healthy" uptime="4h 19m" />
            <ServiceRow name="rag-service" status="healthy" uptime="4h 18m" />
            <ServiceRow name="debate-service" status="healthy" uptime="4h 17m" />
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatCard({ label, value, cls }: { label: string; value: string; cls: string }) {
  return (
    <div className="stat-card">
      <div className="label">{label}</div>
      <div className={`value ${cls}`}>{value}</div>
    </div>
  );
}

function ServiceRow({ name, status, uptime }: { name: string; status: string; uptime: string }) {
  return (
    <tr>
      <td>{name}</td>
      <td><span className={`badge ${status === "healthy" ? "green" : "yellow"}`}>{status}</span></td>
      <td>{uptime}</td>
    </tr>
  );
}
