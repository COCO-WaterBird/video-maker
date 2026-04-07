from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


class LocalMaterialStorage:
    """原图 / 软装结果 / mask 落盘，目录即素材边界。"""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def project_dir(self, project_id: str) -> Path:
        return self.root / "projects" / project_id

    def asset_dir(self, project_id: str, asset_id: str) -> Path:
        return self.project_dir(project_id) / "assets" / asset_id

    def ensure_asset_dir(self, project_id: str, asset_id: str) -> Path:
        d = self.asset_dir(project_id, asset_id)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def write_original(
        self, project_id: str, asset_id: str, filename: str, data: bytes
    ) -> str:
        d = self.ensure_asset_dir(project_id, asset_id)
        path = d / f"original_{filename}"
        path.write_bytes(data)
        return str(path.relative_to(self.root))

    def write_staged(self, project_id: str, asset_id: str, data: bytes, ext: str) -> str:
        d = self.ensure_asset_dir(project_id, asset_id)
        path = d / f"staged.{ext.lstrip('.')}"
        path.write_bytes(data)
        return str(path.relative_to(self.root))

    def write_mask(self, project_id: str, asset_id: str, data: bytes, ext: str) -> str:
        d = self.ensure_asset_dir(project_id, asset_id)
        path = d / f"mask.{ext.lstrip('.')}"
        path.write_bytes(data)
        return str(path.relative_to(self.root))

    def write_meta(self, project_id: str, asset_id: str, meta: dict[str, Any]) -> None:
        d = self.ensure_asset_dir(project_id, asset_id)
        (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    def read_meta(self, project_id: str, asset_id: str) -> dict[str, Any]:
        p = self.asset_dir(project_id, asset_id) / "meta.json"
        if not p.is_file():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))

    def abs_path(self, relpath: str) -> Path:
        return (self.root / relpath).resolve()

    def copy_file_into_asset(
        self, project_id: str, asset_id: str, src: Path, dest_name: str
    ) -> str:
        d = self.ensure_asset_dir(project_id, asset_id)
        dest = d / dest_name
        shutil.copy2(src, dest)
        return str(dest.relative_to(self.root))
