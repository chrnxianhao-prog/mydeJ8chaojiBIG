"""按书写系统把一行混排文字切成段。

一个音色念不了两种语言：拿中文音色去念 "buenos días" 会糊成一团，
拿西语音色念中文则直接出乱音。所以合成前必须先按文字切段、各段配各段的音色。
"""

from __future__ import annotations

import unicodedata

CJK = "cjk"
LATIN = "latin"

_CJK_RANGES = (
    (0x2E80, 0x2EFF),    # 康熙部首
    (0x3000, 0x303F),    # 中文标点
    (0x3040, 0x30FF),    # 日文假名
    (0x3400, 0x4DBF),    # 汉字扩展 A
    (0x4E00, 0x9FFF),    # 基本汉字
    (0xF900, 0xFAFF),    # 兼容汉字
    (0xFF00, 0xFFEF),    # 全角字符
)


def script_of(char: str) -> str | None:
    """返回该字符所属的书写系统；标点、数字、空白返回 None，表示跟随上下文。"""
    code = ord(char)
    for low, high in _CJK_RANGES:
        if low <= code <= high:
            return CJK
    if char.isalpha():
        # 剥掉变音符号后仍是 ASCII 字母的算拉丁字母：á é í ñ ü 都在此列
        base = unicodedata.normalize("NFD", char)[0]
        if "a" <= base.lower() <= "z":
            return LATIN
        return None
    return None


def segment(text: str) -> list[tuple[str, str]]:
    """切成 [(书写系统, 原文), ...]，标点和空白原样保留。

    未定性的字符跟随前一段（标点几乎总是收束前一句）；出现在开头时并入第一段。
    """
    runs: list[tuple[str, str]] = []
    current: str | None = None
    buffer = ""

    for char in text:
        script = script_of(char)
        if script is None:
            buffer += char
            continue
        if current is None:
            current = script
        elif script != current:
            runs.append((current, buffer))
            buffer = ""
            current = script
        buffer += char

    if current is not None:
        runs.append((current, buffer))
    elif text.strip():
        # 纯数字或纯标点，没有任何字母可判定：交给拉丁音色念
        runs.append((LATIN, text))

    return [(script, chunk) for script, chunk in runs if chunk.strip()]


def dominant_script(text: str) -> str:
    """整行文字的主导书写系统，用于挑默认音色。"""
    cjk = latin = 0
    for char in text:
        script = script_of(char)
        if script == CJK:
            cjk += 1
        elif script == LATIN:
            latin += 1
    return CJK if cjk > latin else LATIN
