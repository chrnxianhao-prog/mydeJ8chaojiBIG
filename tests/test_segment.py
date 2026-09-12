from profe.segment import CJK, LATIN, dominant_script, segment


def test_pure_spanish_stays_one_piece():
    assert segment("¿Cómo estás?") == [(LATIN, "¿Cómo estás?")]


def test_accents_and_enye_are_latin_not_unknown():
    assert segment("El niño cumplió años") == [(LATIN, "El niño cumplió años")]


def test_splits_chinese_and_spanish():
    assert segment("Buenos días 就是早上好") == [
        (LATIN, "Buenos días "),
        (CJK, "就是早上好"),
    ]


def test_splits_back_and_forth():
    assert [script for script, _ in segment("我叫 Ana，她叫 Sofía")] == [
        CJK,
        LATIN,
        CJK,
        LATIN,
    ]


def test_chinese_punctuation_stays_with_chinese():
    pieces = segment("你好，buenos días")
    assert pieces[0] == (CJK, "你好，")


def test_leading_punctuation_joins_the_first_piece():
    assert segment("——Hola") == [(LATIN, "——Hola")]


def test_digits_follow_the_surrounding_language():
    assert segment("Tengo 25 años") == [(LATIN, "Tengo 25 años")]
    assert segment("我有 25 岁") == [(CJK, "我有 25 岁")]


def test_digits_alone_still_get_spoken():
    assert segment("2024") == [(LATIN, "2024")]


def test_blank_input_produces_nothing():
    assert segment("   ") == []
    assert segment("") == []


def test_dominant_script_picks_the_majority():
    assert dominant_script("Buenos días 早") == LATIN
    assert dominant_script("这一整句基本都是中文 hola") == CJK
    assert dominant_script("四个汉字 hola") == LATIN  # 数量相同时按拉丁处理
