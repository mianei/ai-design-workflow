import { NavLink } from 'react-router-dom';

const links = [
  { to: '/', label: 'Dashboard', end: true },
  { to: 'research', label: 'Research Board' },
  { to: 'concepts', label: 'Concept Board' },
  { to: 'brief', label: 'Brief Editor' },
  { to: 'history', label: 'Decision History' },
];

export function TopBar({
  projectId,
  title,
}: {
  projectId?: number;
  title?: string;
}) {
  return (
    <header className="topbar">
      <div className="brand">
        <strong>Designflow</strong>
        <span>{title ? title : 'AI Product Concept Workflow Agent'}</span>
      </div>
      {projectId ? (
        <nav className="nav-pills">
          <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : undefined)}>
            Projects
          </NavLink>
          {links.slice(1).map((l) => (
            <NavLink
              key={l.to}
              to={`/projects/${projectId}/${l.to}`}
              className={({ isActive }) => (isActive ? 'active' : undefined)}
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
      ) : null}
    </header>
  );
}
