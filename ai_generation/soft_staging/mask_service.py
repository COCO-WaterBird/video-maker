from __future__ import annotations

from pathlib import Path

from ai_generation.material_assets.service import MaterialAssetService
from ai_generation.material_assets.models import AssetRecord


class MaskService:
    """
    可选 mask：全图编辑时不传 mask；局部软装可上传或后续接分割模型生成。
    """

    def __init__(self, materials: MaterialAssetService) -> None:
        self._materials = materials

    def attach_uploaded_mask(
        self,
        asset: AssetRecord,
        mask_bytes: bytes,
        ext: str = "png",
    ) -> AssetRecord:
        relpath = self._materials.storage.write_mask(asset.project_id, asset.id, mask_bytes, ext)
        return self._materials.set_mask_relpath(asset, relpath)

    def mask_path_or_none(self, asset: AssetRecord) -> Path | None:
        return self._materials.mask_abs_path(asset)
