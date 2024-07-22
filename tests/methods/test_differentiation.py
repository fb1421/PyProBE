"""Tests for the differentiation module."""

import numpy as np

import pyprobe.methods.differentiation as diff


def test_differentiate_LEAN():
    """Test the LEAN differentiation method."""
    x_min = 0
    x_max = 1
    num_points = 10000
    x = np.linspace(x_min, x_max, num_points)

    average_gradient = 2
    n = 200

    total_range = x_max * average_gradient
    levels = np.linspace(0, total_range, n)

    points_per_level = num_points // n
    remainder = num_points % n

    y = np.repeat(levels, points_per_level)
    if remainder > 0:
        y = np.append(y, levels[:remainder])

    x_pts, _, dxdy = diff._calc_gradient_with_LEAN(x, y, 1, "dxdy")
    assert np.isclose(np.median(dxdy), 1 / average_gradient, rtol=0.1)
    x_pts, _, dydx = diff._calc_gradient_with_LEAN(x, y, 1, "dydx")
    assert np.isclose(np.median(dydx), average_gradient, rtol=0.1)


def test_x_sections():
    """Test the LEAN get_x_sections method."""
    x = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20, 20.5, 21, 21.5, 22, 22.5, 23]
    x_sections = diff._get_x_sections(x)
    x_sliced = [x[s] for s in x_sections]
    assert x_sliced == [
        [0, 1, 2, 3, 4, 5, 6],
        [6, 8, 10, 12, 14, 16, 18, 20],
        [20, 20.5, 21, 21.5, 22, 22.5, 23],
    ]