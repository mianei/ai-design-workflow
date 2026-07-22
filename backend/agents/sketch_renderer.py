"""Generate industrial-design style SVG concept sketches from structured specs."""
from __future__ import annotations

import hashlib
import re
from typing import Any


PALETTES = {
    "calm": ["#d8e2e0", "#5a6b68", "#9aaea8", "#c5a882"],
    "warm": ["#f0e0d0", "#8c5a4a", "#e8b4a0", "#f7f1ea"],
    "tech": ["#dfe6ee", "#2c3640", "#7a8fa3", "#6ec6c0"],
    "premium": ["#e8e6e3", "#3d3a36", "#b0aaa3", "#c9a66b"],
    "default": ["#ece8e0", "#4a4844", "#a8a49c", "#7d9b8c"],
}


def _hex(color: str, fallback: str = "#cfc9be") -> str:
    if not color:
        return fallback
    c = color.strip()
    if re.fullmatch(r"#?[0-9a-fA-F]{6}", c):
        return c if c.startswith("#") else f"#{c}"
    return fallback


def _pick_palette(keywords: list[str], colors: list[str] | None = None) -> list[str]:
    if colors and len(colors) >= 3:
        return [_hex(c) for c in colors[:4]]
    joined = " ".join(keywords).lower()
    for key in ("calm", "warm", "tech", "premium"):
        if key in joined:
            base = PALETTES[key]
            return [_hex(x) if x.startswith("#") else x for x in [base[0], base[2], base[1], base[3]]]
    # fix calm palette typo if any
    return PALETTES["default"]


def _form_family(category: str, keywords: list[str], form_type: str | None = None) -> str:
    if form_type in {"bottle", "cuff", "panel", "wearable", "compact"}:
        return form_type
    text = f"{category} {' '.join(keywords)}".lower()
    if any(k in text for k in ("血压", "cuff", "arm", "腕带", "袖带")):
        return "cuff"
    if any(k in text for k in ("杯", "瓶", "bottle", "cup", "水壶")):
        return "bottle"
    if any(k in text for k in ("手环", "watch", "wearable", "耳机")):
        return "wearable"
    if any(k in text for k in ("音箱", "盒子", "仪", "monitor", "屏")):
        return "panel"
    return "compact"


def render_concept_sketch_svg(spec: dict[str, Any]) -> str:
    """Return a standalone SVG string resembling a preliminary ID sketch board."""
    name = spec.get("concept_name") or "Concept"
    keywords = spec.get("design_keywords") or []
    category = spec.get("product_category") or ""
    form = _form_family(category, keywords, spec.get("form_type"))
    colors = _pick_palette(keywords, spec.get("colors"))
    fill, ink, mid, accent = colors[0], colors[1], colors[2] if len(colors) > 2 else colors[1], colors[-1]
    caption = spec.get("sketch_caption") or spec.get("visual_direction") or ""
    seed = int(hashlib.md5(name.encode("utf-8")).hexdigest()[:6], 16)

    body = {
        "bottle": _bottle_views,
        "cuff": _cuff_views,
        "panel": _panel_views,
        "wearable": _wearable_views,
        "compact": _compact_views,
    }[form](fill, ink, mid, accent, seed)

    kw = " · ".join(keywords[:4]) if keywords else form
    swatches = "".join(
        f'<rect x="{40 + i * 36}" y="500" width="28" height="28" rx="4" fill="{c}" stroke="#1a1c1a" stroke-width="1"/>'
        for i, c in enumerate(colors[:4])
    )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 560" role="img" aria-label="{_xml(name)} sketch">
  <defs>
    <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e6e1d8" stroke-width="1"/>
    </pattern>
  </defs>
  <rect width="640" height="560" fill="#f7f4ee"/>
  <rect x="16" y="16" width="608" height="528" fill="url(#grid)" stroke="#d7d2c8"/>
  <text x="36" y="48" font-family="Georgia, serif" font-size="20" fill="#1a1c1a">{_xml(name)}</text>
  <text x="36" y="72" font-family="IBM Plex Sans, sans-serif" font-size="12" fill="#5f6460">{_xml(kw)}</text>
  <text x="520" y="48" font-family="IBM Plex Mono, monospace" font-size="11" fill="#8a8680">PRELIM SKETCH</text>
  {body}
  <g>
    <text x="36" y="492" font-family="IBM Plex Sans, sans-serif" font-size="11" fill="#5f6460">CMF</text>
    {swatches}
  </g>
  <text x="36" y="548" font-family="IBM Plex Sans, sans-serif" font-size="11" fill="#5f6460">{_xml(caption[:90])}</text>
</svg>'''


def _xml(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _bottle_views(fill: str, ink: str, mid: str, accent: str, seed: int) -> str:
    lean = 4 + (seed % 5)
    return f'''
  <g stroke="{ink}" fill="none" stroke-width="2" stroke-linecap="round">
    <text x="120" y="110" font-family="IBM Plex Mono, monospace" font-size="11" fill="#8a8680" stroke="none">FRONT</text>
    <path d="M170 150 h60 v20 c0 8 -8 12 -12 12 h-36 c-4 0 -12 -4 -12 -12 z" fill="{mid}" opacity="0.35"/>
    <rect x="178" y="180" width="44" height="18" rx="3" fill="{accent}" opacity="0.5"/>
    <path d="M165 198 c-8 10 -10 24 -10 40 v150 c0 28 18 42 45 42 s45 -14 45 -42 v-150 c0 -16 -2 -30 -10 -40 z" fill="{fill}" opacity="0.85"/>
    <path d="M165 198 c-8 10 -10 24 -10 40 v150 c0 28 18 42 45 42 s45 -14 45 -42 v-150 c0 -16 -2 -30 -10 -40 z"/>
    <path d="M175 260 h70" stroke-dasharray="4 6" opacity="0.5"/>
    <circle cx="200" cy="320" r="10" fill="{accent}" opacity="0.7"/>
    <text x="380" y="110" font-family="IBM Plex Mono, monospace" font-size="11" fill="#8a8680" stroke="none">SIDE</text>
    <path d="M420 160 h36 v20 h-36 z" fill="{mid}" opacity="0.35"/>
    <path d="M415 180 h46 v210 c0 20 -10 30 -23 30 s-23 -10 -23 -30 z" fill="{fill}" opacity="0.85"/>
    <path d="M415 180 h46 v210 c0 20 -10 30 -23 30 s-23 -10 -23 -30 z"/>
    <path d="M438 180 v210" opacity="0.35"/>
    <path d="M400 420 q40 {8+lean} 80 0" opacity="0.35"/>
  </g>'''


def _cuff_views(fill: str, ink: str, mid: str, accent: str, seed: int) -> str:
    bulge = 8 + (seed % 6)
    return f'''
  <g stroke="{ink}" fill="none" stroke-width="2" stroke-linecap="round">
    <text x="90" y="110" font-family="IBM Plex Mono, monospace" font-size="11" fill="#8a8680" stroke="none">ARM CUFF + MODULE</text>
    <ellipse cx="220" cy="280" rx="110" ry="70" fill="{fill}" opacity="0.75"/>
    <ellipse cx="220" cy="280" rx="110" ry="70"/>
    <ellipse cx="220" cy="280" rx="70" ry="42" opacity="0.45"/>
    <rect x="160" y="230" width="120" height="70" rx="14" fill="{mid}" opacity="0.55"/>
    <rect x="160" y="230" width="120" height="70" rx="14"/>
    <rect x="175" y="245" width="58" height="28" rx="4" fill="{accent}" opacity="0.65"/>
    <circle cx="255" cy="260" r="6" fill="{accent}"/>
    <path d="M120 280 q-30 0 -40 {bulge}" opacity="0.5"/>
    <path d="M320 280 q30 0 40 {bulge}" opacity="0.5"/>
    <text x="400" y="110" font-family="IBM Plex Mono, monospace" font-size="11" fill="#8a8680" stroke="none">SIDE</text>
    <path d="M430 200 h90 v160 h-90 z" fill="{fill}" opacity="0.8"/>
    <path d="M430 200 h90 v160 h-90 z"/>
    <path d="M445 230 h60 v40 h-60 z" fill="{mid}" opacity="0.5"/>
    <path d="M430 280 h90" stroke-dasharray="4 5" opacity="0.45"/>
  </g>'''


def _panel_views(fill: str, ink: str, mid: str, accent: str, seed: int) -> str:
    roundness = 18 + (seed % 10)
    return f'''
  <g stroke="{ink}" fill="none" stroke-width="2" stroke-linecap="round">
    <text x="110" y="110" font-family="IBM Plex Mono, monospace" font-size="11" fill="#8a8680" stroke="none">FRONT</text>
    <rect x="100" y="140" width="200" height="280" rx="{roundness}" fill="{fill}" opacity="0.85"/>
    <rect x="100" y="140" width="200" height="280" rx="{roundness}"/>
    <rect x="122" y="170" width="156" height="100" rx="8" fill="{mid}" opacity="0.45"/>
    <rect x="122" y="170" width="156" height="100" rx="8"/>
    <circle cx="150" cy="320" r="12" fill="{accent}" opacity="0.7"/>
    <circle cx="190" cy="320" r="12"/>
    <circle cx="230" cy="320" r="12"/>
    <path d="M140 370 h120" opacity="0.4"/>
    <text x="390" y="110" font-family="IBM Plex Mono, monospace" font-size="11" fill="#8a8680" stroke="none">SIDE</text>
    <path d="M430 160 h50 v260 h-50 z" fill="{fill}" opacity="0.85"/>
    <path d="M430 160 h50 v260 h-50 z"/>
    <path d="M455 160 v260" opacity="0.35"/>
  </g>'''


def _wearable_views(fill: str, ink: str, mid: str, accent: str, seed: int) -> str:
    return f'''
  <g stroke="{ink}" fill="none" stroke-width="2">
    <text x="120" y="110" font-family="IBM Plex Mono, monospace" font-size="11" fill="#8a8680" stroke="none">TOP</text>
    <ellipse cx="200" cy="260" rx="95" ry="120" fill="{fill}" opacity="0.3"/>
    <rect x="155" y="210" width="90" height="100" rx="22" fill="{fill}" opacity="0.9"/>
    <rect x="155" y="210" width="90" height="100" rx="22"/>
    <rect x="168" y="225" width="64" height="48" rx="8" fill="{mid}" opacity="0.5"/>
    <circle cx="200" cy="295" r="6" fill="{accent}"/>
    <path d="M155 230 q-50 -10 -55 40 q5 50 55 40" />
    <path d="M245 230 q50 -10 55 40 q-5 50 -55 40" />
    <text x="390" y="110" font-family="IBM Plex Mono, monospace" font-size="11" fill="#8a8680" stroke="none">WORN</text>
    <path d="M430 180 q60 -40 120 0 v160 q-60 40 -120 0 z" fill="{fill}" opacity="0.25"/>
    <rect x="470" y="230" width="50" height="60" rx="12" fill="{mid}" opacity="0.6"/>
    <rect x="470" y="230" width="50" height="60" rx="12"/>
  </g>'''


def _compact_views(fill: str, ink: str, mid: str, accent: str, seed: int) -> str:
    return f'''
  <g stroke="{ink}" fill="none" stroke-width="2">
    <text x="120" y="110" font-family="IBM Plex Mono, monospace" font-size="11" fill="#8a8680" stroke="none">ISO SKETCH</text>
    <path d="M180 360 l80 -40 l80 40 l-80 40 z" fill="{fill}" opacity="0.5"/>
    <path d="M180 360 l80 -40 l80 40 l-80 40 z"/>
    <path d="M180 360 l0 -120 l80 -40 l0 120 z" fill="{mid}" opacity="0.35"/>
    <path d="M180 360 l0 -120 l80 -40 l0 120 z"/>
    <path d="M260 200 l80 40 l0 120 l-80 -40 z" fill="{fill}" opacity="0.7"/>
    <path d="M260 200 l80 40 l0 120 l-80 -40 z"/>
    <circle cx="300" cy="280" r="14" fill="{accent}" opacity="0.65"/>
    <path d="M400 180 q80 40 80 140" stroke-dasharray="5 6" opacity="0.45"/>
    <text x="400" y="340" font-family="IBM Plex Mono, monospace" font-size="11" fill="#8a8680" stroke="none">gesture / hold</text>
  </g>'''


def svg_to_data_uri(svg: str) -> str:
    from urllib.parse import quote

    return "data:image/svg+xml;charset=utf-8," + quote(svg)
