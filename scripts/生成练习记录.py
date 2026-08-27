#!/usr/bin/env python3
"""从 spanish-coach-state.json 重新生成人类可读的 练习记录.md

用法：python3 scripts/生成练习记录.py
每次更新状态文件后跑一遍，保持 markdown 快照与 JSON 同步。
"""
import json
import os
from collections import defaultdict
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, 'spanish-coach-state.json')
OUT = os.path.join(ROOT, '练习记录.md')


def main():
    with open(STATE, encoding='utf-8') as f:
        s = json.load(f)

    L = []
    add = L.append
    stamp = s.get('last_assessment_date') or s.get('last_task_date', '')

    add('# 西班牙语练习记录\n')
    add(f'> 本文件由 `scripts/生成练习记录.py` 从 `spanish-coach-state.json` 自动生成，数据截至 **{stamp}**。')
    add('> 修改进度请改 JSON 再重跑脚本，不要直接编辑本文件。\n')

    # 一、概览
    add('## 一、学习进度概览\n')
    add('| 项目 | 数值 |')
    add('|------|------|')
    rows = [
        ('当前等级', s.get('level', '')),
        ('目标等级', s.get('target_level', '')),
        ('目标期限', s.get('target_deadline', '')),
        ('连续学习天数（streak）', f"{s.get('streak', 0)} 天"),
        ('累计完成天数', f"{s.get('total_completed_days', 0)} 天"),
        ('累计漏掉天数', f"{s.get('total_missed_days', 0)} 天"),
        ('难度系数', s.get('difficulty_modifier', 0)),
        ('最近一次任务日期', s.get('last_task_date', '')),
        ('最近一次测试日期', s.get('last_test_day', '')),
        ('已做测试次数', f"{s.get('tests_completed', 0)} 次"),
    ]
    for k, v in rows:
        add(f'| {k} | {v} |')
    if s.get('level_note'):
        add(f"\n> ⚠️ {s['level_note']}")

    # 当前重点
    focus = s.get('current_focus_areas') or []
    if focus:
        add('\n## 二、当前攻克重点\n')
        for i, x in enumerate(focus, 1):
            add(f'{i}. {x}')
    relearn = s.get('relearn_queue') or []
    if relearn:
        add('\n**重修队列**：' + '、'.join(relearn))

    # 词汇
    vocab = s.get('vocabulary_learned', [])
    add(f'\n## 三、已学词汇（{len(vocab)} 个）\n')
    add('```')
    L.extend(vocab)
    add('```')

    # 语法点
    gp = s.get('grammar_points_covered', [])
    add(f'\n## 四、已覆盖语法点（{len(gp)} 个）\n')
    for i, g in enumerate(gp, 1):
        add(f'{i}. {g}')

    # 近期主题
    rt = s.get('recent_topics', [])
    if rt:
        add('\n## 五、近期学习主题\n')
        for i, t in enumerate(rt, 1):
            add(f'{i}. {t}')

    # 语法错误
    ce = s.get('common_errors', [])
    add(f'\n## 六、常见语法/句型错误（{len(ce)} 条）\n')
    for e in ce:
        line = f"- {e.get('error', '')}"
        if e.get('count'):
            line += f"（错 {e['count']} 次）"
        if e.get('relearn'):
            line += ' **[需重修]**'
        if e.get('date'):
            line += f" [{e['date']}]"
        add(line)

    # 全局错词库
    bank = s.get('wrong_answer_bank', [])
    add(f'\n## 七、全局错词库（{len(bank)} 条）\n')
    add('用于每日旧词复习环节投放，连对 2 次移除。\n')
    grouped = defaultdict(list)
    for w in bank:
        grouped[w.get('module', '未分类')].append(w)
    for mod in sorted(grouped):
        items = grouped[mod]
        add(f'### {mod}（{len(items)} 个）\n')
        for w in items:
            add(f"- {w['word']} — 连对 {w.get('correct_count', 0)}/2 次，最近错于 {w.get('date_wrong', '')}")
        add('')

    # 模块错词库
    mb = s.get('module_wrong_banks', {})
    total = sum(len(v) for v in mb.values())
    add(f'## 八、模块错词库（{total} 条）\n')
    add('按模块独立追踪，刷到该模块时自动夹带，连对 3 次移除。\n')
    for mod in sorted(mb):
        items = mb[mod]
        if not items:
            continue
        add(f'### {mod}（{len(items)} 个）\n')
        for w in items:
            add(f"- {w['word']} — 错 {w.get('wrong_count', 0)} 次，"
                f"连对 {w.get('correct_count', 0)}/3 次，最近错于 {w.get('date_wrong', '')}")
        add('')

    add('---\n')
    add('规则动词现在式/简单过去式词尾、不规则动词家族分类详见 `spanish-verb-chart.md`。')
    add(f'\n<!-- generated at {datetime.now().isoformat(timespec="seconds")} -->')

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')

    print(f'✅ 已生成 {OUT}')
    print(f'   词汇 {len(vocab)} · 语法点 {len(gp)} · 语法错误 {len(ce)} · '
          f'全局错词 {len(bank)} · 模块错词 {total}')


if __name__ == '__main__':
    main()
