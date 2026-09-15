import pytest

from profe.providers.piper import rate_to_length_scale


@pytest.mark.parametrize(
    "rate, expected",
    [("+0%", 1.0), ("-50%", 2.0), ("-35%", 1.538), ("+20%", 0.833)],
)
def test_percent_rate_becomes_a_length_scale(rate, expected):
    # profe 用「慢 35%」描述语速，Piper 用音素时长系数，方向相反
    assert rate_to_length_scale(rate) == pytest.approx(expected, abs=0.001)


def test_slower_rate_means_longer_audio():
    assert rate_to_length_scale("-35%") > rate_to_length_scale("+0%")


@pytest.mark.parametrize("junk", ["", "乱写", "35", "fast"])
def test_unparsable_rate_falls_back_to_normal_speed(junk):
    # 语速解析不出来就按正常速念，不该让整份材料渲染失败
    assert rate_to_length_scale(junk) == 1.0


def test_extreme_slowdown_is_clamped():
    # -99% 数学上是 100 倍时长，钳到 10 倍：再慢就不是语音了，且渲染会拖很久
    assert rate_to_length_scale("-99%") == pytest.approx(10.0)
    assert rate_to_length_scale("+500%") > 0
