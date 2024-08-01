"""A module to load and process Neware battery cycler data."""


import polars as pl

from pyprobe.cyclers.basecycler import BaseCycler


class Neware(BaseCycler):
    """A class to load and process Neware battery cycler data.

    Args:
        input_data_path: The path to the input data.
    """

    input_data_path: str
    common_suffix: str = ""
    column_name_pattern: str = r"(.+)\((.+)\)"
    column_dict: dict[str, str] = {
        "Date": "Date",
        "Step": "Step Index",
        "Current": "Current",
        "Voltage": "Voltage",
        "Charge Capacity": "Chg. Cap.",
        "Discharge Capacity": "DChg. Cap.",
    }

    @property
    def time(self) -> pl.Expr:
        """Identify and format the time column.

        Returns:
            pl.Expr: A polars expression for the time column.
        """
        return (
            (
                pl.col(self.column_dict["Date"])
                .diff()
                .dt.total_microseconds()
                .cum_sum()
                / 1e6
            )
            .fill_null(strategy="zero")
            .alias("Time [s]")
        )
