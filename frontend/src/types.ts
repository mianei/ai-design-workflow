export interface ProjectSummary {
  id: number;
  title: string;
  raw_input: string;
  status: string;
  selected_concept_id: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface Requirement {
  product_category: string;
  target_users: string;
  business_goal: string;
  price_range: string;
  brand_attributes: string;
  design_constraints: string;
}

export interface Competitor {
  name: string;
  strength: string;
  weakness: string;
}

export interface Research {
  market_trends: string[];
  competitors: Competitor[];
  user_pain_points: string[];
  opportunities: string[];
}

export interface Persona {
  name: string;
  age: string;
  scenario: string;
  needs: string[];
  frustrations: string[];
  buying_reason: string;
}

export interface Concept {
  id: string;
  concept_key: string;
  concept_name: string;
  target_user: string;
  design_keywords: string[];
  product_features: string[];
  visual_direction: string;
  business_value: string;
  is_favorite: boolean;
  rating: number | null;
  merged_from?: string | null;
}

export interface Brief {
  design_goal: string;
  target_user: string;
  design_keywords: string[];
  CMF_direction: string;
  form_language: string;
  must_have_features: string;
  avoid_features: string;
}

export interface AgentStep {
  agent_name: string;
  status: string;
  message: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface DecisionEvent {
  id: number;
  event_type: string;
  actor: string;
  payload: Record<string, unknown>;
  created_at: string | null;
}

export interface ProjectDetail extends ProjectSummary {
  requirement: Requirement | null;
  research: Research | null;
  insight: Persona | null;
  concepts: Concept[];
  brief: Brief | null;
  agent_steps: AgentStep[];
  decisions: DecisionEvent[];
}
