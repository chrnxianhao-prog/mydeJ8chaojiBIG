"""精选音色表。

完整音色表有几百个（`profe voices` 可以实时拉取），这里只列教学常用的：
学西语先要定口音 —— 西班牙的 θ 音（ceceo）和拉美的 s 音是两套发音习惯，
学谁的口音要一开始就选定，中途换会把耳朵搞乱。
"""

from __future__ import annotations

from dataclasses import dataclass

from .segment import CJK, LATIN


@dataclass(frozen=True)
class Voice:
    id: str
    label: str
    accent: str


SPANISH: tuple[Voice, ...] = (
    Voice("es-ES-ElviraNeural", "Elvira · 女声", "西班牙（卡斯蒂利亚）"),
    Voice("es-ES-AlvaroNeural", "Álvaro · 男声", "西班牙（卡斯蒂利亚）"),
    Voice("es-MX-DaliaNeural", "Dalia · 女声", "墨西哥"),
    Voice("es-MX-JorgeNeural", "Jorge · 男声", "墨西哥"),
    Voice("es-AR-ElenaNeural", "Elena · 女声", "阿根廷"),
    Voice("es-CO-SalomeNeural", "Salomé · 女声", "哥伦比亚"),
    Voice("es-US-PalomaNeural", "Paloma · 女声", "美国西语"),
)

CHINESE: tuple[Voice, ...] = (
    Voice("zh-CN-XiaoxiaoNeural", "晓晓 · 女声", "普通话"),
    Voice("zh-CN-YunxiNeural", "云希 · 男声", "普通话"),
)

ENGLISH: tuple[Voice, ...] = (
    Voice("en-US-AriaNeural", "Aria · 女声", "美式"),
    Voice("en-US-GuyNeural", "Guy · 男声", "美式"),
    Voice("en-GB-SoniaNeural", "Sonia · 女声", "英式"),
)

DEFAULT_TARGET = SPANISH[0].id
DEFAULT_GLOSS = CHINESE[0].id

_BY_ID = {voice.id: voice for voice in SPANISH + CHINESE + ENGLISH}


def resolve(name: str) -> str:
    """把简写或音色 ID 解析成完整音色 ID。

    支持三种写法：完整 ID（es-MX-JorgeNeural）、区域码（es-MX / es）、
    以及人名（jorge）。解析不出来就原样返回 —— 微软的音色远不止这张表，
    用户填了表外的合法 ID 不应该被挡住。
    """
    name = name.strip()
    if name in _BY_ID:
        return name

    lowered = name.lower()
    for voice in SPANISH + CHINESE + ENGLISH:
        if voice.id.lower() == lowered:
            return voice.id
        if voice.id.split("-")[2].removesuffix("Neural").lower() == lowered:
            return voice.id

    for voice in SPANISH + CHINESE + ENGLISH:
        locale = "-".join(voice.id.split("-")[:2])
        if lowered in (locale.lower(), locale.split("-")[0].lower()):
            return voice.id

    return name


def for_script(script: str, target: str, gloss: str) -> str:
    """按书写系统挑音色：汉字走释义音色，拉丁字母走目标语音色。"""
    return gloss if script == CJK else target


def catalog() -> dict[str, tuple[Voice, ...]]:
    return {"西班牙语": SPANISH, "中文": CHINESE, "英语": ENGLISH}


__all__ = [
    "Voice",
    "SPANISH",
    "CHINESE",
    "ENGLISH",
    "DEFAULT_TARGET",
    "DEFAULT_GLOSS",
    "resolve",
    "for_script",
    "catalog",
    "CJK",
    "LATIN",
]
