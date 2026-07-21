import { AgentProgress } from '../components/AgentProgress';
import { TopBar } from '../components/TopBar';
import type { ProjectDetail } from '../types';

export function ResearchBoard({
  project,
  onRerun,
}: {
  project: ProjectDetail;
  onRerun: () => Promise<void>;
}) {
  const { requirement, research, insight, agent_steps } = project;

  return (
    <div className="app-shell">
      <TopBar projectId={project.id} title={project.title} />
      <div className="grid-2">
        <div>
          <section className="panel">
            <div className="section-title">
              <h2>AI Research Board</h2>
              <button className="btn" type="button" onClick={() => void onRerun()}>
                重新运行 Agents
              </button>
            </div>
            {!requirement && project.status === 'running' ? (
              <p className="muted">Agents 正在分析需求与市场…</p>
            ) : null}

            {requirement ? (
              <div style={{ marginBottom: 22 }}>
                <h3>结构化需求</h3>
                <div className="keyword-row" style={{ marginBottom: 10 }}>
                  <span className="tag">{requirement.product_category}</span>
                  <span className="tag neutral">{requirement.price_range}</span>
                  <span className="tag ai">{requirement.brand_attributes}</span>
                </div>
                <p>
                  <strong>用户：</strong>
                  {requirement.target_users}
                </p>
                <p>
                  <strong>商业目标：</strong>
                  {requirement.business_goal}
                </p>
                <p className="muted">
                  <strong>约束：</strong>
                  {requirement.design_constraints}
                </p>
              </div>
            ) : null}

            {research ? (
              <div style={{ marginBottom: 22 }}>
                <h3>市场趋势</h3>
                <ul className="list-clean">
                  {research.market_trends.map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
                <h3>竞品分析</h3>
                <div className="project-list">
                  {research.competitors.map((c) => (
                    <div key={c.name} className="project-item">
                      <div>
                        <strong>{c.name}</strong>
                        <div className="muted">优势：{c.strength}</div>
                        <div className="muted">劣势：{c.weakness}</div>
                      </div>
                    </div>
                  ))}
                </div>
                <h3 style={{ marginTop: 16 }}>用户痛点</h3>
                <ul className="list-clean">
                  {research.user_pain_points.map((p) => (
                    <li key={p}>{p}</li>
                  ))}
                </ul>
                <h3>市场机会</h3>
                <ul className="list-clean">
                  {research.opportunities.map((o) => (
                    <li key={o}>{o}</li>
                  ))}
                </ul>
              </div>
            ) : null}

            {insight ? (
              <div>
                <h3>User Persona</h3>
                <p>
                  <strong>
                    {insight.name} · {insight.age}岁
                  </strong>
                </p>
                <p className="muted">{insight.scenario}</p>
                <p>
                  <strong>Needs</strong>
                </p>
                <ul className="list-clean">
                  {insight.needs.map((n) => (
                    <li key={n}>{n}</li>
                  ))}
                </ul>
                <p>
                  <strong>Frustrations</strong>
                </p>
                <ul className="list-clean">
                  {insight.frustrations.map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
                <p>
                  <strong>购买动机：</strong>
                  {insight.buying_reason}
                </p>
              </div>
            ) : null}
          </section>
        </div>

        <aside className="panel">
          <div className="section-title">
            <h2>Agent 执行过程</h2>
            <span className="tag ai">{project.status}</span>
          </div>
          <AgentProgress steps={agent_steps} />
        </aside>
      </div>
    </div>
  );
}
