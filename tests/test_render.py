import asyncio

import pytest

from conftest import FRAME_MS, mp3
from profe.audio import duration_ms
from profe.lesson import Style, build_plan, parse
from profe.render import render


class FakeProvider:
    """替代真实合成：按文字长度返回对应帧数的合法音频，并记下每次请求。"""

    name = "fake"

    def __init__(self):
        self.calls = []

    async def synthesize(self, text: str, voice: str, rate: str) -> bytes:
        self.calls.append((text, voice, rate))
        return mp3(max(1, len(text)))


def _render(plan, provider, **kwargs):
    return asyncio.run(render(plan, provider, **kwargs))


def test_renders_every_spoken_step_into_one_track():
    provider = FakeProvider()
    plan = build_plan(parse("Hola = 你好"), Style())
    audio, cues = _render(plan, provider)

    assert [cue.role for cue in cues] == ["normal", "slow", "gloss"]
    assert duration_ms(audio) > sum(cue.duration_ms for cue in cues)  # 停顿占了差额


def test_cue_offsets_line_up_with_the_stitched_audio():
    provider = FakeProvider()
    style = Style(slow=False, gloss_enabled=False, after_normal_ms=0, between_items_ms=480)
    audio, cues = _render(build_plan(parse("Hola\nAdiós"), style), provider)

    assert cues[0].start_ms == 0
    assert cues[1].start_ms == pytest.approx(cues[0].duration_ms + 480)
    assert duration_ms(audio) == pytest.approx(
        cues[1].start_ms + cues[1].duration_ms + 480
    )


def test_shadow_pause_really_matches_the_slow_clip_length():
    provider = FakeProvider()
    style = Style(gloss_enabled=False, after_normal_ms=0, between_items_ms=0, shadow_extra_ms=240)
    audio, cues = _render(build_plan(parse("Hola"), style), provider)

    normal, slow = cues
    silence_after_slow = duration_ms(audio) - (slow.start_ms + slow.duration_ms)
    assert silence_after_slow == pytest.approx(slow.duration_ms + 240, abs=FRAME_MS)


def test_identical_requests_are_synthesized_once():
    provider = FakeProvider()
    _render(build_plan(parse("Hola\nHola"), Style(slow=False, gloss_enabled=False)), provider)
    assert len(provider.calls) == 1


def test_normal_and_slow_are_separate_requests():
    provider = FakeProvider()
    _render(build_plan(parse("Hola"), Style(gloss_enabled=False)), provider)
    assert [rate for _, _, rate in provider.calls] == ["+0%", "-35%"]


def test_cache_survives_a_rebuild(tmp_path):
    plan = build_plan(parse("Hola = 你好"), Style())

    first = FakeProvider()
    audio_a, _ = _render(plan, first, cache_dir=tmp_path)
    assert first.calls

    second = FakeProvider()
    audio_b, _ = _render(plan, second, cache_dir=tmp_path)
    assert second.calls == []
    assert audio_a == audio_b


def test_progress_is_reported_to_completion():
    seen = []
    plan = build_plan(parse("Hola = 你好"), Style())
    _render(plan, FakeProvider(), on_progress=lambda done, total: seen.append((done, total)))

    total = seen[-1][1]
    assert seen[-1] == (total, total)
