from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CandidateImage:
    image_bytes: bytes
    label: str = ""


def pick_best_image(candidates: list[CandidateImage]) -> CandidateImage:
    """
    多候选时选择策略占位：当前取第一张。
    后续可接人工打分、美学模型或再调 vision 做对比。
    """
    if not candidates:
        raise ValueError("candidates is empty")
    return candidates[0]
