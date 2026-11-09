# 语音版每日练习 · Voz diaria

> 分支 `claude/spanish-voice-practice`：把原来只在 Claude 里跑的文字版教学，
> 变成每天一条语音课。老师还是「小云」，学生还是浩哥（A2，目标 1 年内到 B2）。

## 每天发什么

每天一条，固定放在 `lecciones/diaria-YYYY-MM-DD.txt`（课文）+ 同名 `.mp3`（音频），
同时发到聊天里。内容沿用仓库已有的规则：

- **场景一律用仓库**（收货卸货、盘点、货架、叉车、少货坏货、跟司机/供应商/同事说话），
  不出收银台、卖衣服。
- **难度 A2**，紧扣当前最优先的问题：三时态混淆（pretérito / imperfecto /
  condicional）> doler/gustar 主语 > 间接宾语 le/me/te > 错题库老词。
- **每课 10 句**，分 3–4 个小节，每句带中文释义。

## 音频节奏（profe 原有格式，不改）

```
西语（正常语速） → 停 0.5 秒 → 西语（慢速 -35%） → 跟读时间 → 中文释义 → 停 0.9 秒
```

慢速那一遍是重点：正常语速下连读成一坨的句子，慢速才听得出重音落在哪。
跟读时间按慢速那一遍的实际时长算，刚好够跟着念一遍。

## 合成方式

用仓库自己的 `profe` 工具生成，离线版（`--provider local`）：

```bash
python -m profe --provider local lesson lecciones/diaria-YYYY-MM-DD.txt
```

- 西语默认走拉美口音（Kokoro dora，课文写 `voice=es-MX-JorgeNeural`），
  慢速那一遍 -50%，句间停顿 1500 毫秒。西班牙口音（Piper davefx）只在课文
  写 `voice=es-ES-…` 时用。
- 中文释义走 Kokoro 中文发音。
- Edge 在线版（`--provider edge`）在云端容器里连不上微软端点，别用。

⚠️ 写课文的铁律（2026-11-08 踩坑）：小节标题（`#` 开头的行）会被西语音色
念出来，标题里**一个中文都不能有**，中文说明一律写在 `//` 批注里。
第一版标题里混了中文，西语音色硬念中文，整段都糊了，学生完全听不懂。

## 学生怎么练

1. 先盲听：听到西语想意思，不要先看字。
2. 跟读：慢速那一遍之后留出的时间，跟着念一遍。
3. 再听中文释义对答案。
4. 练完在聊天里说一声，老师把进度写进 `spanish-coach-state.json` 并提交，
   提交信息格式：`学习记录: YYYY-MM-DD <本次内容简述>`。

## 文件

| 文件 | 作用 |
|------|------|
| `lecciones/diaria-YYYY-MM-DD.txt` | 当天课文（profe 格式：`西语 = 中文释义`） |
| `lecciones/diaria-YYYY-MM-DD.mp3` | 当天音频，导进手机通勤路上听 |
| `VOZ-DIARIA.md` | 本文件：语音版每日练习的约定 |
