"""跳过 GPT 看图时的占位分析结果，仅用于拼接编辑 prompt。"""

from __future__ import annotations

from ai_generation.image_analysis.schemas import ImageAnalysisResult


def analysis_without_vision(
    user_hint: str | None = None,
    ingest_room_type: str | None = None,
) -> ImageAnalysisResult:
    """
    不调用视觉模型，用规则生成最小 ImageAnalysisResult。
    room_type 沿用入库时的 ingest_room_type，以便厨房仍走 KITCHEN_SOFT_STAGING_PROMPT_EN。
    """
    edit_lines = [
        "在严格保留建筑结构、墙体、地面、门窗与固定装修的前提下，仅增强软装与陈设；"
        "整体为写实室内摄影风格，避免卡通与过度涂抹。",
    ]
    if user_hint and user_hint.strip():
        edit_lines.append(f"用户偏好：{user_hint.strip()}")

    rt = (ingest_room_type or "").strip()
    normalized_room = rt.replace(" ", "_") if rt else ""

    return ImageAnalysisResult(
        soft_furnishing_suggestions=["（已跳过看图分析，无自动建议）"],
        edit_prompt="\n".join(edit_lines),
        negative_prompt=(
            "避免画面模糊、涂抹感、花瓣或细节糊成一团、塑料假质感、油画/水彩感；"
            "避免改动墙色、窗洞、柜体与台面等硬装。"
        ),
        style="default",
        room_type=normalized_room,
    )
