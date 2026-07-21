import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../api';
import type { ProjectSummary } from '../types';
import { TopBar } from '../components/TopBar';

const SAMPLE = `产品：智能水杯
目标用户：25-35岁女性
价格：300-500元
品牌定位：年轻、科技、高品质`;

export function Dashboard({
  projects,
  onRefresh,
}: {
  projects: ProjectSummary[];
  onRefresh: () => Promise<void>;
}) {
  const navigate = useNavigate();
  const [title, setTitle] = useState('智能水杯概念探索');
  const [rawInput, setRawInput] = useState(SAMPLE);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const project = await api.createProject(title.trim(), rawInput.trim());
      await onRefresh();
      navigate(`/projects/${project.id}/research`);
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建失败');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <TopBar />
      <div className="grid-2">
        <section className="panel">
          <div className="section-title">
            <h2>新建项目</h2>
            <span className="tag">Human starts · AI explores</span>
          </div>
          <p className="muted">
            输入模糊产品需求。系统会依次运行 Requirement → Research → Insight → Concept
            Agents，生成可选方向。最终 brief 必须由人确认。
          </p>
          <form onSubmit={onSubmit}>
            <div className="field">
              <label htmlFor="title">项目名称</label>
              <input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="raw">产品需求</label>
              <textarea
                id="raw"
                value={rawInput}
                onChange={(e) => setRawInput(e.target.value)}
                required
              />
            </div>
            {error ? <p style={{ color: 'var(--danger)' }}>{error}</p> : null}
            <button className="btn accent" type="submit" disabled={loading}>
              {loading ? '启动 Agent 工作流…' : '启动 AI 工作流'}
            </button>
          </form>
        </section>

        <section className="panel">
          <div className="section-title">
            <h2>Project Dashboard</h2>
            <button className="btn" type="button" onClick={() => void onRefresh()}>
              刷新
            </button>
          </div>
          {projects.length === 0 ? (
            <div className="empty">还没有项目。左侧输入需求开始第一次探索。</div>
          ) : (
            <div className="project-list">
              {projects.map((p) => (
                <Link key={p.id} className="project-item" to={`/projects/${p.id}/research`}>
                  <div>
                    <strong>{p.title}</strong>
                    <div className="muted" style={{ fontSize: '0.86rem' }}>
                      {p.raw_input.slice(0, 72)}
                      {p.raw_input.length > 72 ? '…' : ''}
                    </div>
                  </div>
                  <span className="tag neutral">{p.status}</span>
                </Link>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
