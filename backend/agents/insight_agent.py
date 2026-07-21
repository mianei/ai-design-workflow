"""User Insight Agent — builds persona from research context."""
from __future__ import annotations

from typing import Any

from backend.agents.base import BaseAgent
from backend.agents.llm import call_llm_json


class InsightAgent(BaseAgent):
    name = "insight"
    display_message = "User insight generated"

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        req = context["requirement"]
        research = context["research"]
        mock = _mock_persona(req)
        system = (
            "You are a UX researcher. From requirement and market research, create "
            "ONE primary user persona as JSON: name, age, scenario, needs[], "
            "frustrations[], buying_reason. Use Chinese."
        )
        user = f"Requirement:\n{req}\n\nResearch:\n{research}\n\nReturn persona JSON only."
        result = await call_llm_json(system, user, mock)
        return {
            "name": result.get("name", mock["name"]),
            "age": result.get("age", mock["age"]),
            "scenario": result.get("scenario", mock["scenario"]),
            "needs": result.get("needs", mock["needs"]),
            "frustrations": result.get("frustrations", mock["frustrations"]),
            "buying_reason": result.get("buying_reason", mock["buying_reason"]),
        }


def _mock_persona(req: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": "林可 (Ke)",
        "age": "29",
        "scenario": "互联网公司产品经理，工作日 8-10 小时坐办公室，通勤地铁 40 分钟，周末轻度健身",
        "needs": [
            "在会议密集时仍保持稳定饮水习惯",
            "桌面物件要有高级感，能匹配个人审美",
            "清洗简单，不增加生活负担",
            "智能功能要「有用但不吵」",
        ],
        "frustrations": [
            "现有智能杯提醒像闹铃一样打断专注",
            "塑料感强的产品放在 MacBook 旁很违和",
            "功能说明书太长，不想学习复杂 App",
        ],
        "buying_reason": (
            f"愿意为「看起来专业 + 用起来省心」的 {req.get('product_category', '产品')} "
            f"支付 {req.get('price_range', '中高端')} 价格，作为自我投资与桌面仪式感。"
        ),
    }
