# coding: utf-8
import pytest

from seabattle.strategy import Strategy


@pytest.fixture
def four_decker_strategy():
    g = Strategy(region_size=4)
    return g


@pytest.fixture
def three_decker_strategy():
    g = Strategy(region_size=3)
    return g


@pytest.fixture
def two_decker_strategy():
    g = Strategy(region_size=2)
    return g


def points_in_line_count(shooting_field, size):
    prev = None
    for row in shooting_field:
        counter = 0
        for point in row:
            if point == prev:
                counter += 1
            if counter == size:
                return False
        else:
            return True


def test_strategy(four_decker_strategy, three_decker_strategy, two_decker_strategy):
    assert points_in_line_count(four_decker_strategy.shooting_field, 4)
    assert points_in_line_count(three_decker_strategy.shooting_field, 3)
    assert points_in_line_count(two_decker_strategy.shooting_field, 2)
