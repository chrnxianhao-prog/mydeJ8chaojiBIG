import pytest

from conftest import FRAME_BYTES, FRAME_MS, mp3
from profe.audio import (
    AudioFormatError,
    duration_ms,
    frames,
    silence_like,
    stitch,
    strip_container,
)


def test_frame_geometry_matches_edge_tts_format():
    parsed = frames(mp3(3))
    assert [frame.length for frame in parsed] == [FRAME_BYTES] * 3
    assert parsed[0].sample_rate == 24000
    assert parsed[0].duration_ms == pytest.approx(FRAME_MS)


def test_duration_adds_up():
    assert duration_ms(mp3(50)) == pytest.approx(50 * FRAME_MS)


def test_strips_id3v2_tag():
    size = 0x40
    tag = b"ID3\x04\x00\x00" + bytes([0, 0, 0, size]) + bytes(size)
    assert strip_container(tag + mp3(2)) == mp3(2)


def test_strips_id3v1_trailer():
    assert strip_container(mp3(2) + b"TAG" + bytes(125)) == mp3(2)


def test_resyncs_past_corrupt_bytes():
    # 中间插一段垃圾，解析器应该重新找同步字而不是整段放弃
    assert len(frames(mp3(2) + b"\x00\x11\x22" + mp3(2))) == 4


def test_silence_copies_the_reference_frame_format():
    silence = silence_like(mp3(1), 240)
    parsed = frames(silence)
    assert len(parsed) == 10
    assert all(frame.length == FRAME_BYTES for frame in parsed)
    assert silence[:4] == mp3(1)[:4]        # 帧头一致，拼接后不会格式错位
    assert set(silence[4:FRAME_BYTES]) == {0}  # 负载全零 —— 解码出来就是静音


def test_silence_rounds_to_whole_frames_and_never_vanishes():
    assert silence_like(mp3(1), 0) == b""
    assert duration_ms(silence_like(mp3(1), 5)) == pytest.approx(FRAME_MS)


def test_silence_rejects_unparsable_reference():
    with pytest.raises(AudioFormatError):
        silence_like(b"not audio at all", 100)


def test_stitch_reports_each_clip_start():
    audio, starts = stitch([mp3(10), mp3(5), mp3(20)])
    assert starts == pytest.approx([0.0, 10 * FRAME_MS, 15 * FRAME_MS])
    assert duration_ms(audio) == pytest.approx(35 * FRAME_MS)
