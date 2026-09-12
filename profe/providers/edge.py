"""Edge TTS 引擎：走微软 Edge 浏览器"大声朗读"背后的在线服务。

免费、不需要 API Key，音质是微软的神经网络音色。
输出固定为 audio-24khz-48kbitrate-mono-mp3（恒定码率），audio 模块的帧拼接依赖这一点。
"""

from __future__ import annotations

import asyncio

from . import SynthesisError

_MAX_ATTEMPTS = 3
_BACKOFF_SECONDS = (1, 3)


def _diagnose(error: Exception) -> str:
    text = str(error)
    if "403" in text:
        return (
            "微软拒绝了这次连接（403）。绝大多数情况是出口 IP 被判定为机房 IP —— "
            "云服务器、部分公司网络和某些 VPN 会中招。换成家庭宽带直连通常就好了。"
        )
    if "CERTIFICATE_VERIFY_FAILED" in text or "SSLError" in text:
        return (
            "TLS 证书校验失败。如果你在有 HTTPS 抓包代理的网络里，"
            "把代理的 CA 证书加进 certifi 的信任库，不要关掉证书校验。"
        )
    if "Cannot connect" in text or "TimeoutError" in text or isinstance(error, asyncio.TimeoutError):
        return "连不上微软的语音端点，检查网络或代理设置。"
    return text


class EdgeProvider:
    name = "edge"

    async def synthesize(self, text: str, voice: str, rate: str = "+0%") -> bytes:
        import edge_tts

        last: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                communicate = edge_tts.Communicate(text, voice, rate=rate)
                chunks = [
                    chunk["data"]
                    async for chunk in communicate.stream()
                    if chunk["type"] == "audio"
                ]
                if not chunks:
                    raise SynthesisError("服务端没有返回音频")
                return b"".join(chunks)
            except Exception as error:  # 网络类异常五花八门，统一重试后再归类
                last = error
                if attempt < _MAX_ATTEMPTS - 1:
                    await asyncio.sleep(_BACKOFF_SECONDS[attempt])

        raise SynthesisError(f"合成失败（{voice}）：{_diagnose(last)}") from last

    async def list_voices(self, prefix: str = "") -> list[dict]:
        import edge_tts

        try:
            voices = await edge_tts.list_voices()
        except Exception as error:
            raise SynthesisError(f"拉取音色列表失败：{_diagnose(error)}") from error
        return [voice for voice in voices if voice["ShortName"].startswith(prefix)]
