# 每日页出题脚本（2026-10-29 起，容器重置后脚本全丢过一次，所以存进仓库）

**用法：整个文件夹拷进 scratchpad 再跑**（脚本按自身所在目录找 whisper 模型、写输出）。

```bash
cp .claude/skills/listening-test/scripts/dia/*.py <scratchpad>/
python3 -m pip install -q "sherpa-onnx<2" numpy lameenc playwright   # 2.0.1 的 Kokoro 坏了
# whisper-small（判官）下到 <scratchpad>/tts/sherpa-onnx-whisper-small/
#   https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.tar.bz2
#   只解出 small-encoder.int8.onnx / small-decoder.int8.onnx / small-tokens.txt
```

| 文件 | 干什么 |
|------|--------|
| `motor_dia.py` | `construir(C, "dMMDD")`：逐条合成、whisper 验过才收，写 `_audio.json` / `_data.json`，带短文泄题检查 |
| `ejemplo_d1029.py` | 当天内容 `C` 的写法范例（TRES 每行第 4 项是 whisper 要听出来的关键词） |
| `pagina.py` | `armar(...)`：拿 `assets/daily-page-dalia.template.html` 换当天文字、嵌音频和 Dalia 原文，出 `dMMDD.html` |
| `ejemplo_d1029_page.py` | `armar` 的调用范例 |
| `prueba_pagina.py dMMDD` | 发布前真点一遍：盲听/认词/自写卡/选中可见/全对 20/全错 0 + 听写 MP3 浏览器解码回测 |
| `retoma.py dMMDD g0_0="新句子"` | 只重做个别练习句（句末 cajas 被念糊时用） |

发完把当天的 `dMMDD.template.html` 覆盖回 `assets/daily-page-dalia.template.html`，下次在它上面改。
