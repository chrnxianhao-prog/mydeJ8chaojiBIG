"""给网页出题用的单句合成：一句话进去，base64 的 MP3 出来。

每日页的出题脚本都用这个，别各自再抄一份引擎配置 ——
2026-09-25 以前每个脚本都自己写了一遍 claude-high 的配置，换音色时得一个个改。

    import sys; sys.path.insert(0, "<仓库根目录>")
    from profe.voz import hablar
    audio["w0"] = hablar("la cuchara", speed=0.85)               # 默认拉美口音
    audio["w0_es"] = hablar("la cuchara", acento="espana")        # 西班牙口音
"""

from __future__ import annotations

import base64
from pathlib import Path

from .providers.local import a_mp3, motor

# 模型缓存固定放仓库根目录的 .piper-cache/，从哪个目录跑脚本都能找到
CACHE = Path(__file__).resolve().parent.parent / ".piper-cache"


def hablar(texto: str, speed: float = 1.0, acento: str = "latam", bitrate: int = 56) -> str:
    tts, sid = motor(acento, CACHE)
    out = tts.generate(texto, sid=sid, speed=speed)
    return base64.b64encode(a_mp3(out.samples, out.sample_rate, bitrate)).decode()
