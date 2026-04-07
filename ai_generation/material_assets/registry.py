from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_generation.material_assets.models import AssetRecord, ProjectRecord


class MaterialRegistry:
    """轻量索引：项目与资产列表，便于查询而不扫盘。"""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._path = self.root / "registry.json"

    def _load(self) -> dict[str, Any]:
        if not self._path.is_file():
            return {"projects": {}, "assets": {}}
        return json.loads(self._path.read_text(encoding="utf-8"))

    def _save(self, data: dict[str, Any]) -> None:
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def upsert_project(self, project: ProjectRecord) -> None:
        data = self._load()
        data["projects"][project.id] = project.model_dump(mode="json")
        self._save(data)

    def upsert_asset(self, asset: AssetRecord) -> None:
        data = self._load()
        data["assets"][asset.id] = asset.model_dump(mode="json")
        self._save(data)

    def get_project(self, project_id: str) -> ProjectRecord | None:
        raw = self._load()["projects"].get(project_id)
        return ProjectRecord.model_validate(raw) if raw else None

    def get_asset(self, asset_id: str) -> AssetRecord | None:
        raw = self._load()["assets"].get(asset_id)
        return AssetRecord.model_validate(raw) if raw else None
