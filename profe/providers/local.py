"""离线合成：拉美口音用 Kokoro 女声 dora，西班牙口音用 Piper davefx。

存在的理由是云端容器连不上任何在线语音服务（Edge TTS / gTTS / Google 都是 403，
出口被判定为机房 IP）。模型下到本地自己推理，不需要联网合成。
模型从 sherpa-onnx 的 GitHub release 取 —— HuggingFace 在容器里被出网策略拒绝。

音色选型（2026-09-25）：之前一直用 Piper es_MX-claude-high，学生反馈
llevar / barato / las telas 念得不对，要「专业的西班牙语语音，分拉美口音和西班牙口音」。
七个开源西语模型跑了 whisper 识别测试（.claude/skills/listening-test/scripts/voice_judge.py）：
Kokoro 两种读法都 20/20、davefx 19/20、原来的 claude 18/20（siga 被听成 sida）。
入围的做成 A/B 页，学生自己听着选了下面这两个。

Kokoro 的 lang 参数真的会改发音：es-419 把 c/z 念成 s（拉美），es 念成咬舌音（西班牙）。
这里拉美用 Kokoro + es-419；西班牙口音学生选的是 davefx，不是 Kokoro 的 es 读法。
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

CACHE_DIR = Path(".piper-cache")
MODEL_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/{dir}.tar.bz2"
MP3_BITRATE = 56

MODELOS = {
    "latam": {"dir": "kokoro-multi-lang-v1_0", "tipo": "kokoro", "marca": "model.onnx",
              "lang": "es-419", "sid": 28},   # sid 28 = ef_dora
    "espana": {"dir": "vits-piper-es_ES-davefx-medium", "tipo": "vits",
               "marca": "es_ES-davefx-medium.onnx", "sid": 0},
}

# 渲染是多线程并发的，首次运行时几个线程会同时来下模型、建引擎。
# 不加锁的话它们会往同一个临时文件写，第一个改完名，其余的就找不到文件。
_INIT_LOCK = threading.Lock()
_MOTORES: dict[tuple[str, str], object] = {}


def acento_de(voice: str) -> str:
    """课文里写的是 Edge 的音色名（es-MX-JorgeNeural 之类）。西班牙的走 davefx，其余都走拉美。"""
    v = voice.strip().lower().replace("_", "-")
    if v.startswith("es-es") or v in ("espana", "españa", "davefx"):
        return "espana"
    return "latam"


def rate_to_speed(rate: str) -> float:
    """把 profe 的百分比语速换算成 sherpa-onnx 的 speed 系数。

    profe 用 "-35%" 表示慢 35%；sherpa 的 speed 是倍率，小于 1 更慢，
    所以直接就是 1 + 百分比。
    """
    match = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)%", rate.strip())
    if not match:
        return 1.0
    return max(0.3, min(3.0, 1 + float(match.group(1)) / 100))


def _download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    # 临时文件带上进程号，两个进程同时下载也不会互相踩
    tmp = target.with_suffix(f".{os.getpid()}.part")
    with urllib.request.urlopen(url, timeout=900) as response, tmp.open("wb") as out:
        shutil.copyfileobj(response, out)
    tmp.replace(target)


def ensure_model(acento: str, cache_dir: Path = CACHE_DIR) -> Path:
    """确保模型就位，返回模型目录。容器是一次性的，每个新会话要重下（Kokoro 约 330 MB）。"""
    m = MODELOS[acento]
    home = cache_dir / m["dir"]
    if not (home / m["marca"]).exists():
        archive = cache_dir / f"{m['dir']}.tar.bz2"
        if not archive.exists():
            _download(MODEL_URL.format(dir=m["dir"]), archive)
        with tarfile.open(archive) as tar:
            tar.extractall(cache_dir)
        archive.unlink(missing_ok=True)
    if not (home / m["marca"]).exists():
        raise SynthesisError(f"模型准备失败，检查 {cache_dir}/ 下的内容")
    return home


def motor(acento: str, cache_dir: Path = CACHE_DIR):
    """返回 (sherpa_onnx.OfflineTts, sid)。同一进程里每种口音只建一次引擎。"""
    clave = (acento, str(cache_dir))
    with _INIT_LOCK:
        if clave not in _MOTORES:
            try:
                import sherpa_onnx
            except ImportError as error:
                raise SynthesisError(
                    f"当前这个 Python 没装 sherpa-onnx：\n"
                    f"   {sys.executable}\n"
                    f"   装到同一个解释器里：python -m pip install sherpa-onnx numpy lameenc"
                ) from error
            m = MODELOS[acento]
            d = ensure_model(acento, cache_dir)
            if m["tipo"] == "kokoro":
                modelo = sherpa_onnx.OfflineTtsModelConfig(
                    kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                        model=str(d / "model.onnx"), voices=str(d / "voices.bin"),
                        tokens=str(d / "tokens.txt"), data_dir=str(d / "espeak-ng-data"),
                        dict_dir=str(d / "dict"),
                        lexicon=f"{d}/lexicon-us-en.txt,{d}/lexicon-zh.txt",
                        lang=m["lang"]),
                    num_threads=4)
            else:
                modelo = sherpa_onnx.OfflineTtsModelConfig(
                    vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                        model=str(d / m["marca"]), tokens=str(d / "tokens.txt"),
                        data_dir=str(d / "espeak-ng-data")),
                    num_threads=4)
            _MOTORES[clave] = sherpa_onnx.OfflineTts(
                sherpa_onnx.OfflineTtsConfig(model=modelo, max_num_sentences=1))
        return _MOTORES[clave], MODELOS[acento]["sid"]


def a_mp3(samples, sample_rate: int, bitrate: int = MP3_BITRATE) -> bytes:
    """profe 的拼接是按 MPEG 帧做的，WAV 进不了那条流水线，所以一律转 MP3。"""
    import lameenc
    import numpy as np

    pcm = (np.array(samples) * 32767).astype("<i2").tobytes()
    encoder = lameenc.Encoder()
    encoder.set_bit_rate(bitrate)
    encoder.set_in_sample_rate(sample_rate)
    encoder.set_channels(1)
    encoder.set_quality(2)
    return encoder.encode(pcm) + encoder.flush()


class LocalProvider:
    name = "local"

    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir

    async def synthesize(self, text: str, voice: str, rate: str = "+0%") -> bytes:
        acento = acento_de(voice)
        speed = rate_to_speed(rate)

        def run() -> bytes:
            tts, sid = motor(acento, self.cache_dir)
            out = tts.generate(text, sid=sid, speed=speed)
            if not len(out.samples):
                raise SynthesisError(f"合成返回空音频：{text[:30]!r}")
            return a_mp3(out.samples, out.sample_rate)

        return await asyncio.to_thread(run)

    async def list_voices(self, prefix: str = "") -> list[dict]:
        return [
            {"ShortName": "es-MX（Kokoro dora）", "Gender": "Female", "Locale": "es-419"},
            {"ShortName": "es-ES（Piper davefx）", "Gender": "Male", "Locale": "es-ES"},
        ]
