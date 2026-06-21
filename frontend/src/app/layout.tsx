import Link from "next/link";
import "./globals.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="layout">
          <aside className="sidebar">
            <h1>AISC</h1>
            <Link href="/">Dashboard</Link>
            <Link href="/projects">Projects</Link>
            <Link href="/agents">Agents</Link>
            <Link href="/artifacts">Artifacts</Link>
          </aside>
          <main className="main">{children}</main>
        </div>
      </body>
    </html>
  );
}
