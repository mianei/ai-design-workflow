"""Concept Generation Agent — produces selectable design directions (not final design)."""
from __future__ import annotations

from typing import Any

from backend.agents.base import BaseAgent
from backend.agents.llm import call_llm_json


class ConceptAgent(BaseAgent):
    name = "concept"
    display_message = "3 concepts generated"

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        req = context["requirement"]
        research = context["research"]
        persona = context["insight"]
        mock = _mock_concepts(req, persona)
        system = (
            "You are a senior industrial design strategist. Generate exactly 3 distinct "
            "product CONCEPT DIRECTIONS (not final designs) for designers to choose from. "
            "Return JSON: {concepts:[{id, concept_name, target_user, design_keywords[], "
            "product_features[], visual_direction, business_value}]}. "
            "ids must be concept_a, concept_b, concept_c. Use Chinese for descriptive fields; "
            "concept_name and keywords may be bilingual."
        )
        user = (
            f"Requirement:\n{req}\n\nResearch:\n{research}\n\nPersona:\n{persona}\n\n"
            "Return JSON with 3 concepts."
        )
        result = await call_llm_json(system, user, mock)
        concepts = result.get("concepts", mock["concepts"])
        # Normalize ids
        normalized = []
        default_ids = ["concept_a", "concept_b", "concept_c"]
        for i, c in enumerate(concepts[:3]):
            cid = c.get("id") or default_ids[i]
            normalized.append(
                {
                    "id": cid,
                    "concept_name": c.get("concept_name", f"Concept {chr(65 + i)}"),
                    "target_user": c.get("target_user", persona.get("name", "")),
                    "design_keywords": c.get("design_keywords", []),
                    "product_features": c.get("product_features", []),
                    "visual_direction": c.get("visual_direction", ""),
                    "business_value": c.get("business_value", ""),
                }
            )
        while len(normalized) < 3:
            normalized.append(mock["concepts"][len(normalized)])
        return {"concepts": normalized}


def _mock_concepts(req: dict[str, Any], persona: dict[str, Any]) -> dict[str, Any]:
    user = persona.get("name", "目标用户")
    category = req.get("product_category", "产品")
    return {
        "concepts": [
            {
                "id": "concept_a",
                "concept_name": "Urban Wellness Companion",
                "target_user": f"{user} / 都市办公女性",
                "design_keywords": ["minimal", "premium", "calm"],
                "product_features": [
                    "静默饮水进度光环（可关闭）",
                    "一键拆洗密封结构",
                    "桌面无线充电底座可选",
                ],
                "visual_direction": "克制圆柱体量 + 柔和边缘；哑光金属与磨砂玻璃；低饱和冷灰与雾蓝",
                "business_value": f"占据「办公桌高级日用品」心智，支撑 {req.get('price_range', '中高端')} 定价",
            },
            {
                "id": "concept_b",
                "concept_name": "Emotional Smart Bottle",
                "target_user": f"{user} / 需要情绪陪伴的年轻消费者",
                "design_keywords": ["cute", "personalized", "warm"],
                "product_features": [
                    "可更换外壳 / 表情模块",
                    "饮水达成微小庆祝反馈",
                    "社交分享饮水成就卡片",
                ],
                "visual_direction": "圆润亲和轮廓；柔和粉色与奶油白；触感涂层与细节点缀",
                "business_value": "提升社交传播与复购配件收入，强化品牌亲和力",
            },
            {
                "id": "concept_c",
                "concept_name": "Precision Hydration Tool",
                "target_user": f"{user} / 效率导向的专业人群",
                "design_keywords": ["precise", "tech", "modular"],
                "product_features": [
                    "精准温控与饮水目标算法",
                    "模块化滤芯 / 茶仓",
                    "与日历会议日程联动的轻提醒",
                ],
                "visual_direction": f"工具感几何分割；阳极氧化铝；深石墨与青柠点缀，强调{category}专业属性",
                "business_value": "用专业能力叙事建立信任，便于后续拓展健康配件生态",
            },
        ]
    }
