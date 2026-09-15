#!/usr/bin/env python3
"""把渲染好的听力 mp3 包成一个可直接点播的网页。

学生不想下载文件也不想跑命令，只想点开就听。音频以 data URI 内嵌，
所以这个页面是自足的，发布成 Artifact 后手机电脑都能直接播。

页面上刻意不放原文和题目 —— 提前看到就测不出听力。

用法：
  python .claude/skills/listening-test/scripts/build_page.py 音频.mp3 "La entrevista de trabajo" \
      --date "15 sep 2026" -o /tmp/.../page.html
"""

import argparse
import base64
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "player.html"
MAX_BYTES = 12 * 1024 * 1024  # Artifact 上限 16MB，base64 会膨胀约三分之一


def main() -> int:
    parser = argparse.ArgumentParser(description="把听力 mp3 包成可点播的网页")
    parser.add_argument("audio", help="profe 渲染出来的 mp3")
    parser.add_argument("title", help="页面标题，用西语场景名，如 La entrevista de trabajo")
    parser.add_argument("--date", default="", help="副标题里的日期，如 15 sep 2026")
    parser.add_argument("-o", "--output", required=True, help="输出的 html 路径")
    args = parser.parse_args()

    audio = Path(args.audio)
    if not audio.exists():
        print(f"✗ 找不到音频：{audio}", file=sys.stderr)
        return 1

    raw = audio.read_bytes()
    encoded = base64.b64encode(raw).decode()
    if len(encoded) > MAX_BYTES:
        print(
            f"✗ 音频太大（{len(raw)/1024/1024:.1f} MB，内嵌后约 {len(encoded)/1024/1024:.1f} MB）。"
            f"把材料拆短一些。",
            file=sys.stderr,
        )
        return 1

    eyebrow = f"Comprensión auditiva · {args.date}" if args.date else "Comprensión auditiva"
    html = TEMPLATE.read_text(encoding="utf-8")
    html = (
        html.replace("__TITLE__", args.title)
        .replace("__EYEBROW__", eyebrow)
        .replace("__AUDIO__", encoded)
    )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")

    print(f"✓ {out}")
    print(f"   音频 {len(raw)/1024:.0f} KB　页面 {out.stat().st_size/1024:.0f} KB")
    print("   接着用 Artifact 工具发布这个文件，把链接发给学生。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
