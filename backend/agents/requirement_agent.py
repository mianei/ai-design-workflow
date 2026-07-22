"""Requirement Understanding Agent — structures fuzzy product briefs."""
from __future__ import annotations

from typing import Any

from backend.agents.base import BaseAgent
from backend.agents.llm import call_llm_json
from backend.agents.validate import require_object
from backend.config import use_mock_llm


class RequirementAgent(BaseAgent):
    name = "requirement"
    display_message = "Requirement analysis completed"

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        raw = context["raw_input"]
        mock = _mock_requirement(raw)
        system = (
            "You are a senior product strategist for consumer goods companies. "
            "Parse fuzzy product requirements into structured JSON with keys: "
            "product_category, target_users, business_goal, price_range, "
            "brand_attributes, design_constraints. "
            "All values must be concise Chinese or bilingual strings."
        )
        user = f"Raw product requirement:\n{raw}\n\nReturn JSON only."
        result = await call_llm_json(system, user, mock)
        data = require_object(
            result,
            mock,
            use_mock=use_mock_llm(),
            required=[
                "product_category",
                "target_users",
                "business_goal",
                "price_range",
                "brand_attributes",
                "design_constraints",
            ],
        )
        return {
            "product_category": data["product_category"],
            "target_users": data["target_users"],
            "business_goal": data["business_goal"],
            "price_range": data["price_range"],
            "brand_attributes": data["brand_attributes"],
            "design_constraints": data["design_constraints"],
        }


def _mock_requirement(raw: str) -> dict[str, Any]:
    text = raw.lower()
    category = "智能水杯" if ("水杯" in raw or "bottle" in text or "cup" in text) else "消费品硬件"
    return {
        "product_category": category,
        "target_users": "25-35岁都市女性，关注健康与生活品质",
        "business_goal": "打造差异化智能日用单品，提升品牌年轻科技形象与客单价",
        "price_range": "300-500元",
        "brand_attributes": "年轻、科技、高品质",
        "design_constraints": "便携、易清洁、续航可靠、避免运动水壶廉价感",
    }
