import { useCallback, useEffect, useState } from 'react';
import { Navigate, Route, Routes, useParams } from 'react-router-dom';
import { api } from './api';
import { BriefEditor } from './pages/BriefEditor';
import { ConceptBoard } from './pages/ConceptBoard';
import { Dashboard } from './pages/Dashboard';
import { DecisionHistory } from './pages/DecisionHistory';
import { ResearchBoard } from './pages/ResearchBoard';
import type { ProjectDetail, ProjectSummary } from './types';

function ProjectRoutes({
  project,
  setProject,
}: {
  project: ProjectDetail;
  setProject: (p: ProjectDetail) => void;
}) {
  const rerun = async () => {
    await api.rerun(project.id);
    const fresh = await api.getProject(project.id);
    setProject(fresh);
  };

  return (
    <Routes>
      <Route
        path="research"
        element={<ResearchBoard project={project} onRerun={rerun} />}
      />
      <Route
        path="concepts"
        element={<ConceptBoard project={project} onUpdate={setProject} />}
      />
      <Route
        path="brief"
        element={<BriefEditor project={project} onUpdate={setProject} />}
      />
      <Route path="history" element={<DecisionHistory project={project} />} />
      <Route path="*" element={<Navigate to="research" replace />} />
    </Routes>
  );
}

function ProjectLoader() {
  const { projectId } = useParams();
  const id = Number(projectId);
  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    if (!id) return;
    try {
      const data = await api.getProject(id);
      setProject(data);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败');
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!project || (project.status !== 'running' && project.status !== 'failed')) return;
    if (project.status === 'failed') return;
    const timer = window.setInterval(() => {
      void load();
    }, 1500);
    return () => window.clearInterval(timer);
  }, [project?.status, load]);

  if (error) {
    return (
      <div className="app-shell">
        <div className="panel empty">{error}</div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="app-shell">
        <div className="panel empty">加载项目中…</div>
      </div>
    );
  }

  return <ProjectRoutes project={project} setProject={setProject} />;
}

export default function App() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);

  const refresh = useCallback(async () => {
    const list = await api.listProjects();
    setProjects(list);
  }, []);

  useEffect(() => {
    void refresh().catch(() => undefined);
  }, [refresh]);

  return (
    <Routes>
      <Route path="/" element={<Dashboard projects={projects} onRefresh={refresh} />} />
      <Route path="/projects/:projectId/*" element={<ProjectLoader />} />
    </Routes>
  );
}
