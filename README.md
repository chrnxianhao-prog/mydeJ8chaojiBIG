# profe

西班牙语听说练习音频生成器。写一份纯文本课文，生成一条可以反复听的 mp3。

用微软 Edge 浏览器"大声朗读"背后的在线语音服务（edge-tts）：**免费、不需要 API Key、不需要注册**。

## 装

```bash
pip install -r requirements.txt
```

只有一个依赖。先确认环境没问题：

```bash
python -m profe doctor
```

## 用

写一份课文（`lecciones/leccion-01.txt` 是现成的例子）：

```
# Lección 1 — Saludos
// 以 // 开头的是批注，不会被念出来
Hola. = 你好。
¿Cómo estás? = 你好吗？
Hasta luego.
```

生成音频：

```bash
python -m profe lesson lecciones/leccion-01.txt
```

得到 `lecciones/leccion-01.mp3`，导进手机就能通勤路上听。

## 每句话的节奏

```
西语（正常语速）  →  停 0.5 秒  →  西语（慢速 -35%）  →  跟读时间  →  中文释义  →  停 0.9 秒
```

**慢速那一遍是重点。** 正常语速下 `¿Cómo estás?` 是连读成一坨的，慢速才听得出 s 有没有咬住、重音落在哪个音节。

**跟读时间是按慢速那一遍的实际时长算的**，不是固定值：句子长停得久，句子短停得短，刚好够你跟着念一遍。

## 常用参数

```bash
# 换成墨西哥口音的男声
python -m profe lesson 课文.txt --voice es-MX-JorgeNeural

# 简写也行：es-MX 会自动解析成该地区的音色
python -m profe lesson 课文.txt --voice es-MX

# 去掉中文释义，做纯西语沉浸材料
python -m profe lesson 课文.txt --no-gloss

# 去掉慢速复读，当听力材料用
python -m profe lesson 课文.txt --no-slow

# 句间停顿拉长到 2 秒，留足反应时间
python -m profe lesson 课文.txt --gap 2000

# 单句试听
python -m profe say "¿Dónde está la estación?" -o test.mp3

# 看有哪些音色
python -m profe voices          # 教学常用的
python -m profe voices --all --prefix es-   # 微软的全部西语音色
```

## 选口音

西班牙的 `c/z` 发 θ（think 的 th），拉美发 s —— 这是两套发音习惯。**一开始就选定一个，中途换会把耳朵搞乱。**

| 音色 | 口音 |
|---|---|
| `es-ES-ElviraNeural` / `es-ES-AlvaroNeural` | 西班牙（默认） |
| `es-MX-DaliaNeural` / `es-MX-JorgeNeural` | 墨西哥 |
| `es-AR-ElenaNeural` | 阿根廷 |
| `es-CO-SalomeNeural` | 哥伦比亚 |

## 几个设计上的取舍

**中西混排自动分段配音色。** 一个音色念不了两种语言：中文音色念 "buenos días" 会糊成一团，西语音色念中文直接出乱音。所以 `你好 = hola 就是你好` 这种释义会被自动切成两段，各配各的音色。这是整个工具里最关键的一件事。

**不依赖 ffmpeg。** Edge TTS 输出的是固定格式的恒定码率 MPEG 音频，所以片段直接按帧拼接，静音用片段自己的帧头配全零负载合成 —— 装个 Python 就能跑，不用配环境。

**改一行课文不会重新合成整课。** 按 `音色 + 语速 + 文字` 的内容哈希缓存在 `.profe-cache/`，只有变动的句子会重新请求。

## 已知问题

**`doctor` 报 403** —— 微软拒绝了连接。基本都是出口 IP 被判定为机房 IP：**云服务器、部分公司网络、某些 VPN 都会中招**。换家庭宽带直连通常就好了。这不是代码问题，换网络即可。

**TLS 证书校验失败** —— 你的网络里有 HTTPS 抓包代理。把代理的 CA 证书加进 certifi 的信任库，不要关掉证书校验。

## 后面要做的

`--timeline` 会额外输出一个 json，记录每一段语音在成品里的起止时间、角色和音色：

```bash
python -m profe lesson 课文.txt --timeline
```

这是给**视频配音**留的接口 —— 有了时间轴才能对轨和生成字幕。等主要目标跑顺了再接。

换更适合配音的合成引擎也已经留好位置：`profe/providers/` 下加一个实现 `synthesize()` 的文件即可，上层编排和拼接都不用动。

## 测试

```bash
python -m pytest tests/ -q
```

测试用假的合成引擎跑完整条流水线，不联网。
