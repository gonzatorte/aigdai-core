from ror.fairsharing_mapper import fairsharing_2_ror, ror_2_fairsharing


def test_fairsharing_2_ror():
    assert fairsharing_2_ror(6) == '05rex1605'
    assert fairsharing_2_ror(1) is None
    assert fairsharing_2_ror(1111111) is None


def test_ror_2_fairsharing():
    assert ror_2_fairsharing('05rex1605') == 6
    assert ror_2_fairsharing('cafecafec') is None
