"use client";

const GATES = [
  {
    name: "Requirements Gate",
    threshold: 90,
    maxIterations: 5,
    metrics: [
      { name: "Completeness", weight: 25, threshold: 90, critical: true },
      { name: "Clarity", weight: 20, threshold: 85, critical: false },
      { name: "Consistency", weight: 20, threshold: 85, critical: false },
      { name: "Feasibility", weight: 20, threshold: 85, critical: false },
      { name: "Business Alignment", weight: 15, threshold: 90, critical: true },
    ],
  },
  {
    name: "Architecture Gate",
    threshold: 90,
    maxIterations: 5,
    metrics: [
      { name: "Scalability", weight: 25, threshold: 90, critical: true },
      { name: "Reliability", weight: 20, threshold: 85, critical: true },
      { name: "Security", weight: 25, threshold: 90, critical: true },
      { name: "Maintainability", weight: 15, threshold: 80, critical: false },
      { name: "Cost Efficiency", weight: 15, threshold: 75, critical: false },
    ],
  },
  {
    name: "Code Gate",
    threshold: 92,
    maxIterations: 7,
    metrics: [
      { name: "Complexity", weight: 20, threshold: 85, critical: false },
      { name: "Maintainability", weight: 20, threshold: 85, critical: false },
      { name: "Testability", weight: 20, threshold: 90, critical: true },
      { name: "Performance", weight: 20, threshold: 85, critical: false },
      { name: "Security", weight: 20, threshold: 95, critical: true },
    ],
  },
  {
    name: "Testing Gate",
    threshold: 95,
    maxIterations: 5,
    metrics: [
      { name: "Coverage", weight: 30, threshold: 90, critical: true },
      { name: "Mutation Score", weight: 30, threshold: 80, critical: true },
      { name: "Reliability", weight: 20, threshold: 95, critical: true },
      { name: "Edge Cases", weight: 20, threshold: 85, critical: false },
    ],
  },
  {
    name: "Security Gate",
    threshold: 98,
    maxIterations: 3,
    metrics: [
      { name: "Vulnerability Scan", weight: 35, threshold: 95, critical: true },
      { name: "LLM Review", weight: 25, threshold: 95, critical: true },
      { name: "Secret Detection", weight: 20, threshold: 100, critical: true },
      { name: "Dependency Audit", weight: 10, threshold: 90, critical: false },
      { name: "Compliance", weight: 10, threshold: 90, critical: false },
    ],
  },
  {
    name: "Deployment Gate",
    threshold: 95,
    maxIterations: 3,
    metrics: [
      { name: "Stability", weight: 40, threshold: 95, critical: true },
      { name: "Availability", weight: 35, threshold: 99, critical: true },
      { name: "Performance", weight: 25, threshold: 90, critical: false },
    ],
  },
];

export default function QualityPage() {
  return (
    <div>
      <header className="page-header">
        <div>
          <h2>Quality Gates</h2>
          <p>6 gates · 27 metrics · Recursive loop controller</p>
        </div>
      </header>

      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        {GATES.map((gate) => (
          <div className="card" key={gate.name}>
            <div className="card-header">
              <div>
                <h3>{gate.name}</h3>
                <div className="card-subtitle">
                  Threshold: ≥ {gate.threshold} · Max loops: {gate.maxIterations}
                </div>
              </div>
              <span className={`badge ${gate.threshold >= 98 ? "badge-danger" : gate.threshold >= 95 ? "badge-warning" : "badge-primary"}`}>
                {gate.threshold >= 98 ? "STRICT" : gate.threshold >= 95 ? "HIGH" : "STANDARD"}
              </span>
            </div>
            <div className="card-body">
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "0.75rem" }}>
                {gate.metrics.map((m) => (
                  <div key={m.name} style={{
                    background: "var(--bg-elevated)",
                    borderRadius: "var(--radius-sm)",
                    padding: "0.75rem 1rem",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    borderLeft: `3px solid ${m.critical ? "var(--accent-danger)" : "var(--accent-primary)"}`,
                  }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: "0.85rem" }}>{m.name}</div>
                      <div style={{ fontSize: "0.68rem", color: "var(--text-tertiary)" }}>
                        Weight: {(m.weight * 100).toFixed(0)}% · Threshold: ≥ {m.threshold}
                      </div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      {m.critical && (
                        <span className="badge badge-danger" style={{ fontSize: "0.55rem", padding: "0.1rem 0.4rem" }}>
                          CRITICAL
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
