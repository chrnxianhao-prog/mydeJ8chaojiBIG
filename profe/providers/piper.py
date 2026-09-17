"""离线神经网络合成：墨西哥口音的 Piper 模型，用 sherpa-onnx 跑。

存在的理由是云端容器连不上任何在线语音服务（Edge TTS / gTTS 都是 403，
出口被判定为机房 IP）。模型下到本地自己推理，不需要联网合成。

为什么不用 Piper 官方的二进制：它打包的 onnxruntime 只认到 IR 版本 8，
读不了现在这些模型。sherpa-onnx 从 PyPI 装得到，而且这些模型本来就是
它打包发布的。

为什么走 GitHub 取模型：HuggingFace 在容器里被出网策略拒绝，
而 sherpa-onnx 把模型镜像在自己的 GitHub release 上，那条路是通的。

音色选型（2026-09-17）：学生反馈原来的 es-carlfm-x-low 念错太多。
x-low 是最低档、2023 年的单人模型，孤立单词尤其吃力。换成 es_MX-claude-high：
高两个档位、22 kHz，而且是墨西哥口音 —— 学生住墨西哥城，这个口音对他更实用。
"""

from __future__ import annotations

import asyncio
import os
import re
import shutil
import sys
import tarfile
import threading
import urllib.request
from pathlib import Path

from . import SynthesisError

# 渲染是多线程并发的，首次运行时几个线程会同时来下模型、建引擎。
# 不加锁的话它们会往同一个临时文件写，第一个改完名，其余的就找不到文件。
_INIT_LOCK = threading.Lock()

CACHE_DIR = Path(".piper-cache")
VOICE = "vits-piper-es_MX-claude-high"
MODEL_URL = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/{VOICE}.tar.bz2"
MP3_BITRATE = 56


def _download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    # 临时文件带上进程号，两个进程同时下载也不会互相踩
    tmp = target.with_suffix(f".{os.getpid()}.part")
    with urllib.request.urlopen(url, timeout=600) as response, tmp.open("wb") as out:
        shutil.copyfileobj(response, out)
    tmp.replace(target)


def ensure_model(cache_dir: Path = CACHE_DIR) -> Path:
    """确保模型就位，返回模型目录。容器是一次性的，每个新会话要重下约 65 MB。"""
    cache_dir.mkdir(parents=True, exist_ok=True)
    home = cache_dir / VOICE
    if not (home / "es_MX-claude-high.onnx").exists():
        archive = cache_dir / f"{VOICE}.tar.bz2"
        if not archive.exists():
            _download(MODEL_URL, archive)
        with tarfile.open(archive) as tar:
            tar.extractall(cache_dir)
    if not (home / "es_MX-claude-high.onnx").exists():
        raise SynthesisError(f"模型准备失败，检查 {cache_dir}/ 下的内容")
    return home


def rate_to_speed(rate: str) -> float:
    """把 profe 的百分比语速换算成 sherpa-onnx 的 speed 系数。

    profe 用 "-35%" 表示慢 35%；sherpa 的 speed 是倍率，小于 1 更慢，
    所以直接就是 1 + 百分比。
    """
    match = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)%", rate.strip())
    if not match:
        return 1.0
    return max(0.3, min(3.0, 1 + float(match.group(1)) / 100))


class PiperProvider:
    name = "piper"

    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir
        self._tts = None

    def _engine(self):
        if self._tts is not None:
            return self._tts
        with _INIT_LOCK:
            if self._tts is not None:   # 等锁期间别的线程已经建好了
                return self._tts
            try:
                import sherpa_onnx
            except ImportError as error:
                raise SynthesisError(
                    f"当前这个 Python 没装 sherpa-onnx：\n"
                    f"   {sys.executable}\n"
                    f"   装到同一个解释器里：python -m pip install sherpa-onnx numpy lameenc"
                ) from error

            home = ensure_model(self.cache_dir)
            self._tts = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(
                model=sherpa_onnx.OfflineTtsModelConfig(
                    vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                        model=str(home / "es_MX-claude-high.onnx"),
                        tokens=str(home / "tokens.txt"),
                        data_dir=str(home / "espeak-ng-data"),
                    ),
                    num_threads=4,
                ),
                max_num_sentences=1,
            ))
            return self._tts

    async def synthesize(self, text: str, voice: str, rate: str = "+0%") -> bytes:
        # 课文里写的多半是 Edge 的音色名（es-MX-JorgeNeural 之类）。
        # 这边只有一个音色，认不出来就用它，不必让渲染失败。
        speed = rate_to_speed(rate)

        def run() -> bytes:
            import lameenc
            import numpy as np

            out = self._engine().generate(text, sid=0, speed=speed)
            if not len(out.samples):
                raise SynthesisError(f"合成返回空音频：{text[:30]!r}")
            pcm = (np.array(out.samples) * 32767).astype("<i2").tobytes()

            # 转成 MP3 —— profe 的拼接是按 MPEG 帧做的，WAV 进不了那条流水线
            encoder = lameenc.Encoder()
            encoder.set_bit_rate(MP3_BITRATE)
            encoder.set_in_sample_rate(out.sample_rate)
            encoder.set_channels(1)
            encoder.set_quality(2)
            return encoder.encode(pcm) + encoder.flush()

        return await asyncio.to_thread(run)

    async def list_voices(self, prefix: str = "") -> list[dict]:
        return [{"ShortName": "es_MX-claude-high", "Gender": "Male", "Locale": "es-MX"}]
