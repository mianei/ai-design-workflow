import type { AgentStep } from '../types';

const ORDER = ['requirement', 'research', 'insight', 'concept', 'brief'] as const;

const LABELS: Record<string, string> = {
  requirement: 'Requirement analysis',
  research: 'Market research',
  insight: 'User insight',
  concept: 'Concept generation',
  brief: 'Design brief',
};

export function AgentProgress({ steps }: { steps: AgentStep[] }) {
  const byName = Object.fromEntries(steps.map((s) => [s.agent_name, s]));

  return (
    <div className="agent-rail">
      {ORDER.map((name) => {
        const step = byName[name];
        const status = step?.status || 'pending';
        const mark =
          status === 'completed' ? '✓' : status === 'running' ? '…' : status === 'failed' ? '!' : '○';
        return (
          <div key={name} className={`agent-step ${status}`}>
            <div className="mark">{mark}</div>
            <div>
              <strong>
                {status === 'completed' ? '✓ ' : ''}
                {LABELS[name]}
                {status === 'completed' ? ' completed' : status === 'running' ? '…' : ''}
              </strong>
              <div className="muted" style={{ fontSize: '0.86rem' }}>
                {step?.message ||
                  (status === 'pending' ? 'Waiting for previous agents' : status)}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
