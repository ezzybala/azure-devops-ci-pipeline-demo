import pytest

from app.calculator import add, subtract


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [(5, 2, 7), (-5, 2, -3), (0, 0, 0)],
)
def test_add(left, right, expected):
    assert add(left, right) == expected


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [(5, 2, 3), (2, 5, -3), (-5, -2, -3)],
)
def test_subtract(left, right, expected):
    assert subtract(left, right) == expected
