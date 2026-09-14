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

from dataclasses import dataclass, field, replace

from . import voices as voice_catalog
from .segment import segment

SEPARATORS = ("=", "＝")
COMMENT_PREFIX = "//"
DIRECTIVE_PREFIX = "#!"
HEADER_PREFIX = "#"

# 听力测试不能念中文释义 —— 那等于直接报答案；也不给慢速，否则听力难度失真。
# 这类设定写在课文文件里而不是命令行参数里：出题的人定，做题的人不用记参数。
PRESETS = {
    "listening": {"slow": False, "gloss_enabled": False, "between_items_ms": 1200},
}

DIRECTIVE_FIELDS = {
    "voice": "target_voice",
    "gloss-voice": "gloss_voice",
    "slow-rate": "slow_rate",
    "gap": "between_items_ms",
}


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
    overrides: dict[str, object] = field(default_factory=dict)  # 由 #! 声明得出


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


def _parse_directive(body: str, line_no: int) -> dict[str, object]:
    """解析一行 `#!` 声明，例如 `#! listening voice=es-MX-JorgeNeural`。"""
    overrides: dict[str, object] = {}
    for token in body.split():
        if "=" not in token:
            if token not in PRESETS:
                raise LessonError(f"第 {line_no} 行：未知的模式 {token!r}，可用：{', '.join(PRESETS)}")
            overrides.update(PRESETS[token])
            continue

        key, value = token.split("=", 1)
        field_name = DIRECTIVE_FIELDS.get(key)
        if not field_name:
            raise LessonError(
                f"第 {line_no} 行：未知的设定 {key!r}，可用：{', '.join(DIRECTIVE_FIELDS)}"
            )
        if field_name == "between_items_ms":
            if not value.isdigit():
                raise LessonError(f"第 {line_no} 行：gap 要是毫秒数，收到 {value!r}")
            overrides[field_name] = int(value)
        else:
            overrides[field_name] = value
    return overrides


def parse(text: str) -> Lesson:
    title: str | None = None
    items: list[Item] = []
    headers: dict[int, list[str]] = {}
    overrides: dict[str, object] = {}

    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith(COMMENT_PREFIX):
            continue

        # 必须排在 HEADER_PREFIX 之前判断：#! 也是以 # 开头的
        if line.startswith(DIRECTIVE_PREFIX):
            overrides.update(_parse_directive(line[len(DIRECTIVE_PREFIX) :], line_no))
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
    return Lesson(title=title, items=items, headers=headers, overrides=overrides)


def apply_overrides(style: Style, overrides: dict[str, object]) -> Style:
    """把课文里的 #! 声明套到默认节奏上。音色名在这里统一解析成完整 ID。"""
    resolved = dict(overrides)
    for key in ("target_voice", "gloss_voice"):
        if key in resolved:
            resolved[key] = voice_catalog.resolve(str(resolved[key]))
    return replace(style, **resolved)


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
