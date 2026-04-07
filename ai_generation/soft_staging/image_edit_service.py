from __future__ import annotations

import base64
import os
import urllib.request
from pathlib import Path

from openai import OpenAI


def _env(name: str, default: str) -> str:
    v = os.getenv(name)
    return v.strip() if v and v.strip() else default


class OpenAIImageEditService:
    """调用 OpenAI 图片编辑 API，输出软装后的栅格图。

    费用主要来自本接口（gpt-image 类），与是否「看图」相比通常占大头。
    可用环境变量压价（见 .env.example），默认偏向省钱：1024 + medium。
    """

    def __init__(
        self,
        model: str | None = None,
        size: str | None = None,
        quality: str | None = None,
    ) -> None:
        self._client = OpenAI()
        self._model = model or _env("OPENAI_IMAGE_MODEL", "gpt-image-1")
        self._size = size or _env("OPENAI_IMAGE_EDIT_SIZE", "1024x1024")
        self._quality = quality or _env("OPENAI_IMAGE_EDIT_QUALITY", "medium")
        self._input_fidelity = _env("OPENAI_IMAGE_INPUT_FIDELITY", "high")

    def edit(
        self,
        image_path: str | Path,
        prompt: str,
        mask_path: str | Path | None = None,
    ) -> bytes:
        path = Path(image_path)
        mpath = Path(mask_path) if mask_path is not None else None

        with open(path, "rb") as image_f:
            if mpath is not None:
                with open(mpath, "rb") as mask_f:
                    return self._call_edit(image_f, prompt, mask_f)
            return self._call_edit(image_f, prompt, None)

    def _call_edit(self, image_f, prompt: str, mask_f):
        kwargs = {
            "model": self._model,
            "image": image_f,
            "prompt": prompt,
        }
        if mask_f is not None:
            kwargs["mask"] = mask_f

        extra_base = {"size": self._size, "quality": self._quality}
        fid = self._input_fidelity.lower()
        if fid not in ("high", "low"):
            fid = "high"

        try:
            resp = self._client.images.edit(
                **kwargs, **extra_base, input_fidelity=fid
            )
        except TypeError:
            try:
                resp = self._client.images.edit(**kwargs, **extra_base)
            except TypeError:
                if self._size == "auto":
                    try:
                        resp = self._client.images.edit(
                            **kwargs,
                            **{**extra_base, "size": "1536x1024"},
                        )
                    except TypeError:
                        resp = self._client.images.edit(**kwargs)
                else:
                    resp = self._client.images.edit(**kwargs)

        item = resp.data[0]
        if item.b64_json:
            return base64.standard_b64decode(item.b64_json)
        if item.url:
            return urllib.request.urlopen(item.url).read()
        raise RuntimeError("Image edit response missing b64_json and url")
