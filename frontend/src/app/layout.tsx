"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import "./globals.css";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: "◉" },
  { href: "/projects", label: "Projects", icon: "⊞", badge: "3" },
  { href: "/agents", label: "Agents", icon: "⬡", badge: "12" },
  { href: "/artifacts", label: "Artifacts", icon: "▤" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <html lang="en">
      <body>
        <div className="app-layout">
          <aside className="sidebar">
            <div className="sidebar-brand">
              <h1>AISC</h1>
              <span>Autonomous AI Software Company</span>
            </div>
            <nav className="sidebar-nav">
              <div className="nav-section">Overview</div>
              {NAV_ITEMS.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`nav-item ${pathname === item.href ? "active" : ""}`}
                >
                  <span className="nav-icon">{item.icon}</span>
                  {item.label}
                  {item.badge && <span className="nav-badge">{item.badge}</span>}
                </Link>
              ))}
              <div className="nav-section">Operations</div>
              <Link href="/pipeline" className={`nav-item ${pathname === "/pipeline" ? "active" : ""}`}>
                <span className="nav-icon">⇢</span>
                Pipeline
              </Link>
              <Link href="/quality" className={`nav-item ${pathname === "/quality" ? "active" : ""}`}>
                <span className="nav-icon">✦</span>
                Quality Gates
              </Link>
            </nav>
            <div className="sidebar-footer">
              <div className="avatar">AS</div>
              <div>
                <div style={{ fontWeight: 600, fontSize: "0.8rem" }}>AISC System</div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.3rem" }}>
                  <span className="status-dot online" />
                  Operational
                </div>
              </div>
            </div>
          </aside>
          <main className="main-content">{children}</main>
        </div>
      </body>
    </html>
  );
}
