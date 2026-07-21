import { TopBar } from '../components/TopBar';
import type { ProjectDetail } from '../types';

const LABELS: Record<string, string> = {
  project_created: '创建项目',
  ai_generated: 'AI 生成',
  favorite: '收藏方案',
  rate: '评分',
  user_edit: '人工修改',
  merge: '合并方向',
  select_brief: '选择概念并生成 Brief',
  finalize: '最终确认',
};

export function DecisionHistory({ project }: { project: ProjectDetail }) {
  return (
    <div className="app-shell">
      <TopBar projectId={project.id} title={project.title} />
      <section className="panel">
        <div className="section-title">
          <h2>Decision History</h2>
          <span className="tag neutral">{project.decisions.length} events</span>
        </div>
        <p className="muted">记录 AI 产出与人工决策，保证流程可追溯。</p>
        {project.decisions.length === 0 ? (
          <div className="empty">暂无决策记录。</div>
        ) : (
          <div>
            {[...project.decisions].reverse().map((d) => (
              <div key={d.id} className="history-item">
                <div>
                  <span className={`tag ${d.actor === 'ai' ? 'ai' : ''}`}>
                    {d.actor === 'ai' ? 'AI' : 'Human'}
                  </span>
                </div>
                <div>
                  <strong>{LABELS[d.event_type] || d.event_type}</strong>
                  <div className="mono muted">{d.created_at}</div>
                  <pre
                    className="mono"
                    style={{
                      margin: '8px 0 0',
                      whiteSpace: 'pre-wrap',
                      background: '#f7f4ee',
                      padding: 10,
                      borderRadius: 8,
                    }}
                  >
                    {JSON.stringify(d.payload, null, 2)}
                  </pre>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
