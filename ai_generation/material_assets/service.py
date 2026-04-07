from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ai_generation.material_assets.models import AssetRecord, ProjectRecord
from ai_generation.material_assets.registry import MaterialRegistry
from ai_generation.material_assets.storage import LocalMaterialStorage


class MaterialAssetService:
    """上传原图、存储、记录项目 / 房间类型 / 风格标签。"""

    def __init__(self, data_root: str | Path) -> None:
        self.storage = LocalMaterialStorage(data_root)
        self.registry = MaterialRegistry(Path(data_root) / "_index")

    def create_project(self, name: str) -> ProjectRecord:
        p = ProjectRecord(name=name)
        self.registry.upsert_project(p)
        return p

    def ingest_original(
        self,
        project_id: str,
        file_bytes: bytes,
        filename: str,
        room_type: str | None = None,
        style_tags: list[str] | None = None,
    ) -> AssetRecord:
        asset = AssetRecord(project_id=project_id, original_relpath="", room_type=room_type, style_tags=style_tags or [])
        relpath = self.storage.write_original(project_id, asset.id, filename, file_bytes)
        asset.original_relpath = relpath
        self.registry.upsert_asset(asset)
        self.storage.write_meta(
            project_id,
            asset.id,
            {
                "asset_id": asset.id,
                "project_id": project_id,
                "room_type": room_type,
                "style_tags": style_tags or [],
            },
        )
        return asset

    def ingest_original_from_path(
        self,
        project_id: str,
        path: str | Path,
        room_type: str | None = None,
        style_tags: list[str] | None = None,
    ) -> AssetRecord:
        p = Path(path)
        return self.ingest_original(project_id, p.read_bytes(), p.name, room_type, style_tags)

    def attach_analysis(self, asset: AssetRecord, analysis: dict[str, Any]) -> AssetRecord:
        asset.analysis = analysis
        asset.updated_at = datetime.now(timezone.utc)
        self.registry.upsert_asset(asset)
        meta = self.storage.read_meta(asset.project_id, asset.id)
        meta["analysis"] = analysis
        self.storage.write_meta(asset.project_id, asset.id, meta)
        return asset

    def set_staged_relpath(self, asset: AssetRecord, staged_relpath: str) -> AssetRecord:
        asset.staged_relpath = staged_relpath
        asset.updated_at = datetime.now(timezone.utc)
        self.registry.upsert_asset(asset)
        meta = self.storage.read_meta(asset.project_id, asset.id)
        meta["staged_relpath"] = staged_relpath
        self.storage.write_meta(asset.project_id, asset.id, meta)
        return asset

    def set_mask_relpath(self, asset: AssetRecord, mask_relpath: str) -> AssetRecord:
        asset.mask_relpath = mask_relpath
        asset.updated_at = datetime.now(timezone.utc)
        self.registry.upsert_asset(asset)
        meta = self.storage.read_meta(asset.project_id, asset.id)
        meta["mask_relpath"] = mask_relpath
        self.storage.write_meta(asset.project_id, asset.id, meta)
        return asset

    def get_asset(self, asset_id: str) -> AssetRecord | None:
        return self.registry.get_asset(asset_id)

    def original_abs_path(self, asset: AssetRecord) -> Path:
        return self.storage.abs_path(asset.original_relpath)

    def staged_abs_path(self, asset: AssetRecord) -> Path | None:
        if not asset.staged_relpath:
            return None
        return self.storage.abs_path(asset.staged_relpath)

    def mask_abs_path(self, asset: AssetRecord) -> Path | None:
        if not asset.mask_relpath:
            return None
        return self.storage.abs_path(asset.mask_relpath)
