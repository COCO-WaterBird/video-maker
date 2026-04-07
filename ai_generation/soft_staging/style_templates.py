"""风格模板：与分析结果中的 style 标签拼接，统一语气与约束。"""

from __future__ import annotations

# 厨房专用：英文主 prompt（含硬装锁定 + 软装范围 + 光影与风格）
KITCHEN_SOFT_STAGING_PROMPT_EN = """Edit the provided kitchen photo into a photorealistic soft-staged interior. Keep the original architecture and all permanent elements exactly unchanged, including the cabinet layout, cabinet finish, island shape and position, countertops, backsplash, appliances, windows, doors, walls, ceiling, flooring, camera angle, and perspective. Do not remodel, repaint, replace, resize, move, or redesign any fixed element. Only adjust soft styling and small decor elements such as flowers, greenery, trays, bowls, cutting boards, countertop accessories, bar stools, and a subtle rug. Keep the styling minimal, elegant, realistic, and uncluttered. Brighten the overall image while preserving realism. Increase natural daylight, lift shadows, improve white balance, and create a clean, airy, high-end North American kitchen feel. Make the space feel brighter, warmer, and more inviting, without changing the architecture or making the result look overexposed or artificial.

Image quality (critical): output must be tack-sharp photorealistic photography, crisp edges, natural micro-contrast, and preserved fine textures (wood grain, stone, cabinet finish, metal). Flowers and plants must look like a real DSLR photo: clear petal and leaf edges, believable color and translucency, no mushy blobs, no painterly smear, no waxy plastic look, no watercolor or oil-painting artifacts. Avoid heavy blur, over-softening, excessive denoise, or “AI mush” on small decor. If in doubt, render florals smaller and simpler rather than painterly."""


def is_kitchen_room(room_type: str | None) -> bool:
    if not room_type:
        return False
    t = room_type.strip().lower()
    if "kitchen" in t.replace(" ", "_"):
        return True
    return "厨房" in room_type


STYLE_CONSTRAINTS: dict[str, str] = {
    "nordic": "北欧风：浅木、留白、柔和织物，低饱和配色。",
    "modern_luxury": "现代轻奢：金属点缀、大理石纹理感、丝绒或皮革，克制华丽。",
    "japanese": "日式：原木、棉麻、低矮家具，自然宁静。",
    "minimal": "极简：线条干净、少装饰、中性色。",
    "default": "真实室内摄影光影，避免卡通与过度 HDR；画面清晰锐利、细节可辨，避免涂抹与糊成一团。",
}


def constraint_for_style(style_key: str) -> str:
    k = (style_key or "").strip().lower().replace(" ", "_")
    return STYLE_CONSTRAINTS.get(k, STYLE_CONSTRAINTS["default"])


def structural_preservation_clause() -> str:
    return (
        "严格保留原始照片的建筑结构、墙体、地面、门窗位置与透视；"
        "不得改变房间布局与硬装；仅调整软装与陈设。"
    )
