"""合成引擎接口。

上层（课程编排、拼接）不关心声音是谁合成的，只认这一个协议。
将来要换更适合视频配音的引擎，加一个实现这个协议的文件即可，其余代码不动。
"""

from __future__ import annotations

from typing import Protocol


class SynthesisError(RuntimeError):
    """合成失败，且带上给用户看的处置建议。"""


class Provider(Protocol):
    name: str

    async def synthesize(self, text: str, voice: str, rate: str) -> bytes:
        """返回一段 MPEG 音频。rate 形如 "+0%" / "-25%"。"""
        ...


def get_provider(name: str) -> Provider:
    if name == "edge":
        from .edge import EdgeProvider

        return EdgeProvider()
    raise SynthesisError(f"未知的合成引擎：{name}")
