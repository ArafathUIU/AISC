const MOCK_ARTIFACTS = [
  { name: "PRD: SaaS Dashboard", type: "prd", gate: "requirements", score: 94, status: "approved" },
  { name: "Architecture: User Service", type: "architecture_doc", gate: "architecture", score: 91, status: "approved" },
  { name: "Generated code: models/user.py", type: "source_code", gate: "code", score: 88, status: "in_review" },
  { name: "Test suite: user endpoints", type: "test_file", gate: "testing", score: 96, status: "approved" },
  { name: "Security report: user-service", type: "security_report", gate: "security", score: 99, status: "approved" },
];

export default function ArtifactsPage() {
  return (
    <div>
      <h2 className="page-title">Artifacts</h2>
      <div className="card">
        <table>
          <thead>
            <tr><th>Name</th><th>Type</th><th>Gate</th><th>Score</th><th>Status</th></tr>
          </thead>
          <tbody>
            {MOCK_ARTIFACTS.map((a) => (
              <tr key={a.name}>
                <td>{a.name}</td>
                <td><span className="badge blue">{a.type}</span></td>
                <td>{a.gate}</td>
                <td style={{ fontWeight: 600, color: a.score >= 90 ? "var(--success)" : "var(--warning)" }}>
                  {a.score}
                </td>
                <td>
                  <span className={`badge ${a.status === "approved" ? "green" : "yellow"}`}>
                    {a.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
