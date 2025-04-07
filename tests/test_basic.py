"""
Test di base per verificare che pytest funzioni correttamente.
"""


def test_basic():
    """
    Un test di base che verifica che True sia True.
    """
    assert True


def test_math():
    """
    Un test di base che verifica operazioni matematiche semplici.
    """
    assert 1 + 1 == 2
    assert 2 * 2 == 4
    assert 10 / 2 == 5
