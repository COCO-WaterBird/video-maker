from __future__ import annotations

from ai_generation.image_analysis.schemas import ImageAnalysisResult
from ai_generation.soft_staging.style_templates import (
    KITCHEN_SOFT_STAGING_PROMPT_EN,
    constraint_for_style,
    is_kitchen_room,
    structural_preservation_clause,
)


def build_edit_prompt_for_staging(
    analysis: ImageAnalysisResult,
    extra_user_text: str | None = None,
    ingest_room_type: str | None = None,
) -> str:
    """将视觉分析结果与风格模板合并为最终编辑 prompt。"""
    use_kitchen = is_kitchen_room(analysis.room_type) or is_kitchen_room(ingest_room_type)
    parts: list[str] = []
    if use_kitchen:
        parts.append(KITCHEN_SOFT_STAGING_PROMPT_EN)
    else:
        parts.append(structural_preservation_clause())
        parts.append(constraint_for_style(analysis.style or "default"))
    parts.append(analysis.edit_prompt.strip())
    if analysis.negative_prompt.strip():
        parts.append(f"避免：{analysis.negative_prompt.strip()}")
    if extra_user_text:
        parts.append(extra_user_text.strip())
    return "\n".join(p for p in parts if p)
