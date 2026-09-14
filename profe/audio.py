"""MPEG 帧层面的音频拼接。

Edge TTS 只输出一种恒定码率的 MPEG 音频，所以片段可以直接按帧拼接，
静音也可以用片段自己的帧头配全零负载合成出来 —— 不需要 ffmpeg，不需要解码。
"""

from __future__ import annotations

from dataclasses import dataclass

# 帧头第 4 位起的版本/层/码率/采样率表。Edge TTS 只发 Layer III。
_BITRATE_V1 = (None, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, None)
_BITRATE_V2 = (None, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, None)
_SAMPLE_RATE = {
    3: (44100, 48000, 32000, None),  # MPEG-1
    2: (22050, 24000, 16000, None),  # MPEG-2
    0: (11025, 12000, 8000, None),   # MPEG-2.5
}


class AudioFormatError(ValueError):
    pass


@dataclass(frozen=True)
class Frame:
    offset: int
    length: int
    sample_rate: int
    samples: int

    @property
    def duration_ms(self) -> float:
        return self.samples * 1000 / self.sample_rate


def _parse_header(data: bytes, offset: int) -> Frame | None:
    if offset + 4 > len(data):
        return None
    b0, b1, b2, b3 = data[offset : offset + 4]
    if b0 != 0xFF or (b1 & 0xE0) != 0xE0:
        return None

    version = (b1 >> 3) & 0b11
    layer = (b1 >> 1) & 0b11
    if version == 1 or layer != 0b01:  # 保留版本号，或非 Layer III
        return None

    bitrate_index = (b2 >> 4) & 0b1111
    rate_index = (b2 >> 2) & 0b11
    padding = (b2 >> 1) & 0b1

    bitrate = (_BITRATE_V1 if version == 3 else _BITRATE_V2)[bitrate_index]
    sample_rate = _SAMPLE_RATE[version][rate_index]
    if not bitrate or not sample_rate:
        return None

    samples = 1152 if version == 3 else 576
    length = (samples // 8) * bitrate * 1000 // sample_rate + padding
    if length <= 4 or offset + length > len(data):
        return None
    return Frame(offset=offset, length=length, sample_rate=sample_rate, samples=samples)


def strip_container(data: bytes) -> bytes:
    """去掉 ID3 标签和首个帧同步之前的垃圾字节。"""
    start = 0
    if data[:3] == b"ID3" and len(data) >= 10:
        size = 0
        for byte in data[6:10]:
            size = (size << 7) | (byte & 0x7F)  # synchsafe 整数
        start = 10 + size

    while start < len(data):
        if _parse_header(data, start):
            break
        start += 1

    end = len(data)
    if data[end - 128 : end - 125] == b"TAG":  # ID3v1 在文件尾部
        end -= 128
    return data[start:end]


def frames(data: bytes) -> list[Frame]:
    """扫描出所有合法帧。遇到坏字节会重新寻找同步字，不会整段放弃。"""
    found: list[Frame] = []
    offset = 0
    while offset < len(data):
        frame = _parse_header(data, offset)
        if frame:
            found.append(frame)
            offset += frame.length
        else:
            offset += 1
    return found


def duration_ms(data: bytes) -> float:
    return sum(frame.duration_ms for frame in frames(strip_container(data)))


def silence_like(reference: bytes, ms: float) -> bytes:
    """按 reference 自己的帧格式合成静音。

    复制它的帧头、把负载清零：解码器读到长度为 0 的主数据就输出静音，
    而且格式必然和被拼接的音频一致 —— 即使上游哪天换了码率也不会错位。
    """
    if ms <= 0:
        return b""
    payload = strip_container(reference)
    first = _parse_header(payload, 0)
    if not first:
        raise AudioFormatError("参考音频里找不到合法的 MPEG 帧")

    frame = payload[:4] + bytes(first.length - 4)
    count = max(1, round(ms / first.duration_ms))
    return frame * count


def stitch(clips: list[bytes]) -> tuple[bytes, list[float]]:
    """按顺序拼接片段，返回音频和每个片段的起始时间（毫秒）。"""
    out = bytearray()
    starts: list[float] = []
    elapsed = 0.0
    for clip in clips:
        payload = strip_container(clip)
        starts.append(elapsed)
        out += payload
        elapsed += sum(frame.duration_ms for frame in frames(payload))
    return bytes(out), starts
