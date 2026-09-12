import pytest

from profe.lesson import LessonError, Pause, Speak, Style, build_plan, parse

SOURCE = """
# Lección 1 — Saludos
// 这行是批注，不该出现在音频里
¿Cómo estás? = 你好吗？
Buenos días.  =  早上好。
Hasta luego.
"""


def test_parses_title_items_and_ignores_comments():
    lesson = parse(SOURCE)
    assert lesson.title == "Lección 1 — Saludos"
    assert [item.target for item in lesson.items] == [
        "¿Cómo estás?",
        "Buenos días.",
        "Hasta luego.",
    ]
    assert lesson.items[0].gloss == "你好吗？"
    assert lesson.items[2].gloss is None


def test_keeps_line_numbers_for_error_messages():
    assert parse(SOURCE).items[0].line_no == 4


def test_rejects_a_line_with_only_a_gloss():
    with pytest.raises(LessonError):
        parse("= 只有释义")


def test_rejects_an_empty_lesson():
    with pytest.raises(LessonError):
        parse("# 只有标题\n// 和批注")


def test_section_headers_are_attached_to_their_position():
    lesson = parse("# 开场\nUno = 一\n# 第二节\nDos = 二")
    assert lesson.headers == {0: ["开场"], 1: ["第二节"]}


def test_title_and_first_section_header_both_survive():
    lesson = parse("# Lección 1\n# Saludos\nHola = 你好")
    assert lesson.title == "Lección 1"
    assert lesson.headers == {0: ["Lección 1", "Saludos"]}
    spoken = [step.text for step in build_plan(lesson, Style()) if isinstance(step, Speak)]
    assert spoken[:2] == ["Lección 1", "Saludos"]


def _roles(plan):
    return [step.role for step in plan if isinstance(step, Speak)]


def test_plan_follows_the_teaching_rhythm():
    lesson = parse("Hola = 你好")
    plan = build_plan(lesson, Style())
    assert _roles(plan) == ["normal", "slow", "gloss"]


def test_slow_pass_uses_the_slow_rate_and_the_same_voice():
    plan = build_plan(parse("Hola = 你好"), Style(slow_rate="-40%"))
    normal, slow = [step for step in plan if isinstance(step, Speak)][:2]
    assert (normal.rate, slow.rate) == ("+0%", "-40%")
    assert normal.voice == slow.voice


def test_shadow_pause_mirrors_the_slow_clip():
    plan = build_plan(parse("Hola = 你好"), Style())
    mirrored = [step for step in plan if isinstance(step, Pause) and step.mirror]
    assert len(mirrored) == 1
    assert mirrored[0].mirror == 1.0


def test_switches_off_slow_and_gloss():
    plan = build_plan(parse("Hola = 你好"), Style(slow=False, gloss_enabled=False))
    assert _roles(plan) == ["normal"]
    assert not [step for step in plan if isinstance(step, Pause) and step.mirror]


def test_gloss_uses_the_gloss_voice_and_target_uses_the_target_voice():
    style = Style(target_voice="es-MX-JorgeNeural", gloss_voice="zh-CN-YunxiNeural")
    plan = build_plan(parse("Hola = 你好"), style)
    spoken = [step for step in plan if isinstance(step, Speak)]
    assert spoken[0].voice == "es-MX-JorgeNeural"
    assert spoken[-1].voice == "zh-CN-YunxiNeural"


def test_mixed_language_gloss_splits_across_two_voices():
    style = Style(target_voice="es-ES-ElviraNeural", gloss_voice="zh-CN-XiaoxiaoNeural")
    plan = build_plan(parse("Hola = hola 就是你好"), style)
    gloss = [step for step in plan if isinstance(step, Speak) and step.role == "gloss"]
    assert [step.voice for step in gloss] == [
        "es-ES-ElviraNeural",
        "zh-CN-XiaoxiaoNeural",
    ]
