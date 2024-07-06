"""Tests for the LEAN differentiation method."""

import numpy as np

from pyprobe.methods.differentiation.LEAN import DifferentiateLEAN


def test_differentiate():
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

    x_pts, _, dxdy = DifferentiateLEAN.gradient(x, y, 1, "dxdy")
    assert np.isclose(np.median(dxdy), 1 / average_gradient, rtol=0.1)
    x_pts, _, dydx = DifferentiateLEAN.gradient(x, y, 1, "dydx")
    assert np.isclose(np.median(dydx), average_gradient, rtol=0.1)
