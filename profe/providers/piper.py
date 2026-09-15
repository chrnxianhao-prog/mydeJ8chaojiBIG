"""Piper 引擎：完全离线的本地神经网络合成。

存在的理由是云端容器连不上任何在线语音服务（Edge TTS / gTTS 都是 403，
出口被判定为机房 IP）。Piper 把模型下到本地自己推理，不需要联网合成，
所以老师端也能直接出音频，不必让学生在自己电脑上跑一遍。

模型走 GitHub release 下载 —— HuggingFace 在容器里被出网策略拒绝，
而 GitHub 的 release 资源是通的。
"""

from __future__ import annotations

import asyncio
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import wave
from pathlib import Path

from . import SynthesisError

CACHE_DIR = Path(".piper-cache")
ENGINE_URL = "https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_amd64.tar.gz"
VOICE_URL = "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-es-carlfm-x-low.tar.gz"
DEFAULT_VOICE = "es-carlfm-x-low"

# 默认参数下同一句话跑三次时长能差 50%，还会在词尾补一段重复的杂音。
# 压低这两个噪声量后波动降到 ±3%，教学材料必须可复现，所以固定住。
STABLE_ARGS = ("--noise_scale", "0.2", "--noise_w", "0.2")

MP3_BITRATE = 48


def _download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".part")
    with urllib.request.urlopen(url, timeout=300) as response, tmp.open("wb") as out:
        shutil.copyfileobj(response, out)
    tmp.rename(target)


def ensure_assets(cache_dir: Path = CACHE_DIR) -> tuple[Path, Path]:
    """确保引擎和音色就位，返回 (piper 可执行文件, 模型文件)。

    容器是一次性的，每个新会话都要重下约 50 MB。这一步做成幂等的，
    已经下过就直接复用。
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    binary = cache_dir / "piper" / "piper"
    model = cache_dir / f"{DEFAULT_VOICE}.onnx"

    if not binary.exists():
        archive = cache_dir / "engine.tar.gz"
        if not archive.exists():
            _download(ENGINE_URL, archive)
        with tarfile.open(archive) as tar:
            tar.extractall(cache_dir)
        binary.chmod(0o755)

    if not model.exists():
        archive = cache_dir / "voice.tar.gz"
        if not archive.exists():
            _download(VOICE_URL, archive)
        with tarfile.open(archive) as tar:
            tar.extractall(cache_dir)

    if not binary.exists() or not model.exists():
        raise SynthesisError(f"Piper 资源准备失败，检查 {cache_dir}/ 下的内容")
    return binary, model


def rate_to_length_scale(rate: str) -> float:
    """把 profe 的百分比语速换算成 Piper 的音素时长系数。

    profe 用 "-35%" 表示慢 35%，Piper 用大于 1 的系数表示拉长。
    """
    match = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)%", rate.strip())
    if not match:
        return 1.0
    factor = 1 + float(match.group(1)) / 100
    if factor <= 0.1:
        factor = 0.1
    return round(1 / factor, 3)


def _encode_mp3(wav_path: Path) -> bytes:
    """转成 MP3 —— profe 的拼接是按 MPEG 帧做的，WAV 进不了那条流水线。"""
    try:
        import lameenc
    except ImportError as error:
        raise SynthesisError(
            f"当前这个 Python 没装 lameenc（Piper 输出 WAV，要转成 MP3 才能拼接）：\n"
            f"   {sys.executable}\n"
            f"   装到同一个解释器里：python -m pip install lameenc"
        ) from error

    with wave.open(str(wav_path)) as source:
        rate, channels = source.getframerate(), source.getnchannels()
        pcm = source.readframes(source.getnframes())

    encoder = lameenc.Encoder()
    encoder.set_bit_rate(MP3_BITRATE)
    encoder.set_in_sample_rate(rate)
    encoder.set_channels(channels)
    encoder.set_quality(2)
    return encoder.encode(pcm) + encoder.flush()


class PiperProvider:
    name = "piper"

    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir
        self._assets: tuple[Path, Path] | None = None

    def _ready(self) -> tuple[Path, Path]:
        if self._assets is None:
            self._assets = ensure_assets(self.cache_dir)
        return self._assets

    async def synthesize(self, text: str, voice: str, rate: str = "+0%") -> bytes:
        # 课文里写的多半是 Edge 的音色名（es-MX-JorgeNeural 之类）。
        # Piper 这边只有一个可用的西语音色，认不出来就用它，不必让渲染失败。
        binary, model = await asyncio.to_thread(self._ready)
        length_scale = rate_to_length_scale(rate)
        output = self.cache_dir / f"out-{abs(hash((text, rate))):x}.wav"

        def run() -> bytes:
            try:
                subprocess.run(
                    [str(binary), "--model", str(model), *STABLE_ARGS,
                     "--length_scale", str(length_scale), "--output_file", str(output)],
                    input=text.encode(), capture_output=True, check=True, timeout=120,
                )
                return _encode_mp3(output)
            finally:
                output.unlink(missing_ok=True)

        try:
            return await asyncio.to_thread(run)
        except subprocess.CalledProcessError as error:
            detail = error.stderr.decode(errors="replace").strip().splitlines()
            raise SynthesisError(f"Piper 合成失败：{detail[-1] if detail else error}") from error

    async def list_voices(self, prefix: str = "") -> list[dict]:
        return [{"ShortName": DEFAULT_VOICE, "Gender": "Male", "Locale": "es-ES"}]
