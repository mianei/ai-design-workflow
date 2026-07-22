import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { AgentProgress } from '../components/AgentProgress';
import { TopBar } from '../components/TopBar';
import type { Concept, ProjectDetail } from '../types';

export function ConceptBoard({
  project,
  onUpdate,
}: {
  project: ProjectDetail;
  onUpdate: (next: ProjectDetail) => void;
}) {
  const navigate = useNavigate();
  const [mergeA, setMergeA] = useState('');
  const [mergeB, setMergeB] = useState('');
  const [busy, setBusy] = useState(false);
  const [keywordDrafts, setKeywordDrafts] = useState<Record<string, string>>({});

  const concepts = project.concepts;
  const ready = concepts.length > 0;

  const options = useMemo(
    () => concepts.map((c) => ({ value: c.concept_key, label: c.concept_name })),
    [concepts],
  );

  async function patch(
    conceptKey: string,
    body: { is_favorite?: boolean; rating?: number; design_keywords?: string[] },
  ) {
    setBusy(true);
    try {
      const next = await api.updateConcept(project.id, conceptKey, body);
      onUpdate(next);
    } finally {
      setBusy(false);
    }
  }

  async function merge() {
    if (!mergeA || !mergeB || mergeA === mergeB) return;
    setBusy(true);
    try {
      const next = await api.mergeConcepts(project.id, mergeA, mergeB);
      onUpdate(next);
    } finally {
      setBusy(false);
    }
  }

  async function selectForBrief(conceptKey: string) {
    setBusy(true);
    try {
      const next = await api.generateBrief(project.id, conceptKey);
      onUpdate(next);
      navigate(`/projects/${project.id}/brief`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app-shell">
      <TopBar projectId={project.id} title={project.title} />
      <section className="panel" style={{ marginBottom: 18 }}>
        <div className="section-title">
          <div>
            <h2>Concept Board</h2>
            <p className="muted" style={{ margin: 0 }}>
              AI 只提供方向，不自动选定最终方案。请收藏、评分、改关键词，或合并两个方向。
            </p>
          </div>
          <span className="tag">Human Decision Layer</span>
        </div>

        {!ready ? (
          <div className="grid-2">
            <div className="empty">概念尚未生成，请等待 Agent 工作流完成。</div>
            <AgentProgress steps={project.agent_steps} />
          </div>
        ) : (
          <>
            <div className="grid-3">
              {concepts.map((c) => (
                <ConceptCard
                  key={c.concept_key}
                  concept={c}
                  selected={project.selected_concept_id === c.concept_key}
                  keywordText={
                    keywordDrafts[c.concept_key] ?? c.design_keywords.join(', ')
                  }
                  onKeywordChange={(v) =>
                    setKeywordDrafts((prev) => ({ ...prev, [c.concept_key]: v }))
                  }
                  disabled={busy}
                  onFavorite={() =>
                    void patch(c.concept_key, { is_favorite: !c.is_favorite })
                  }
                  onRate={(rating) => void patch(c.concept_key, { rating })}
                  onSaveKeywords={() => {
                    const raw = keywordDrafts[c.concept_key] ?? c.design_keywords.join(', ');
                    const keywords = raw
                      .split(/[,，]/)
                      .map((s) => s.trim())
                      .filter(Boolean);
                    void patch(c.concept_key, { design_keywords: keywords });
                  }}
                  onSelect={() => void selectForBrief(c.concept_key)}
                />
              ))}
            </div>

            <div style={{ marginTop: 20, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <select value={mergeA} onChange={(e) => setMergeA(e.target.value)}>
                <option value="">合并来源 A</option>
                {options.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
              <select value={mergeB} onChange={(e) => setMergeB(e.target.value)}>
                <option value="">合并来源 B</option>
                {options.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
              <button className="btn" type="button" disabled={busy} onClick={() => void merge()}>
                合并两个方向
              </button>
            </div>
          </>
        )}
      </section>
    </div>
  );
}

function ConceptCard({
  concept,
  selected,
  keywordText,
  onKeywordChange,
  disabled,
  onFavorite,
  onRate,
  onSaveKeywords,
  onSelect,
}: {
  concept: Concept;
  selected: boolean;
  keywordText: string;
  onKeywordChange: (v: string) => void;
  disabled: boolean;
  onFavorite: () => void;
  onRate: (n: number) => void;
  onSaveKeywords: () => void;
  onSelect: () => void;
}) {
  return (
    <article className={`concept-card ${selected ? 'selected' : ''}`}>
      <div className="section-title" style={{ marginBottom: 0 }}>
        <h3>{concept.concept_name}</h3>
        {concept.is_favorite ? <span className="tag">已收藏</span> : null}
      </div>
      {(concept.sketch_svg || concept.sketch_image_url) && (
        <div className="sketch-frame">
          <img
            src={
              concept.sketch_svg ||
              (concept.sketch_image_url?.startsWith('http')
                ? concept.sketch_image_url
                : `http://127.0.0.1:8000${concept.sketch_image_url}`)
            }
            alt={`${concept.concept_name} sketch`}
          />
        </div>
      )}
      <p className="muted" style={{ margin: 0 }}>
        {concept.target_user}
      </p>
      <div className="keyword-row">
        {concept.design_keywords.map((k) => (
          <span className="keyword" key={k}>
            {k}
          </span>
        ))}
      </div>
      {concept.cmf_colors?.length ? (
        <div className="cmf-row">
          {concept.cmf_colors.map((c) => (
            <span key={c} className="cmf-swatch" style={{ background: c }} title={c} />
          ))}
        </div>
      ) : null}
      <div>
        <strong>产品特征</strong>
        <ul className="list-clean">
          {concept.product_features.map((f) => (
            <li key={f}>{f}</li>
          ))}
        </ul>
      </div>
      <p>
        <strong>视觉方向：</strong>
        {concept.visual_direction}
      </p>
      {concept.sketch_caption ? (
        <p className="muted">
          <strong>草图说明：</strong>
          {concept.sketch_caption}
        </p>
      ) : null}
      <p className="muted">
        <strong>商业价值：</strong>
        {concept.business_value}
      </p>

      <div className="field" style={{ marginBottom: 0 }}>
        <label>修改关键词（逗号分隔）</label>
        <input value={keywordText} onChange={(e) => onKeywordChange(e.target.value)} />
      </div>

      <div className="actions">
        <button className="btn" type="button" disabled={disabled} onClick={onFavorite}>
          {concept.is_favorite ? '取消收藏' : '收藏'}
        </button>
        <button className="btn" type="button" disabled={disabled} onClick={() => onRate(4)}>
          评分 4★
        </button>
        <button className="btn" type="button" disabled={disabled} onClick={() => onRate(5)}>
          评分 5★
        </button>
        <button className="btn" type="button" disabled={disabled} onClick={onSaveKeywords}>
          保存关键词
        </button>
        <button className="btn accent" type="button" disabled={disabled} onClick={onSelect}>
          选此方向生成 Brief
        </button>
      </div>
      {concept.rating != null ? (
        <div className="mono muted">当前评分：{concept.rating}</div>
      ) : null}
      {concept.merged_from ? (
        <div className="mono muted">合并自：{concept.merged_from}</div>
      ) : null}
    </article>
  );
}
