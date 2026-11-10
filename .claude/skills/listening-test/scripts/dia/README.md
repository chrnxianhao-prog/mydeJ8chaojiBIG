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
| `ejemplo_d1103.py` | 当天内容 `C` 的写法范例（TRES 每行第 4 项是 whisper 要听出来的关键词；RAPIDO = 口语快答（中文, 西语, 关键词）） |
| `pagina.py` | `armar(...)`：拿 `assets/daily-page-dalia.template.html` 换当天文字、嵌音频和 Dalia 原文，出 `dMMDD.html` |
| `ejemplo_d1103_page.py` | `armar` 的调用范例 |
| `prueba_pagina.py dMMDD` | 发布前真点一遍：盲听/认词/自写卡/选中可见/全对 20/全错 0 + 听写 MP3 浏览器解码回测 |
| `retoma.py dMMDD g0_0="新句子"` | 只重做个别练习句（句末 cajas 被念糊时用） |
| `refija.py dMMDD llamé` | 听写词 MP3 解码后回测不过时，重挑一条解码后也对的，再跑 `_page.py` |

发完把当天的 `dMMDD.template.html` 覆盖回 `assets/daily-page-dalia.template.html`，下次在它上面改。

## 踩过的坑（2026-11-02）

- **Kokoro 每次合成略有不同**：同一句同一速度，这次 anaquel、下次 anaquil。`toma()` 默认每个速度试两轮。
- **whisper 会拆词也会连词**：pedía → pedí a；me trajo → metrajo。`toma()` 认「连续几个词拼起来正好等于目标」，
  比子串匹配严，不会把 pedía 当成 pedí。
- **ll / y 同音**（拉美）：llamé 偶尔写成 yamé，比较时 ll 当 y。
- **句末名词容易糊**：caja → queja、playo → playa。后面再跟一两个词（…cajas aquí / …playo, por favor）。
- **数字连读**：pedí cien → pedici en。换个不以元音/c 开头粘连的数（treinta）。
- **¿Qué…? 的重音 whisper 不写**（问句也写成 que）：练习句的关键词别放 qué，放后面的词。
- **whisper 把 conté 写成字母 con T**：`fichas()` 把 `con t` 换回 conté。anoté 解码后总被拆成 a noté / anote，换词（revisé）。
- 换了听写词以后**再查一遍短文有没有泄题**（11-10 换成 revisé，短文里正好有 revisé）。
