import type { Brief, ProjectDetail, ProjectSummary } from './types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options?.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; mock_mode: boolean; llm_provider: string }>('/api/health'),
  listProjects: () => request<ProjectSummary[]>('/api/projects'),
  getProject: (id: number) => request<ProjectDetail>(`/api/projects/${id}`),
  createProject: (title: string, raw_input: string) =>
    request<ProjectDetail>('/api/projects', {
      method: 'POST',
      body: JSON.stringify({ title, raw_input }),
    }),
  rerun: (id: number) =>
    request<{ ok: boolean }>(`/api/projects/${id}/rerun`, { method: 'POST' }),
  updateConcept: (
    id: number,
    conceptKey: string,
    body: { is_favorite?: boolean; rating?: number; design_keywords?: string[] },
  ) =>
    request<ProjectDetail>(`/api/projects/${id}/concepts/${conceptKey}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  mergeConcepts: (id: number, source_a: string, source_b: string, concept_name?: string) =>
    request<ProjectDetail>(`/api/projects/${id}/concepts/merge`, {
      method: 'POST',
      body: JSON.stringify({ source_a, source_b, concept_name }),
    }),
  generateBrief: (id: number, concept_key: string) =>
    request<ProjectDetail>(`/api/projects/${id}/brief/generate`, {
      method: 'POST',
      body: JSON.stringify({ concept_key }),
    }),
  updateBrief: (id: number, brief: Partial<Brief>) =>
    request<ProjectDetail>(`/api/projects/${id}/brief`, {
      method: 'PATCH',
      body: JSON.stringify(brief),
    }),
  finalize: (id: number, note?: string) =>
    request<ProjectDetail>(`/api/projects/${id}/finalize`, {
      method: 'POST',
      body: JSON.stringify({ note }),
    }),
};
