import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { api } from '../api';
import { TopBar } from '../components/TopBar';
import type { Brief, ProjectDetail } from '../types';

export function BriefEditor({
  project,
  onUpdate,
}: {
  project: ProjectDetail;
  onUpdate: (next: ProjectDetail) => void;
}) {
  const [draft, setDraft] = useState<Brief | null>(project.brief);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState('');

  useEffect(() => {
    setDraft(project.brief);
  }, [project.brief]);

  async function save(e: FormEvent) {
    e.preventDefault();
    if (!draft) return;
    setBusy(true);
    try {
      const next = await api.updateBrief(project.id, draft);
      onUpdate(next);
    } finally {
      setBusy(false);
    }
  }

  async function finalize() {
    setBusy(true);
    try {
      const next = await api.finalize(project.id, note || 'Human confirmed final brief');
      onUpdate(next);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app-shell">
      <TopBar projectId={project.id} title={project.title} />
      <section className="panel">
        <div className="section-title">
          <div>
            <h2>Brief Editor</h2>
            <p className="muted" style={{ margin: 0 }}>
              AI 生成初稿，设计师可编辑。只有人工确认后才会进入 decided 状态。
            </p>
          </div>
          <span className="tag">{project.status}</span>
        </div>

        {!draft ? (
          <div className="empty">尚未选择概念。请先到 Concept Board 选择方向。</div>
        ) : (
          <form onSubmit={(e) => void save(e)}>
            <div className="field">
              <label>Design Goal</label>
              <textarea
                value={draft.design_goal}
                onChange={(e) => setDraft({ ...draft, design_goal: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Target User</label>
              <input
                value={draft.target_user}
                onChange={(e) => setDraft({ ...draft, target_user: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Design Keywords（逗号分隔）</label>
              <input
                value={draft.design_keywords.join(', ')}
                onChange={(e) =>
                  setDraft({
                    ...draft,
                    design_keywords: e.target.value
                      .split(/[,，]/)
                      .map((s) => s.trim())
                      .filter(Boolean),
                  })
                }
              />
            </div>
            <div className="field">
              <label>Form Language / Visual Language</label>
              <textarea
                value={draft.form_language}
                onChange={(e) => setDraft({ ...draft, form_language: e.target.value })}
              />
            </div>
            <div className="field">
              <label>CMF Direction</label>
              <textarea
                value={draft.CMF_direction}
                onChange={(e) => setDraft({ ...draft, CMF_direction: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Must-have Features</label>
              <textarea
                value={draft.must_have_features}
                onChange={(e) => setDraft({ ...draft, must_have_features: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Avoid Features</label>
              <textarea
                value={draft.avoid_features}
                onChange={(e) => setDraft({ ...draft, avoid_features: e.target.value })}
              />
            </div>

            <div className="actions">
              <button className="btn primary" type="submit" disabled={busy}>
                保存人工修改
              </button>
            </div>

            <div className="panel" style={{ marginTop: 18, boxShadow: 'none' }}>
              <h3>最终确认（Human only）</h3>
              <p className="muted">AI 不能自动决定最终方案。确认后项目状态变为 decided。</p>
              <div className="field">
                <label>确认备注</label>
                <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="可选" />
              </div>
              <button
                className="btn accent"
                type="button"
                disabled={busy || project.status === 'decided'}
                onClick={() => void finalize()}
              >
                {project.status === 'decided' ? '已确认最终 Brief' : '确认最终 Design Brief'}
              </button>
            </div>
          </form>
        )}
      </section>
    </div>
  );
}
