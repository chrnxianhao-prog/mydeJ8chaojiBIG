import pytest

from profe.providers.piper import rate_to_speed


@pytest.mark.parametrize(
    "rate, expected",
    [("+0%", 1.0), ("-35%", 0.65), ("-50%", 0.5), ("+20%", 1.2)],
)
def test_percent_rate_becomes_a_speed_factor(rate, expected):
    # profe 用「慢 35%」描述语速，sherpa 用倍率，小于 1 更慢
    assert rate_to_speed(rate) == pytest.approx(expected, abs=0.001)


def test_slower_rate_means_smaller_factor():
    assert rate_to_speed("-35%") < rate_to_speed("+0%")


@pytest.mark.parametrize("junk", ["", "乱写", "35", "fast"])
def test_unparsable_rate_falls_back_to_normal_speed(junk):
    # 语速解析不出来就按正常速念，不该让整份材料渲染失败
    assert rate_to_speed(junk) == 1.0


def test_extremes_are_clamped():
    # 再慢就不是语音了；再快也没有教学意义
    assert rate_to_speed("-99%") == pytest.approx(0.3)
    assert rate_to_speed("+500%") == pytest.approx(3.0)
