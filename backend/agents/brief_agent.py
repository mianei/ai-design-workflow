"""Design Brief Generator — turns a selected concept into a designer brief."""
from __future__ import annotations

from typing import Any

from backend.agents.base import BaseAgent
from backend.agents.llm import call_llm_json
from backend.agents.validate import require_list, require_object
from backend.config import use_mock_llm


class BriefAgent(BaseAgent):
    name = "brief"
    display_message = "Design brief generated"

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        req = context["requirement"]
        concept = context["selected_concept"]
        persona = context.get("insight", {})
        mock = _mock_brief(req, concept, persona)
        system = (
            "You are a design director writing a brief for industrial designers. "
            "From requirement + selected concept, output JSON: design_goal, target_user, "
            "design_keywords[], CMF_direction, form_language, must_have_features, "
            "avoid_features. Be concrete. Chinese preferred for prose fields."
        )
        user = f"Requirement:\n{req}\n\nSelected concept:\n{concept}\n\nPersona:\n{persona}\n\nReturn brief JSON."
        result = await call_llm_json(system, user, mock)
        data = require_object(
            result,
            mock,
            use_mock=use_mock_llm(),
            required=[
                "design_goal",
                "target_user",
                "design_keywords",
                "CMF_direction",
                "form_language",
                "must_have_features",
                "avoid_features",
            ],
        )
        return {
            "design_goal": data["design_goal"],
            "target_user": data["target_user"],
            "design_keywords": require_list(data["design_keywords"], field="design_keywords", min_items=1),
            "CMF_direction": data["CMF_direction"],
            "form_language": data["form_language"],
            "must_have_features": data["must_have_features"],
            "avoid_features": data["avoid_features"],
        }


def _mock_brief(req: dict[str, Any], concept: dict[str, Any], persona: dict[str, Any]) -> dict[str, Any]:
    keywords = concept.get("design_keywords") or ["minimal", "premium"]
    name = concept.get("concept_name", "Selected Concept")
    return {
        "design_goal": (
            f"基于「{name}」方向，创造适合城市办公场景的"
            f"{req.get('product_category', '产品')}，体现"
            f"{req.get('brand_attributes', '年轻科技高品质')} 品牌气质。"
        ),
        "target_user": concept.get("target_user") or persona.get("name", req.get("target_users", "")),
        "design_keywords": keywords,
        "CMF_direction": "aluminum / matte glass / soft-touch coating；低饱和冷色与一种点缀色",
        "form_language": " + ".join(keywords) + "；克制体量、清晰分区、安静的桌面存在感",
        "must_have_features": "；".join(concept.get("product_features") or ["核心功能清晰", "易清洁", "便携"]),
        "avoid_features": "sport style；cheap plastic feeling；过度拟人霓虹灯效；复杂多级菜单",
    }
