"""Test the Units class."""
import polars as pl
import polars.testing as pl_testing
import pytest

from pyprobe.units import Units


@pytest.fixture
def current_quantity():
    """Return a Units instance for current."""
    return Units("Current [A]")


@pytest.fixture
def capacity_quantity():
    """Return a Units instance for capacity."""
    return Units("Capacity [mAh]")


@pytest.fixture
def time_quantity():
    """Return a Units instance for time."""
    return Units("Time [hr]")


@pytest.fixture
def current_from_cycler_quantity():
    """Return a Units instance for current from a cycler."""
    pattern = r"(\w+)/(\w+)"
    return Units("Current/A", pattern)


@pytest.fixture
def I_from_cycler_quantity():
    """Return a Units instance for I from a cycler."""
    pattern = r"(\w+)/(\w+)"
    return Units("I/mA", pattern)


def test_get_quantity_and_unit():
    """Test the get_quantity_and_unit method."""
    name = "Capacity [Ah]"
    quantity, unit = Units.get_quantity_and_unit(name)
    assert quantity == "Capacity"
    assert unit == "Ah"

    name = "Two names [Ah]"
    quantity, unit = Units.get_quantity_and_unit(name)
    assert quantity == "Two names"
    assert unit == "Ah"

    name = "Step"
    pattern = r"(\w+)\s*\[(\w+)\]"
    with pytest.raises(ValueError):
        quantity, unit = Units.get_quantity_and_unit(name)

    name = "Current/mA"
    pattern = r"(\w+)/(\w+)"
    quantity, unit = Units.get_quantity_and_unit(name, pattern)
    assert quantity == "Current"
    assert unit == "mA"


def test_init(
    current_quantity,
    capacity_quantity,
    time_quantity,
    current_from_cycler_quantity,
    I_from_cycler_quantity,
):
    """Test the __init__ method."""
    assert current_quantity.name == "Current [A]"
    assert current_quantity.default_quantity == "Current"
    assert current_quantity.default_unit == "A"
    assert current_quantity.prefix is None

    assert capacity_quantity.name == "Capacity [mAh]"
    assert capacity_quantity.default_unit == "Ah"
    assert capacity_quantity.prefix == "m"

    assert time_quantity.name == "Time [hr]"
    assert time_quantity.default_quantity == "Time"
    assert time_quantity.default_unit == "s"
    assert time_quantity.prefix is None

    assert current_from_cycler_quantity.name == "Current/A"
    assert current_from_cycler_quantity.default_quantity == "Current"
    assert current_from_cycler_quantity.default_unit == "A"
    assert current_from_cycler_quantity.prefix is None

    assert I_from_cycler_quantity.name == "I/mA"
    assert I_from_cycler_quantity.default_quantity == "Current"
    assert I_from_cycler_quantity.default_unit == "A"
    assert I_from_cycler_quantity.prefix == "m"

    with pytest.raises(ValueError):
        Units("Step")
    with pytest.raises(ValueError):
        Units("Current/A")


def test_from_default_unit(current_quantity, capacity_quantity, time_quantity):
    """Test the from_default_unit method."""
    instruction = current_quantity.from_default_unit()
    original_frame = pl.DataFrame({"Current [A]": [1.0, 2.0, 3.0]})
    updated_frame = original_frame.with_columns(instruction)
    assert "Current [A]" in updated_frame.columns
    pl_testing.assert_series_equal(
        updated_frame["Current [A]"], original_frame["Current [A]"]
    )

    instruction = capacity_quantity.from_default_unit()
    original_frame = pl.DataFrame({"Capacity [Ah]": [1.0, 2.0, 3.0]})
    updated_frame = original_frame.with_columns(instruction)
    assert "Capacity [mAh]" in updated_frame.columns
    pl_testing.assert_series_equal(
        updated_frame["Capacity [mAh]"],
        original_frame["Capacity [Ah]"] / 1e-3,
        check_names=False,
    )

    instruction = time_quantity.from_default_unit()
    print(time_quantity.default_quantity)
    print(time_quantity.factor)
    original_frame = pl.DataFrame({"Time [s]": [1.0, 2.0, 3.0]})
    updated_frame = original_frame.with_columns(instruction)
    assert "Time [hr]" in updated_frame.columns
    pl_testing.assert_series_equal(
        updated_frame["Time [hr]"], original_frame["Time [s]"] / 3600, check_names=False
    )


def test_to_default_name_and_unit(I_from_cycler_quantity):
    """Test the to_default_name_and_unit method."""
    original_frame = pl.DataFrame({"I/mA": [1.0, 2.0, 3.0]})
    instruction = I_from_cycler_quantity.to_default_name_and_unit()
    updated_frame = original_frame.with_columns(instruction)
    assert "Current [A]" in updated_frame.columns
    pl_testing.assert_series_equal(
        updated_frame["Current [A]"], original_frame["I/mA"] * 1e-3, check_names=False
    )


def test_to_default_unit():
    """Test the to_default_unit method."""
    original_frame = pl.DataFrame({"Chg. Cap.(Ah)": [1.0, 2.0, 3.0]})
    instruction = Units("Chg. Cap.(Ah)", r"(.+)\((.+)\)").to_default_unit()
    updated_frame = original_frame.with_columns(instruction)
    assert "Chg. Cap. [Ah]" in updated_frame.columns
    pl_testing.assert_series_equal(
        updated_frame["Chg. Cap. [Ah]"],
        original_frame["Chg. Cap.(Ah)"],
        check_names=False,
    )