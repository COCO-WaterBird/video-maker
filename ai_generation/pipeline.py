from __future__ import annotations

from pathlib import Path

from ai_generation.image_analysis.analyzer import OpenAIVisionAnalyzer
from ai_generation.image_analysis.fallback import analysis_without_vision
from ai_generation.material_assets.service import MaterialAssetService
from ai_generation.soft_staging.image_edit_service import OpenAIImageEditService
from ai_generation.soft_staging.mask_service import MaskService
from ai_generation.soft_staging.prompt_builder import build_edit_prompt_for_staging


class StagingPipeline:
    """
    第一阶段：原图 → 视觉理解 → 软装编辑 → 软装成图（与视频解耦）。
    """

    def __init__(self, data_root: str | Path = "data") -> None:
        root = Path(data_root)
        self.materials = MaterialAssetService(root)
        self.analyzer = OpenAIVisionAnalyzer()
        self.editor = OpenAIImageEditService()
        self.masks = MaskService(self.materials)

    def generate_staged_image(
        self,
        asset_id: str,
        user_hint: str | None = None,
        extra_prompt: str | None = None,
        mask_bytes: bytes | None = None,
        output_format: str = "png",
        skip_vision: bool = False,
    ) -> Path:
        asset = self.materials.get_asset(asset_id)
        if asset is None:
            raise ValueError(f"unknown asset: {asset_id}")

        if mask_bytes is not None:
            asset = self.masks.attach_uploaded_mask(asset, mask_bytes)

        original = self.materials.original_abs_path(asset)
        if skip_vision:
            analysis = analysis_without_vision(
                user_hint=user_hint,
                ingest_room_type=asset.room_type,
            )
            payload = analysis.model_dump(mode="json")
            payload["_skip_vision"] = True
            asset = self.materials.attach_analysis(asset, payload)
        else:
            analysis = self.analyzer.analyze(original, user_hint=user_hint)
            asset = self.materials.attach_analysis(asset, analysis.model_dump(mode="json"))

        prompt = build_edit_prompt_for_staging(
            analysis,
            extra_user_text=extra_prompt,
            ingest_room_type=asset.room_type,
        )
        mask_path = self.masks.mask_path_or_none(asset)
        image_bytes = self.editor.edit(original, prompt, mask_path)

        ext = output_format.lstrip(".")
        staged_relpath = self.materials.storage.write_staged(
            asset.project_id, asset.id, image_bytes, ext
        )
        asset = self.materials.set_staged_relpath(asset, staged_relpath)
        out = self.materials.staged_abs_path(asset)
        assert out is not None
        return out


class VideoFromStagedPipeline:
    """
    第二阶段：仅以软装后的图为输入，调用即梦（占位）等视频能力。
    """

    def __init__(self, materials: MaterialAssetService) -> None:
        self.materials = materials
        from ai_generation.video_generation.jimeng_service import JimengVideoService

        self._video = JimengVideoService()

    def generate_video_from_staged(self, asset_id: str) -> str:
        asset = self.materials.get_asset(asset_id)
        if asset is None:
            raise ValueError(f"unknown asset: {asset_id}")
        staged = self.materials.staged_abs_path(asset)
        if staged is None:
            raise ValueError("缺少软装成图，请先完成第一阶段 generate_staged_image")
        return self._video.generate_from_image(staged)
