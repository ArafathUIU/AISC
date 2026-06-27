"use client";

import { useEffect, useState } from "react";

export default function DashboardPage() {
  return (
    <div>
      <header className="page-header">
        <div>
          <h2>Dashboard</h2>
          <p>System overview · Real-time monitoring</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary">Export Report</button>
          <button className="btn btn-primary">+ New Project</button>
        </div>
      </header>

      <div className="stats-row">
        <AnimatedStatCard
          icon="⊞" iconBg="rgba(108,140,255,0.12)" iconColor="var(--accent-primary)"
          value={3} label="Active Projects" change="+1 this week" changeDir="up"
        />
        <AnimatedStatCard
          icon="⬡" iconBg="rgba(72,187,120,0.12)" iconColor="var(--accent-success)"
          value={8} label="Agents Running" change="All systems nominal" changeDir="up"
        />
        <AnimatedStatCard
          icon="✓" iconBg="rgba(72,187,120,0.12)" iconColor="var(--accent-success)"
          value={177} label="Tests Passing" change="0 failures" changeDir="up"
        />
        <AnimatedStatCard
          icon="◉" iconBg="rgba(245,166,35,0.12)" iconColor="var(--accent-warning)"
          value={1} label="Active Alerts" change="1 requires attention" changeDir="down"
        />
      </div>

      <div className="grid-2" style={{ marginBottom: "1rem" }}>
        <div className="card">
          <div className="card-header">
            <h3>Service Health</h3>
            <span className="badge badge-success">7 of 7 Healthy</span>
          </div>
          <div className="card-body no-padding">
            <table>
              <thead>
                <tr><th>Service</th><th>Status</th><th>Uptime</th><th>Latency</th></tr>
              </thead>
              <tbody>
                <ServiceRow name="auth-service" status="healthy" uptime="14h 23m" latency="12ms" />
                <ServiceRow name="orchestrator-service" status="healthy" uptime="14h 22m" latency="8ms" />
                <ServiceRow name="agent-runtime" status="healthy" uptime="14h 21m" latency="15ms" />
                <ServiceRow name="memory-service" status="healthy" uptime="14h 20m" latency="22ms" />
                <ServiceRow name="rag-service" status="healthy" uptime="14h 18m" latency="18ms" />
                <ServiceRow name="debate-service" status="healthy" uptime="14h 17m" latency="6ms" />
                <ServiceRow name="scoring-engine" status="healthy" uptime="14h 16m" latency="10ms" />
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Quality Score Trend</h3>
            <span className="card-subtitle">Last 7 days</span>
          </div>
          <div className="card-body">
            <Sparkline data={[88, 90, 89, 92, 91, 94, 93.5]} height={120} color="var(--accent-primary)" />
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: "0.75rem" }}>
              <span style={{ color: "var(--text-tertiary)", fontSize: "0.7rem" }}>Mon</span>
              <span style={{ color: "var(--text-tertiary)", fontSize: "0.7rem" }}>Tue</span>
              <span style={{ color: "var(--text-tertiary)", fontSize: "0.7rem" }}>Wed</span>
              <span style={{ color: "var(--text-tertiary)", fontSize: "0.7rem" }}>Thu</span>
              <span style={{ color: "var(--text-tertiary)", fontSize: "0.7rem" }}>Fri</span>
              <span style={{ color: "var(--text-tertiary)", fontSize: "0.7rem" }}>Sat</span>
              <span style={{ color: "var(--text-tertiary)", fontSize: "0.7rem" }}>Sun</span>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Recent Activity</h3>
        </div>
        <div className="card-body no-padding">
          <table>
            <thead>
              <tr><th>Event</th><th>Agent</th><th>Project</th><th>Time</th></tr>
            </thead>
            <tbody>
              <tr>
                <td><span className="badge badge-success">APPROVED</span> PRD</td>
                <td>pm-agent</td>
                <td>SaaS Dashboard</td>
                <td style={{ color: "var(--text-tertiary)", fontSize: "0.8rem" }}>2 min ago</td>
              </tr>
              <tr>
                <td><span className="badge badge-primary">GENERATED</span> Code</td>
                <td>developer-agent</td>
                <td>E-Commerce API</td>
                <td style={{ color: "var(--text-tertiary)", fontSize: "0.8rem" }}>8 min ago</td>
              </tr>
              <tr>
                <td><span className="badge badge-warning">IN REVIEW</span> Architecture</td>
                <td>architect-agent</td>
                <td>SaaS Dashboard</td>
                <td style={{ color: "var(--text-tertiary)", fontSize: "0.8rem" }}>15 min ago</td>
              </tr>
              <tr>
                <td><span className="badge badge-success">PASSED</span> Tests</td>
                <td>qa-agent</td>
                <td>Chat App</td>
                <td style={{ color: "var(--text-tertiary)", fontSize: "0.8rem" }}>22 min ago</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function AnimatedStatCard({ icon, iconBg, iconColor, value, label, change, changeDir }: {
  icon: string; iconBg: string; iconColor: string; value: number;
  label: string; change: string; changeDir: string;
}) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    const timer = setTimeout(() => setDisplay(value), 100);
    return () => clearTimeout(timer);
  }, [value]);

  return (
    <div className="stat-card" style={{ animation: "fadeIn 0.4s ease" }}>
      <div className="stat-icon" style={{ background: iconBg, color: iconColor }}>{icon}</div>
      <div className="stat-value" style={{ fontFamily: "var(--font-mono)" }}>{display}</div>
      <div className="stat-label">{label}</div>
      <div className={`stat-change ${changeDir}`}>{change}</div>
    </div>
  );
}

function ServiceRow({ name, status, uptime, latency }: {
  name: string; status: string; uptime: string; latency: string;
}) {
  return (
    <tr>
      <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>{name}</td>
      <td>
        <span className={`badge badge-${status === "healthy" ? "success" : "warning"}`}>
          <span className={`status-dot ${status === "healthy" ? "online" : "busy"}`} />
          {status}
        </span>
      </td>
      <td style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
        {uptime}
      </td>
      <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>{latency}</td>
    </tr>
  );
}

function Sparkline({ data, height, color }: { data: number[]; height: number; color: string }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const points = data.map((v, i) => `${(i / (data.length - 1)) * 100},${100 - ((v - min) / range) * 80 - 10}`).join(" ");

  return (
    <svg width="100%" height={height} viewBox="0 0 100 100" preserveAspectRatio="none">
      <defs>
        <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={`0,100 ${points} 100,100`} fill="url(#sparkGrad)" />
      <polyline points={points} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
