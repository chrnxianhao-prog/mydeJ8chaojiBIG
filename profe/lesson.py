"""课程文件解析与教学节奏编排。

课文格式刻意做得能用记事本写：

    # Lección 1 — Saludos
    // 这行是批注，不会被念出来
    ¿Cómo estás? = 你好吗？
    Buenos días.  = 早上好。

每句生成的节奏是：正常语速 → 停顿 → 慢速 → 跟读时间 → 中文释义。
慢速那遍是学发音的关键：正常语速下 "¿Cómo estás?" 是连读的一坨，
慢速才听得出 s 有没有咬住、重音落在哪个音节。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import voices as voice_catalog
from .segment import segment

SEPARATORS = ("=", "＝")
COMMENT_PREFIX = "//"
HEADER_PREFIX = "#"


@dataclass(frozen=True)
class Item:
    target: str           # 西班牙语原文
    gloss: str | None     # 中文释义，可以没有
    line_no: int


@dataclass(frozen=True)
class Lesson:
    title: str | None
    items: list[Item]
    # 第几句之前要念哪些标题。课程标题和首个小节标题都落在第 0 句前，所以是列表。
    headers: dict[int, list[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class Speak:
    text: str
    voice: str
    rate: str
    role: str  # normal / slow / gloss / header


@dataclass(frozen=True)
class Pause:
    ms: int = 0
    mirror: float = 0.0  # 再加上一段语音时长的这个倍数


Step = Speak | Pause


@dataclass(frozen=True)
class Style:
    target_voice: str = voice_catalog.DEFAULT_TARGET
    gloss_voice: str = voice_catalog.DEFAULT_GLOSS
    slow: bool = True
    slow_rate: str = "-35%"
    gloss_enabled: bool = True
    after_normal_ms: int = 500
    shadow_extra_ms: int = 250   # 跟读时间 = 慢速那遍的时长 + 这个余量
    between_items_ms: int = 900


class LessonError(ValueError):
    pass


def parse(text: str) -> Lesson:
    title: str | None = None
    items: list[Item] = []
    headers: dict[int, list[str]] = {}

    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith(COMMENT_PREFIX):
            continue

        if line.startswith(HEADER_PREFIX):
            header = line.lstrip(HEADER_PREFIX).strip()
            if not header:
                continue
            if title is None:
                title = header
            headers.setdefault(len(items), []).append(header)
            continue

        target, gloss = line, None
        for sep in SEPARATORS:
            if sep in line:
                left, right = line.split(sep, 1)
                target, gloss = left.strip(), right.strip() or None
                break

        if not target:
            raise LessonError(f"第 {line_no} 行只有释义没有原文：{raw!r}")
        items.append(Item(target=target, gloss=gloss, line_no=line_no))

    if not items:
        raise LessonError("课文里没有任何句子")
    return Lesson(title=title, items=items, headers=headers)


def speak_mixed(text: str, style: Style, rate: str, role: str) -> list[Speak]:
    """一行里中西混排时按书写系统拆开，各段配各段的音色。"""
    return [
        Speak(
            text=chunk,
            voice=voice_catalog.for_script(script, style.target_voice, style.gloss_voice),
            rate=rate,
            role=role,
        )
        for script, chunk in segment(text)
    ]


def build_plan(lesson: Lesson, style: Style) -> list[Step]:
    plan: list[Step] = []

    for index, item in enumerate(lesson.items):
        for header in lesson.headers.get(index, ()):
            plan.extend(speak_mixed(header, style, "+0%", "header"))
            plan.append(Pause(ms=700))

        plan.extend(speak_mixed(item.target, style, "+0%", "normal"))
        plan.append(Pause(ms=style.after_normal_ms))

        if style.slow:
            plan.extend(speak_mixed(item.target, style, style.slow_rate, "slow"))
            plan.append(Pause(ms=style.shadow_extra_ms, mirror=1.0))

        if style.gloss_enabled and item.gloss:
            plan.extend(speak_mixed(item.gloss, style, "+0%", "gloss"))

        plan.append(Pause(ms=style.between_items_ms))

    return plan
