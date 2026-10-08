---
name: listening-test
description: 给浩哥出西班牙语听力测试的完整流程 —— 挑选材料、写进 听力材料/ 文件夹、校验不泄题、用 Piper 离线合成音频、包成可点播的网页发布给他、听后出理解题、批改落库。学生说「听力测试」「听力」「出份听力」「练听力」「听写」「comprensión auditiva」，或任何要练听、要音频材料、要考听懂没听懂的时候，都用这个 skill。哪怕他只说「来段西语音频」或「今天练耳朵」也要用。不要自己临时发明流程，这里的每一步都是踩过坑定下来的。
---

# 出西班牙语听力测试

## 先理解这个流程为什么长这样

**你可以自己生成音频**（2026-09-15 起）。用 `--provider local`（旧名 `piper` 也还能用）：模型下到本地自己推理，
不联网合成，所以不受出网限制。学生确认过音质够用。

在线合成的路仍然是死的 —— Edge TTS / gTTS 都返回 403（出口是机房 IP），
HuggingFace 直接不可达。**能走通是因为模型放在 sherpa-onnx 的 GitHub release 上，而 GitHub 是通的。**

成品**不要用 SendUserFile 发 mp3**，学生明确说过"不能在线听有点烦恼"。
包成网页发布成 Artifact，他点链接就能播，不用下载也不用跑命令。

espeak-ng 老方案已废弃 —— 那是规则合成的机械音，学生 2026-09-12 反馈"根本听不懂"。
Piper 是神经网络模型，跟 Edge TTS 同一类技术，只是模型小些。

**音色（2026-09-25 学生选定）**：
- 拉美口音（默认）：**Kokoro 女声 dora**，`lang=es-419`，24 kHz
- 西班牙口音：**Piper davefx**，22 kHz。课文 `voice=es-ES-*` 就走这个

换过两次了：`es-carlfm-x-low`（9-17 学生说「读错的太多了」）→ `es_MX-claude-high`
（9-25 学生说 llevar / barato / las telas 还是不对）→ 现在这两个。
第二次换之前跑了识别测试（`scripts/voice_judge.py`，七个模型 × 十句易错句交给 whisper-small）：
Kokoro 两种读法 20/20、davefx 19/20、claude 18/20。但学生报的那三个词 whisper 听 claude 也全对 ——
**他的耳朵比识别模型细，分数只做初筛，最后让他听 A/B 自己选**。别退回旧音色。

🔴 **b/v 在西语里同音，whisper 比对时把 v 当 b**（2026-10-01 起出题脚本 `toma()` 和回测都这样比，vendí 听成 bendí 算对）。以前的做法是：**词用 b/v 开头或夹 b/v 的，听写别选**：2026-10-01 vendo 被 whisper 听成 bendo（西语 b/v 同音，
学生也只能靠拼写记忆），换成 abro/mandé 等。另外逐词挑的录音要**编成 MP3 并拼出「念两遍」之后**再用浏览器解码回测，
单条合成时听对不代表发布版听对（10-01 又见：comí 单独念总被听成 con mi，换成 comió）（10-01 llego、terminé、abrí 都是这样掉出来的），回测不过就换速度/换词。
老词复习别再用「只听只翻」：9-26 起六个老词三次共 0/18，10-01 改成「中文 + 首字母 + 字数」主动回忆，
练习区有「对一下 / 提示」，错两次才给答案（`assets/daily-page-dalia.template.html` 里的 viejas 卡）。

🔴 **模板第一行必须是 `<meta charset="utf-8">`**：2026-10-07 容器重置后，Playwright 用 file:// 打开没声明编码的页面，中文和重音字母全成乱码，「全对」只判到 11/20。发布版有外壳不受影响，但本地测试会假报错。

🟢 **Dalia（es-MX-DaliaNeural）走浏览器，不走容器。** 2026-09-30 学生说他 3D 动画项目的配音好听，
那是 Edge「大声朗读」的 Dalia（msedge-tts 调 wss://speech.platform.bing.com/…/edge/v1）。
学生在环境设置里放行了 speech.platform.bing.com，HTTPS 通了（200），但**合成走的是 WebSocket，
代理不支持 WebSocket 升级**（握手 403），容器里合成不了 —— 别再绕。
做法：页面顶部放「声音」开关（`assets/daily-page-dalia.template.html`），电脑上用 Edge 打开时
`speechSynthesis.getVoices()` 里有 Dalia，就用 Web Speech 现场念；手机和别的浏览器没有 Dalia，
自动回落到页面里嵌的 Kokoro 录音。模板要多填一个 `__TEXTOS__`（每个录音 key 对应的原文，
`_dos` 念两遍）。注意：Dalia 这条路**没法事先用 whisper 验**，学生报哪个词念得怪再记下来。
2026-09-30 学生在 Edge 里听了对比，定下**Dalia 为默认、Kokoro 备用**。模板里有 Dalia 就自动选中，学生点过 Kokoro 才记住 Kokoro。

🔴 **单个词一律用 `profe.voz.hablar_palabra(palabra)`，别直接喂给 `hablar()`。**
Kokoro 是拿整句训练的，孤立单词开头会多出一个杂音。2026-09-26 学生听写把 habló 写成 sabor
（原话「这个 hablo 怎么读成 sablo」）。whisper 回测：孤立单词 16 个只认对 6 个
（habló→sablo、hermano→ser mano、hijo→dijo、llevar→Y éste —— 9-25 他报的 llevar 多半也是这个原因）；
放进 `Digo ___, otra vez.` 里念，当天页面 33 个词全认对。词放句尾也会糊（La palabra es: habló → Ableu），
`Escribe ___` 会跟元音开头的词连读（escribe habló → a Blu），所以固定用 `Digo ___, otra vez.`。
页面上要告诉学生「只写中间那个词」。

🔴 **别把 Kokoro 放慢到 0.9 以下，重音会掉。** 2026-09-28 回测：speed 0.7/0.8 时 pagó→pago、cambió→cambio
（尾音节重音被拉平），9-26 页面「慢」按钮念的就是错重音 —— 学生那几天老漏写重音，很可能跟这个有关。
做法：每个词在 0.9 上下挑一条 whisper 认对的（逐词回测，认错就换速度或换词），
「慢」按钮改成「念两遍」＝同一条验证过的片段拼两次、中间 500ms 静音（`profe.audio.stitch` + `silence_like`）。
逐词挑的那条，编成 MP3 后要再用浏览器解码回测一遍：2026-09-30 llevó 生成时 whisper 听对，MP3 解码后却成了 llevo，重挑一条才过。
听写重音词时判分要严：`q.tilde` 为真的题漏重音算错，并提示「你写的 … 是另一个词」。

发布前可以用浏览器把页面里的 mp3 解码成 PCM 交给 whisper 回测（`AudioContext.decodeAudioData`，
容器里没有 ffmpeg），测的就是学生实际听到的那份音频。

出题脚本（每日页那种）合成单句一律用 `profe.voz.hablar(texto, speed, acento)`，
别再各自抄一份引擎配置 —— 9-25 以前每个脚本都自己写了一遍，换音色时得一个个改。

## 步骤

### 1. 先读学生当前状态

`spanish-coach-state.json` 拿 `wrong_answer_bank`（错题库）和 `difficulty_modifier`，
`CLAUDE.md` 的「当前最优先攻克的问题」拿薄弱点。**听力材料要打这些点**，
不要随便编个无关场景——每一份材料都是一次针对性训练的机会，浪费了可惜。

### 2. 设计材料

**选题三原则：**

- **打薄弱点**：把他最混的语法做成听力里必须分辨的信息。比如三时态混淆，
  就写一段叙事——用 imperfecto 铺背景、pretérito 推事件、condicional 收假设，
  理解题故意问"他以前怎么样 / 那天发生了什么"，听不出时态层次就答不对。
- **复现错题库老词**：把 `wrong_answer_bank` 里躺着的词自然编进句子。
  听懂比看懂更能把词钉进长期记忆。
- **贴近他的真实语境**：他做生意、住墨西哥城。买东西、看病、面试、租房、
  跟供应商谈——这类场景他将来真会用到，比课本例句记得牢。

**长度**：A2 阶段 12-16 句，约 1 分半。再长他会走神，理解题也不好设计。

### 3. 写文件

路径 `听力材料/YYYY-MM-DD-主题.txt`（主题用西语小写连字符，如 `la-entrevista`）。

```
#! listening voice=es-MX-JorgeNeural gap=1800
# Comprensión auditiva — La entrevista de trabajo

// ── 给老师的批注（不会被念出来）──
// 考点设计：……
// 理解题（⚠️ 学生听完再发）：
//   1. 他去年在哪里工作？为什么想换工作？
//      答：在市中心的餐厅；喜欢但赚得太少
//   ……

El año pasado yo trabajaba en un restaurante en el centro.
Me gustaba el trabajo, pero ganaba muy poco dinero.
……
```

要点：

- **第一行必须有 `#! listening`**，理由见下方红线。
- **理解题和答案写在 `//` 批注里**，不写进聊天记录。聊天里提前发题，
  学生会先看题再听，测出来的是找答案能力不是听力。
- **听力材料不写 `= 中文`**。listening 模式下写了也不念，但别写，容易误导后来的人。
- 换音色：`voice=es-MX-JorgeNeural`（可写 `es-MX`、`jorge` 简写）。
  **注意 piper 只有一个可用西语音色**（`es_MX-claude-high`），写了别的名字它会忽略并用它，不会报错。
  音色字段现在只在学生本机用 Edge 渲染时才起作用，先照写，将来换引擎不用改材料。
- `gap=` 是句间停顿毫秒数，初期给 1800-2000 留反应时间。

### 4. 跑校验（这一步不能跳）

```bash
python .claude/skills/listening-test/scripts/check_listening.py 听力材料/YYYY-MM-DD-主题.txt
```

退出码 0 才能提交。它会真的把编排跑出来，检查有没有中文会被念出去、
模式对不对，并报出句数、音色和预估时长。

### 5. 渲染音频

```bash
python3 -m profe --provider local lesson 听力材料/YYYY-MM-DD-主题.txt \
    -o <scratchpad>/主题.mp3 --no-cache
```

第一次跑会下模型到 `.piper-cache/`（已在 .gitignore 里；Kokoro 约 330 MB，davefx 约 64 MB，用到哪个下哪个），
之后同会话内复用。容器是一次性的，每个新会话都要重下一次，属正常。
需要 `sherpa-onnx numpy lameenc`，容器里没有就先 `python3 -m pip install` 上。

mp3 放 scratchpad，**不要提交进仓库** —— 音频是可以从课文重新生成的产物。

### 6. 包成网页并发布

```bash
python3 .claude/skills/listening-test/scripts/build_page.py \
    <scratchpad>/主题.mp3 "La entrevista de trabajo" --date "15 sep 2026" \
    -o <scratchpad>/主题.html
```

然后用 **Artifact 工具发布这个 html**，把链接发给学生。页面自带播放器、进度条和重听按钮，
音频内嵌成 data URI，手机电脑点开即播。

页面上**没有原文也没有题目**，这是刻意的。

### 7. 提交材料文件

提交信息用仓库惯例：`学习记录: YYYY-MM-DD 听力测试(主题·考点)`。
推到 `claude/spanish-teacher-assistant-sk7p2f` 分支。只提交 `听力材料/*.txt`。

### 8. 等他听完，再发理解题

3-5 题，**用中文提问**——只测听懂没听懂，别夹带西语产出难度，
否则分不清是没听懂还是不会写。

### 9. 批改并落库

按 `教师制度.md` 的批改规则。然后更新 `spanish-coach-state.json`：
听错的词回 `wrong_answer_bank`，时态层次答错记进 `common_errors`，
更新 `last_task_date` / `streak`，commit。

注意「测试可靠性规则」：同日重复测试不推进连对计数。

## 🔴 红线：材料绝不能念出中文

profe 默认是**跟读教学**节奏：正常语速 → 慢速复读 → **中文释义**。
中文释义会被朗读——**用在听力测试上等于在音频里直接报答案，整套题当场作废。**

`#! listening` 关掉释义和慢速。模式名写错（如 `listenning`）会直接报错而不是静默忽略，
但**光靠肉眼看文件看不出编排结果**，所以第 4 步的校验脚本必须跑。

## 🔴 红线：做出来的页面，学生点了必须看得见

2026-09-22 学生原话：「我点了一个单词但是没有什么变化，颜色变化也要框选让我能看到啊，
**不能只有你知道**」。他说得对，而且这是同一天里第二次栽在「代码看着对，用起来是死的」。

### 三条硬规矩

1. **任何可点的东西，选中状态必须肉眼可见**：填色 + 描边 + 一个 ✓，三样一起上。
   只改 `aria-pressed` 属性不算数 —— 那是给读屏软件看的，不是给人看的。

2. **选中样式只挂 `aria-pressed`，别跟 `data-v` 的具体取值绑死。**
   ```css
   ✅ .opts button[aria-pressed="true"] { ... }
   ❌ .opts button[aria-pressed="true"][data-v="yo"] { ... }
   ```
   下面那种写法，换一套选项（`data-v` 从 `yo`/`usted` 换成动词原形）就整个失效，
   而且**不报任何错**，页面看着完好，点了没反应。这正是 9-22 翻车的原因。

3. **`window.claude.use()` 必须包 try/catch，交卷的绑定写在它前面。**
   `window.claude` 拿不到时 `.use` 是**同步抛错**，`.catch()` 接不住；
   一抛脚本就断在那行，后面的按钮全没绑上。

### 发布前必须用浏览器真跑一遍

容器里 Chromium 是现成的，**别跑 `playwright install`**：

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="/opt/pw-browsers/chromium")
```

**验「看得见」，不是验「状态对了」。** 我 9-22 第一次测只查了 `aria-pressed` 变成
`true`，通过了，可学生那边点下去毫无动静 —— 因为样式压根没匹配上。

至少跑这四项：

| 验什么 | 怎么验 |
|--------|--------|
| 点击有视觉反馈 | 比对点击前后的 `getComputedStyle`，**至少 2 个属性变化**（底色/边框/字色/字重） |
| 明暗两套皮都对 | `new_page(color_scheme="light")` 和 `"dark"` 各跑一遍 |
| 判分方向没反 | 全填正确答案该满分、全填错该零分，**两个方向都跑** |
| 没有 JS 报错 | 挂 `page.on("pageerror", ...)`，有错就是有雷 |

最后**截一张图自己看一眼**（`locator.screenshot()` 然后用 Read 工具读）。
computed style 对了不等于人看着清楚，眼睛过一遍最保险。

⚠️ **读样式前要把 CSS 过渡动画排掉，否则会读到动画中间值，判出假故障。**
按钮上有 `transition: .15s`，2026-09-22 只等 120ms 就读，
结果同一个页面在 dark/390px 报「悬停盖掉选中态」，逐属性重测其实完全一致 ——
是我的检查在抖，不是页面有毛病。两个办法，一起用最稳：

```python
p = b.new_page(color_scheme=tema, reduced_motion="reduce")   # 直接关掉过渡
...
opt.click(); p.wait_for_timeout(350)                          # 再留足余量
```

**自己的检查报错时，先怀疑检查本身，逐属性打出来对一遍再下结论。**

⚠️ **滚动状态也要截一张。** 只截刚打开的第一屏看不出吸顶元素的问题。
2026-09-23 标签条原来是浮在 `top:12px` 的药丸，滚动时正文从它上方的缝和两侧露出来、
又被药丸本体盖住一截，正好把「tú 有个 t → 用 -te」那句规则压没了。
改成外面套一条整宽、页底色的 `.tabs-bar` 去 sticky，药丸本身不 sticky。
检查办法：`page.mouse.wheel(0, 某节的 y - 30)` 滚到一个区块刚好经过顶部时截图。
拿着假故障去改代码，等于把好的改坏。

## 难度调节

跟着 `difficulty_modifier` 走：

- **偏低**：短句、高频词、`gap=2000`、单人叙述。
- **中等**（当前 28 一档）：12-16 句叙事或双人对话，时态混用，`gap=1800`。
- **偏高**：整段对话不给停顿提示、换不熟悉的口音（`es-AR` / `es-CO`）测口音适应力、
  加入数字和时间等易漏细节。

## 常见翻车点

- **忘了 `#! listening`** —— 最致命，音频直接报答案。校验脚本就是防这个。
- **题目跟链接一起发** —— 学生先看题再听，测不出真实水平。必须等他听完再发。
- **材料超过 20 句** —— 他会走神，且理解题覆盖不过来。
- **理解题掺西语作答要求** —— 混淆了听力和产出两种能力，分不清错在哪。
- **改用在线 TTS** —— Edge TTS / gTTS 在容器里都是 403，别再试。离线的 piper 才是通路。
- **退回旧音色** —— x-low 和 claude-high 学生都明确否掉过，Kokoro dora / davefx 是他 A/B 听过自己选的。
- **把 mp3 提交进仓库** —— 音频是可再生成的产物，只提交课文 txt。
- **用 SendUserFile 发 mp3** —— 学生要的是点开即播，发文件卡片他得先下载。
