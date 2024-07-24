"""A module for the Result class."""
import warnings
from pprint import pprint
from typing import Dict, List, Optional

import numpy as np
import polars as pl
from numpy.typing import NDArray

from pyprobe.unitconverter import UnitConverter


class Result:
    """A result object for returning data and plotting.

    Attributes:
        _data (pl.LazyFrame | pl.DataFrame): The data as a polars DataFrame or
            LazyFrame.
        data (Optional[pl.DataFrame]): The data as a polars DataFrame.
        info (Dict[str, str | int | float]): A dictionary containing test info.
    """

    def __init__(
        self,
        _data: pl.LazyFrame | pl.DataFrame,
        info: Dict[str, str | int | float],
        column_definitions: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize the Result object.

        Args:
            _data (pl.LazyFrame | pl.DataFrame): The filtered _data.
            info (Dict[str, str | int | float]): A dict containing test info.
            column_definitions(Optional[Dict[str, str]]):
                A dict containing the definitions of the columns in _data.
        """
        self._data = _data
        self.info = info
        if column_definitions is None:
            self.column_definitions: Dict[str, str] = {}
        else:
            self.column_definitions = column_definitions

    def __call__(self, column_name: str) -> NDArray[np.float64]:
        """Return columns of the data as numpy arrays.

        Args:
            column_name (str): The column names to return.

        Returns:
            Union[NDArray[np.float64]:
                The column as a numpy array.
        Deprecated:
            This method will be removed in a future version. Use `array` instead.
        """
        warnings.warn(
            "The __call__ method is deprecated and will be removed in a future version."
            "Use `array` instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        self.check_units(column_name)
        if column_name not in self.data.columns:
            raise ValueError(f"Column '{column_name}' not in data.")
        else:
            return self.data[column_name].to_numpy()

    def __getitem__(self, *column_name: str) -> "Result":
        """Return a new result object with the specified columns.

        Args:
            *column_name (str): The columns to include in the new result object.

        Returns:
            Result: A new result object with the specified columns.
        """
        column_names = list(column_name)
        for col in column_names:
            self.check_units(col)
        if not all(col in self.data.columns for col in column_names):
            raise ValueError("One or more columns not in data.")
        else:
            return Result(self.data.select(column_names), self.info)

    def get(self, column_name: str) -> NDArray[np.float64]:
        """Return a column of the data as a numpy array.

        Args:
            column_name (str): The column name to return.

        Returns:
            NDArray[np.float64]: The column as a numpy array.
        """
        self.check_units(column_name)
        if column_name not in self.data.columns:
            raise ValueError(f"Column '{column_name}' not in data.")
        else:
            return self.data[column_name].to_numpy()

    def array(self, *filtering_column_names: str) -> NDArray[np.float64]:
        """Return the data as a numpy array.

        Args:
            *filtering_column_names (str): The column names to return.

        Returns:
            NDArray[np.float64]: The data as a numpy array.
        """
        print("filtering_column_names", filtering_column_names)
        if len(filtering_column_names) == 0:
            return self.data.to_numpy()
        else:
            column_names = list(filtering_column_names)
            for col in column_names:
                self.check_units(col)
            if not all(col in self.data.columns for col in column_names):
                raise ValueError("One or more columns not in data.")
            else:
                data_to_convert = self.data.select(column_names)
                return data_to_convert.to_numpy()

    @property
    def data(self) -> pl.DataFrame:
        """Return the data as a polars DataFrame.

        Returns:
            pl.DataFrame: The data as a polars DataFrame.
        """
        if isinstance(self._data, pl.LazyFrame):
            self._data = self._data.collect()
        return self._data

    def print(self) -> None:
        """Print the data."""
        print(self.data)

    def check_units(self, column_name: str) -> None:
        """Check if a column exists and convert the units if it does not.

        Args:
            column_name (str): The column name to convert to.
        """
        if column_name not in self.data.columns:
            instruction = UnitConverter(column_name).from_default()
            self._data = self.data.with_columns(instruction)

    @property
    def column_list(self) -> List[str]:
        """Return a list of the columns in the data."""
        return self.data.columns

    def define_column(self, column_name: str, definition: str) -> None:
        """Define a new column when it is added to the dataframe.

        Args:
            column_name (str): The name of the column.
            definition (str): The definition of the quantity stored in the column
        """
        self.column_definitions[column_name] = definition

    def print_definitions(self) -> None:
        """Print the definitions of the columns stored in this result object."""
        pprint(self.column_definitions)

    def clean_copy(
        self,
        data: Optional[Dict[str, NDArray[np.float64]]] = {},
        column_definitions: Optional[Dict[str, str]] = None,
    ) -> "Result":
        """Create a copy of the result object with info dictionary but without data.

        Args:
            data (Optional[Dict[str, NDArray[np.float64]]):
                The data to include in the new result object.
            column_definitions (Optional[Dict[str, str]]):
                The definitions of the columns in the new result object.

        Returns:
            Result: A new result object with the specified data.
        """
        return Result(pl.DataFrame(data), self.info, column_definitions)

    @classmethod
    def build(
        cls,
        data_list: List[
            pl.LazyFrame
            | pl.DataFrame
            | Dict[str, NDArray[np.float64] | List[float]]
            | List[
                pl.LazyFrame
                | pl.DataFrame
                | Dict[str, NDArray[np.float64] | List[float]]
            ]
        ],
        info: Dict[str, str | int | float],
    ) -> "Result":
        """Build a Result object from a list of dataframes.

        Args:
            data_list (List[List[pl.LazyFrame | pl.DataFrame | Dict]]):
                The data to include in the new result object.
                The first index indicates the cycle and the second index indicates the
                step.
            info (Dict[str, str | int | float]): A dict containing test info.

        Returns:
            Result: A new result object with the specified data.
        """
        cycles_and_steps_given = all(isinstance(item, list) for item in data_list)
        if not cycles_and_steps_given:
            data_list = [data_list]
        data = []
        for cycle, cycle_data in enumerate(data_list):
            for step, step_data in enumerate(cycle_data):
                if isinstance(step_data, dict):
                    step_data = pl.DataFrame(step_data)
                step_data = step_data.with_columns(
                    pl.lit(cycle).alias("Cycle"), pl.lit(step).alias("Step")
                )
                data.append(step_data)
        data = pl.concat(data)
        return cls(data, info)
