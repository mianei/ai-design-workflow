"""Market Research Agent — trends, competitors, pain points, opportunities."""
from __future__ import annotations

from typing import Any

from backend.agents.base import BaseAgent
from backend.agents.llm import call_llm_json


class ResearchAgent(BaseAgent):
    name = "research"
    display_message = "Market research completed"

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        req = context["requirement"]
        mock = _mock_research(req)
        system = (
            "You are a consumer market research analyst. Based on the structured "
            "product requirement, produce JSON with: market_trends (string[]), "
            "competitors ([{name, strength, weakness}]), user_pain_points (string[]), "
            "opportunities (string[]). Write in Chinese. Be specific and actionable."
        )
        user = f"Requirement JSON:\n{req}\n\nReturn JSON only."
        result = await call_llm_json(system, user, mock)
        return {
            "market_trends": result.get("market_trends", mock["market_trends"]),
            "competitors": result.get("competitors", mock["competitors"]),
            "user_pain_points": result.get("user_pain_points", mock["user_pain_points"]),
            "opportunities": result.get("opportunities", mock["opportunities"]),
        }


def _mock_research(req: dict[str, Any]) -> dict[str, Any]:
    category = req.get("product_category", "智能日用品")
    return {
        "market_trends": [
            f"{category}品类向「健康管理 + 情绪价值」双驱动演进",
            "中高端消费者愿意为材质质感与沉默式智能体验付费",
            "办公室场景成为日用智能硬件的高增长切入点",
            "CMF 与可持续材料成为品牌差异化关键杠杆",
        ],
        "competitors": [
            {
                "name": "GlowCup Pro",
                "strength": "App 生态成熟，饮水提醒精准",
                "weakness": "外观偏运动风，质感不足，难以进入办公桌场景",
            },
            {
                "name": "AquaMind",
                "strength": "温度保持出色，金属质感强",
                "weakness": "智能功能堆叠冗余，交互学习成本高",
            },
            {
                "name": "PetitBottle",
                "strength": "颜值高、社交传播力强",
                "weakness": "功能单薄，续航与清洗体验一般",
            },
        ],
        "user_pain_points": [
            "办公室久坐忘喝水，现有提醒过于打扰",
            "智能水杯清洗困难，密封圈易发霉",
            "外观要么太运动要么太可爱，缺少专业精致感",
            "价格 300-500 区间产品同质化严重，难建立信任",
        ],
        "opportunities": [
            "打造「静默智能」：少打扰、强质感的办公伴侣定位",
            "用 CMF 与形态语言建立中高端品牌识别",
            "把饮水数据转化为轻量健康洞察，而非复杂健身系统",
            "面向 25-35 女性的场景化叙事：通勤 / 会议 / 居家办公",
        ],
    }
