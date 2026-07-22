"""Sketch Agent — preliminary concept sketches + optional reference images."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

from backend.agents.base import BaseAgent
from backend.agents.sketch_renderer import render_concept_sketch_svg, svg_to_data_uri
from backend.config import ROOT_DIR

SKETCH_DIR = ROOT_DIR / "database" / "sketches"


class SketchAgent(BaseAgent):
    name = "sketch"
    display_message = "Concept sketches generated"

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        req = context.get("requirement") or {}
        concepts = list((context.get("concepts") or {}).get("concepts") or [])
        project_id = context.get("project_id") or 0

        if not concepts:
            return {"concepts": []}

        # Derive sketch specs from existing concept fields (no extra LLM round-trip).
        # Concept Agent already produced visual_direction / keywords via Kimi.
        planned = [_spec_from_concept(req, c, i) for i, c in enumerate(concepts)]

        # Generate SVG sketches first (always available), then best-effort reference images.
        enriched_base = []
        for concept, spec in zip(concepts, planned):
            svg = render_concept_sketch_svg(spec)
            enriched_base.append(
                {
                    **concept,
                    "form_type": spec.get("form_type"),
                    "cmf_colors": spec.get("colors") or [],
                    "sketch_caption": spec.get("sketch_caption"),
                    "sketch_prompt": spec.get("sketch_prompt"),
                    "sketch_svg": svg_to_data_uri(svg),
                    "sketch_image_url": None,
                }
            )

        image_urls = await asyncio.gather(
            *[
                _maybe_reference_image(
                    project_id=project_id,
                    concept_key=c.get("id") or f"concept_{i}",
                    prompt=c.get("sketch_prompt") or "",
                )
                for i, c in enumerate(enriched_base)
            ]
        )
        for item, url in zip(enriched_base, image_urls):
            item["sketch_image_url"] = url

        return {"concepts": enriched_base}


def _spec_from_concept(req: dict[str, Any], concept: dict[str, Any], index: int) -> dict[str, Any]:
    category = req.get("product_category", "产品")
    keywords = concept.get("design_keywords") or ["minimal"]
    text = f"{category} {concept.get('concept_name', '')} {concept.get('visual_direction', '')}".lower()
    form = "compact"
    if any(k in text for k in ("血压", "cuff", "袖带", "腕带", "armband")):
        form = "cuff"
    elif any(k in text for k in ("杯", "瓶", "bottle", "cup", "水壶", "保温杯")):
        form = "bottle"
    elif any(k in text for k in ("手环", "watch", "wearable", "耳机", "腕")):
        form = "wearable"
    elif any(k in text for k in ("音箱", "盒子", "仪", "monitor", "屏", "主机")):
        form = "panel"

    joined = " ".join(str(k).lower() for k in keywords)
    if "warm" in joined or "cute" in joined or "亲和" in text:
        colors = ["#f0e0d0", "#8c5a4a", "#e8b4a0", "#f7f1ea"]
    elif "tech" in joined or "precise" in joined or "科技" in text:
        colors = ["#dfe6ee", "#2c3640", "#7a8fa3", "#6ec6c0"]
    elif "premium" in joined or "minimal" in joined or "calm" in joined:
        colors = ["#e8e6e3", "#3d3a36", "#b0aaa3", "#c9a66b"]
    else:
        colors = [
            ["#d8e2e0", "#5a6b68", "#9aaea8", "#c5a882"],
            ["#f0e0d0", "#8c5a4a", "#e8b4a0", "#d4b896"],
            ["#dfe6ee", "#2c3640", "#7a8fa3", "#6ec6c0"],
        ][index % 3]

    caption = concept.get("visual_direction") or f"{concept.get('concept_name', '')} 初步方向"
    prompt = (
        f"industrial design concept sketch of {category}, {concept.get('concept_name', '')}, "
        f"{', '.join(keywords)}, {concept.get('visual_direction', '')}, "
        "clean marker line drawing, orthographic and three-quarter view, white background, "
        "preliminary product design exploration board, not photorealistic"
    )
    return {
        "concept_name": concept.get("concept_name"),
        "design_keywords": keywords,
        "product_category": category,
        "visual_direction": concept.get("visual_direction", ""),
        "form_type": form,
        "colors": colors,
        "sketch_caption": caption[:120],
        "sketch_prompt": prompt,
    }


async def _maybe_reference_image(project_id: int, concept_key: str, prompt: str) -> str | None:
    """Best-effort concept reference image via Pollinations (no extra API key)."""
    if not prompt:
        return None
    SKETCH_DIR.mkdir(parents=True, exist_ok=True)
    out_dir = SKETCH_DIR / str(project_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{concept_key}.jpg"
    if path.exists() and path.stat().st_size > 1000:
        return f"/media/sketches/{project_id}/{concept_key}.jpg"

    url = (
        "https://image.pollinations.ai/prompt/"
        + quote(prompt[:280])
        + "?width=768&height=768&nologo=true"
    )
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            resp = await client.get(url)
            ctype = resp.headers.get("content-type", "")
            if resp.status_code == 200 and ("image" in ctype or path.suffix == ".jpg"):
                if len(resp.content) > 1000:
                    path.write_bytes(resp.content)
                    return f"/media/sketches/{project_id}/{concept_key}.jpg"
    except Exception as exc:  # noqa: BLE001
        print(f"[sketch] reference image skipped for {concept_key}: {exc}")
    return None
