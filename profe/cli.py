"""命令行入口。"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from unicodedata import east_asian_width

from . import voices as voice_catalog
from .audio import duration_ms
from .lesson import LessonError, Style, build_plan, parse
from .providers import SynthesisError, get_provider
from .render import render, render_text, write_timeline

CACHE_DIR = Path(".profe-cache")


def _pad(text: str, width: int) -> str:
    """按显示宽度补空格：汉字占两格，否则中西混排的表格会错行。"""
    shown = sum(2 if east_asian_width(char) in "WF" else 1 for char in text)
    return text + " " * max(0, width - shown)


def _format_duration(ms: float) -> str:
    seconds = round(ms / 1000)
    return f"{seconds // 60} 分 {seconds % 60} 秒"


def _style_from_args(args: argparse.Namespace) -> Style:
    return Style(
        target_voice=voice_catalog.resolve(args.voice),
        gloss_voice=voice_catalog.resolve(args.gloss_voice),
        slow=not args.no_slow,
        slow_rate=args.slow_rate,
        gloss_enabled=not args.no_gloss,
        between_items_ms=args.gap,
    )


def _progress(done: int, total: int) -> None:
    if sys.stderr.isatty():
        print(f"\r  合成中 {done}/{total}", end="", file=sys.stderr, flush=True)
    elif done == total:
        print(f"  合成完成 {done}/{total}", file=sys.stderr)


def cmd_lesson(args: argparse.Namespace) -> int:
    source = Path(args.lesson)
    if not source.exists():
        print(f"找不到课文文件：{source}", file=sys.stderr)
        return 1

    try:
        lesson = parse(source.read_text(encoding="utf-8"))
    except LessonError as error:
        print(f"课文解析失败：{error}", file=sys.stderr)
        return 1

    style = _style_from_args(args)
    plan = build_plan(lesson, style)
    output = Path(args.output) if args.output else source.with_suffix(".mp3")
    output.parent.mkdir(parents=True, exist_ok=True)

    print(f"课程：{lesson.title or source.stem}（{len(lesson.items)} 句）")
    print(f"目标语音色：{style.target_voice}    释义音色：{style.gloss_voice}")

    provider = get_provider(args.provider)
    cache = None if args.no_cache else CACHE_DIR
    try:
        audio, cues = asyncio.run(
            render(plan, provider, cache_dir=cache, on_progress=_progress)
        )
    except SynthesisError as error:
        print(f"\n{error}", file=sys.stderr)
        return 2

    if sys.stderr.isatty():
        print(file=sys.stderr)
    output.write_bytes(audio)
    print(f"已生成 {output}（{_format_duration(duration_ms(audio))}）")

    if args.timeline:
        timeline = output.with_suffix(".timeline.json")
        write_timeline(timeline, cues)
        print(f"时间轴 {timeline}（{len(cues)} 段）")
    return 0


def cmd_say(args: argparse.Namespace) -> int:
    provider = get_provider(args.provider)
    try:
        audio = asyncio.run(
            render_text(
                args.text,
                provider,
                voice_catalog.resolve(args.voice),
                voice_catalog.resolve(args.gloss_voice),
                rate=args.rate,
            )
        )
    except SynthesisError as error:
        print(str(error), file=sys.stderr)
        return 2

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(audio)
    print(f"已生成 {output}（{_format_duration(duration_ms(audio))}）")
    return 0


def cmd_voices(args: argparse.Namespace) -> int:
    if not args.all:
        for group, items in voice_catalog.catalog().items():
            print(f"\n{group}")
            for voice in items:
                print(f"  {_pad(voice.id, 26)} {_pad(voice.label, 18)} {voice.accent}")
        print("\n（只列了教学常用的；加 --all 拉取微软的完整音色表）")
        return 0

    provider = get_provider(args.provider)
    try:
        found = asyncio.run(provider.list_voices(args.prefix))
    except SynthesisError as error:
        print(str(error), file=sys.stderr)
        return 2
    for voice in found:
        print(f"  {voice['ShortName']:<32} {voice['Gender']:<8} {voice['Locale']}")
    print(f"\n共 {len(found)} 个音色")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    print("1. 检查 edge-tts 是否装好 ... ", end="")
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        print("没装\n   跑一下：pip install edge-tts")
        return 1
    print("好")

    print("2. 试合成一句西班牙语 ... ", end="", flush=True)
    provider = get_provider(args.provider)
    try:
        audio = asyncio.run(provider.synthesize("Hola, ¿qué tal?", voice_catalog.DEFAULT_TARGET, "+0%"))
    except SynthesisError as error:
        print(f"失败\n   {error}")
        return 2

    length = duration_ms(audio)
    print(f"好（{len(audio)} 字节 / {length / 1000:.1f} 秒）")
    if length <= 0:
        print("   返回的音频解析不出帧，格式可能变了，拼接会出问题。")
        return 2
    print("\n一切正常，可以用 profe lesson 生成课程音频了。")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="profe",
        description="西班牙语听说练习音频生成器（基于免费的 Edge TTS）",
    )
    parser.add_argument("--provider", default="edge", help="合成引擎，默认 edge")
    subparsers = parser.add_subparsers(dest="command", required=True)

    lesson = subparsers.add_parser("lesson", help="把课文生成为一条完整的练习音频")
    lesson.add_argument("lesson", help="课文文件路径")
    lesson.add_argument("-o", "--output", help="输出的 mp3 路径，默认与课文同名")
    lesson.add_argument("--voice", default=voice_catalog.DEFAULT_TARGET, help="西语音色，可写 es-MX 这类简写")
    lesson.add_argument("--gloss-voice", default=voice_catalog.DEFAULT_GLOSS, help="中文释义音色")
    lesson.add_argument("--slow-rate", default="-35%", help="慢速那一遍的语速，默认 -35%%")
    lesson.add_argument("--gap", type=int, default=900, help="句与句之间的停顿毫秒数")
    lesson.add_argument("--no-slow", action="store_true", help="不要慢速复读那一遍")
    lesson.add_argument("--no-gloss", action="store_true", help="不要中文释义，做纯西语沉浸材料")
    lesson.add_argument("--no-cache", action="store_true", help="不使用本地缓存")
    lesson.add_argument("--timeline", action="store_true", help="额外输出时间轴 json（给后期视频配音用）")
    lesson.set_defaults(func=cmd_lesson)

    say = subparsers.add_parser("say", help="朗读一句话")
    say.add_argument("text", help="要朗读的文字，中西混排会自动切段配音色")
    say.add_argument("-o", "--output", default="say.mp3", help="输出路径，默认 say.mp3")
    say.add_argument("--voice", default=voice_catalog.DEFAULT_TARGET, help="西语音色")
    say.add_argument("--gloss-voice", default=voice_catalog.DEFAULT_GLOSS, help="中文音色")
    say.add_argument("--rate", default="+0%", help="语速，例如 -25%%")
    say.set_defaults(func=cmd_say)

    voices = subparsers.add_parser("voices", help="列出可用音色")
    voices.add_argument("--all", action="store_true", help="拉取微软完整音色表")
    voices.add_argument("--prefix", default="", help="按前缀过滤，例如 es-")
    voices.set_defaults(func=cmd_voices)

    doctor = subparsers.add_parser("doctor", help="检查环境和网络能不能正常合成")
    doctor.set_defaults(func=cmd_doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
