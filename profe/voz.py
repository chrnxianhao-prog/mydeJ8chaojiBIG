"""给网页出题用的单句合成：一句话进去，base64 的 MP3 出来。

每日页的出题脚本都用这个，别各自再抄一份引擎配置 ——
2026-09-25 以前每个脚本都自己写了一遍 claude-high 的配置，换音色时得一个个改。

    import sys; sys.path.insert(0, "<仓库根目录>")
    from profe.voz import hablar
    audio["w0"] = hablar("la cuchara", speed=0.85)               # 默认拉美口音
    audio["w0_es"] = hablar("la cuchara", acento="espana")        # 西班牙口音
    audio["t0"] = hablar_palabra("habló")                          # 单个词一律走这个

⚠️ 单个词别直接喂给 hablar()。Kokoro 是拿整句训练的，单独念一个词时开头会多出一个杂音：
2026-09-26 学生听写把 habló 写成 sabor（「这个 hablo 怎么读成 sablo」），
whisper 听原样的单词也是 habló→sablo、hermano→ser mano、hijo→dijo、llevar→Y éste，
16 个词只认对 6 个；放进「Digo ___, otra vez.」里念，当天页面上 33 个词全认对。
词放句尾也会糊（La palabra es: habló → Ableu），「Escribe ___」会跟元音开头的词连读，
所以就用 Digo ___, otra vez.。
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


MARCO_PALABRA = "Digo {}, otra vez."   # 我说 ___，再说一遍


def hablar_palabra(palabra: str, speed: float = 0.9, acento: str = "latam", bitrate: int = 56) -> str:
    """单个词放进固定短句中间念，避开 Kokoro 念孤立词时开头的杂音。"""
    return hablar(MARCO_PALABRA.format(palabra), speed=speed, acento=acento, bitrate=bitrate)
