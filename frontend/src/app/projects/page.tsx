export default function ProjectsPage() {
  return (
    <div>
      <h2 className="page-title">Projects</h2>
      <div className="card">
        <h3>Active Projects</h3>
        <table>
          <thead>
            <tr><th>Name</th><th>Status</th><th>Phase</th><th>Tasks</th><th>Score</th></tr>
          </thead>
          <tbody>
            <tr>
              <td>SaaS Dashboard App</td>
              <td><span className="badge green">active</span></td>
              <td>Phase 3: Development</td>
              <td>12/18</td>
              <td>93.5</td>
            </tr>
            <tr>
              <td>E-Commerce API</td>
              <td><span className="badge green">active</span></td>
              <td>Phase 2: Architecture</td>
              <td>5/15</td>
              <td>91.2</td>
            </tr>
            <tr>
              <td>Chat Application</td>
              <td><span className="badge blue">completed</span></td>
              <td>Phase 6: Learning</td>
              <td>24/24</td>
              <td>95.8</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
