import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# MPEG-2 Layer III / 24 kHz / 48 kbps / 单声道 —— Edge TTS 固定输出的格式。
FRAME_HEADER = bytes([0xFF, 0xF3, 0x64, 0xC0])
FRAME_BYTES = 144
FRAME_MS = 24.0


def mp3(frame_count: int) -> bytes:
    """造一段该格式的合法 MPEG 音频，用来替代真实合成结果。"""
    return (FRAME_HEADER + bytes(FRAME_BYTES - len(FRAME_HEADER))) * frame_count
