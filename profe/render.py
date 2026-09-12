"""把编排好的节奏渲染成一个音频文件。

同一段文字在一份课文里会重复出现（正常速 + 慢速是两次请求，但跨课复用很常见），
所以按内容哈希做缓存：改一行课文重建，不会把整课重新合成一遍。
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from .audio import duration_ms, silence_like, stitch
from .lesson import Pause, Speak, Step, Style, speak_mixed
from .providers import Provider, SynthesisError

DEFAULT_CONCURRENCY = 4


@dataclass(frozen=True)
class Cue:
    """时间轴上的一段语音。后期做视频配音时，字幕和对轨就靠它。"""

    start_ms: float
    duration_ms: float
    role: str
    voice: str
    text: str


def _cache_key(provider_name: str, speak: Speak) -> str:
    raw = f"{provider_name}|{speak.voice}|{speak.rate}|{speak.text}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


async def _synthesize_all(
    plan: list[Step],
    provider: Provider,
    cache_dir: Path | None,
    concurrency: int,
    on_progress: Callable[[int, int], None] | None,
) -> dict[str, bytes]:
    wanted: dict[str, Speak] = {}
    for step in plan:
        if isinstance(step, Speak):
            wanted.setdefault(_cache_key(provider.name, step), step)

    clips: dict[str, bytes] = {}
    pending: dict[str, Speak] = {}
    for key, speak in wanted.items():
        cached = cache_dir / f"{key}.mp3" if cache_dir else None
        if cached and cached.exists():
            clips[key] = cached.read_bytes()
        else:
            pending[key] = speak

    total = len(wanted)
    done = len(clips)
    if on_progress:
        on_progress(done, total)

    semaphore = asyncio.Semaphore(concurrency)
    lock = asyncio.Lock()

    async def run(key: str, speak: Speak) -> None:
        nonlocal done
        async with semaphore:
            audio = await provider.synthesize(speak.text, speak.voice, speak.rate)
        if cache_dir:
            (cache_dir / f"{key}.mp3").write_bytes(audio)
        async with lock:
            clips[key] = audio
            done += 1
            if on_progress:
                on_progress(done, total)

    if pending:
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
        await asyncio.gather(*(run(key, speak) for key, speak in pending.items()))

    return clips


async def render(
    plan: list[Step],
    provider: Provider,
    *,
    cache_dir: Path | None = None,
    concurrency: int = DEFAULT_CONCURRENCY,
    on_progress: Callable[[int, int], None] | None = None,
) -> tuple[bytes, list[Cue]]:
    clips = await _synthesize_all(plan, provider, cache_dir, concurrency, on_progress)

    pieces: list[bytes] = []
    speaking: list[tuple[int, Speak, float]] = []  # 片段下标、内容、时长
    reference: bytes | None = None
    previous_speech_ms = 0.0

    for step in plan:
        if isinstance(step, Speak):
            audio = clips[_cache_key(provider.name, step)]
            reference = reference or audio
            previous_speech_ms = duration_ms(audio)
            speaking.append((len(pieces), step, previous_speech_ms))
            pieces.append(audio)
            continue

        gap = step.ms + step.mirror * previous_speech_ms
        if gap > 0 and reference:
            pieces.append(silence_like(reference, gap))

    if not pieces:
        raise SynthesisError("没有可渲染的内容")

    audio, starts = stitch(pieces)
    cues = [
        Cue(
            start_ms=round(starts[index], 1),
            duration_ms=round(length, 1),
            role=speak.role,
            voice=speak.voice,
            text=speak.text,
        )
        for index, speak, length in speaking
    ]
    return audio, cues


def write_timeline(path: Path, cues: list[Cue]) -> None:
    payload = {"cues": [asdict(cue) for cue in cues]}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


async def render_text(
    text: str,
    provider: Provider,
    target_voice: str,
    gloss_voice: str,
    rate: str = "+0%",
) -> bytes:
    """单句朗读：只做混排切段，不加教学节奏。"""
    style = Style(target_voice=target_voice, gloss_voice=gloss_voice)
    plan: list[Step] = list(speak_mixed(text, style, rate, "normal"))
    if not plan:
        raise SynthesisError("没有可朗读的文字")
    audio, _ = await render(plan, provider)
    return audio
