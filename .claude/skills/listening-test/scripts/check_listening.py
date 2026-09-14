#!/usr/bin/env python3
"""听力材料上机前的自检。

这个脚本守的是一条红线：听力材料里绝不能把中文念出来。
profe 默认节奏会朗读中文释义，忘写 `#! listening` 就等于在音频里直接报答案，
而这种错误在文件上看不出来 —— 必须真的把编排跑出来看念了什么。

用法：python .claude/skills/listening-test/scripts/check_listening.py 听力材料/xxx.txt
退出码 0 表示可以交给学生，非 0 表示别提交。
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from profe.lesson import LessonError, Style, apply_overrides, build_plan, parse  # noqa: E402
from profe.segment import CJK, script_of  # noqa: E402

# Edge TTS 的语速大约每秒 14 个字符，够用来估个时长量级
CHARS_PER_SECOND = 14


def main() -> int:
    if len(sys.argv) != 2:
        print("用法：check_listening.py <听力材料/xxx.txt>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"✗ 找不到文件：{path}", file=sys.stderr)
        return 2

    try:
        lesson = parse(path.read_text(encoding="utf-8"))
    except LessonError as error:
        print(f"✗ 课文解析失败：{error}", file=sys.stderr)
        return 1

    style = apply_overrides(Style(), lesson.overrides)
    spoken = [step for step in build_plan(lesson, style) if hasattr(step, "text")]

    problems: list[str] = []

    if style.gloss_enabled:
        problems.append(
            "会朗读中文释义 —— 第一行缺 `#! listening`。"
            "这样生成的音频会直接报答案，整套题作废。"
        )
    if style.slow:
        problems.append("开着慢速复读 —— 听力测试不该给慢速，难度会失真。")

    leaked = [step.text for step in spoken if any(script_of(c) == CJK for c in step.text)]
    if leaked:
        problems.append(f"有 {len(leaked)} 段会念出中文：{leaked[:3]}")

    if problems:
        print(f"✗ {path.name} 不能用：", file=sys.stderr)
        for problem in problems:
            print(f"   · {problem}", file=sys.stderr)
        return 1

    seconds = sum(len(step.text) for step in spoken) / CHARS_PER_SECOND
    seconds += len(lesson.items) * style.between_items_ms / 1000

    print(f"✓ {path.name}")
    print(f"   标题：{lesson.title or '（无）'}")
    print(f"   句数：{len(lesson.items)}　语音段：{len(spoken)}")
    print(f"   音色：{style.target_voice}　句间停顿：{style.between_items_ms} ms")
    print(f"   预估时长：约 {int(seconds // 60)} 分 {int(seconds % 60)} 秒")
    print("   中文泄漏：无")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
