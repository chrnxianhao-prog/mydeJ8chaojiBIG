---
name: listening-test
description: 给浩哥出西班牙语听力测试的完整流程 —— 挑选材料、写进 听力材料/ 文件夹、校验不泄题、用 Piper 离线合成音频、包成可点播的网页发布给他、听后出理解题、批改落库。学生说「听力测试」「听力」「出份听力」「练听力」「听写」「comprensión auditiva」，或任何要练听、要音频材料、要考听懂没听懂的时候，都用这个 skill。哪怕他只说「来段西语音频」或「今天练耳朵」也要用。不要自己临时发明流程，这里的每一步都是踩过坑定下来的。
---

# 出西班牙语听力测试

## 先理解这个流程为什么长这样

**你可以自己生成音频**（2026-09-15 起）。用 `--provider piper`：模型下到本地自己推理，
不联网合成，所以不受出网限制。学生确认过音质够用。

在线合成的路仍然是死的 —— Edge TTS / gTTS 都返回 403（出口是机房 IP），
HuggingFace 直接不可达。**能走通是因为模型放在 sherpa-onnx 的 GitHub release 上，而 GitHub 是通的。**

成品**不要用 SendUserFile 发 mp3**，学生明确说过"不能在线听有点烦恼"。
包成网页发布成 Artifact，他点链接就能播，不用下载也不用跑命令。

espeak-ng 老方案已废弃 —— 那是规则合成的机械音，学生 2026-09-12 反馈"根本听不懂"。
Piper 是神经网络模型，跟 Edge TTS 同一类技术，只是模型小些。

音色是 `es_MX-claude-high`（墨西哥口音，22 kHz），用 sherpa-onnx 推理。
2026-09-17 之前用的是 `es-carlfm-x-low`，学生反馈"读错的太多了"——
最低档模型念孤立单词尤其吃力，已经换掉，别再退回去。

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
python3 -m profe --provider piper lesson 听力材料/YYYY-MM-DD-主题.txt \
    -o <scratchpad>/主题.mp3 --no-cache
```

第一次跑会下约 65 MB 的模型到 `.piper-cache/`（已在 .gitignore 里），
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
- **退回 x-low 音色** —— 学生已经明确否掉过，`es_MX-claude-high` 是他点头认可的。
- **把 mp3 提交进仓库** —— 音频是可再生成的产物，只提交课文 txt。
- **用 SendUserFile 发 mp3** —— 学生要的是点开即播，发文件卡片他得先下载。
