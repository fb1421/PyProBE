"""A module for the RawData class."""
import logging
from typing import Dict, List, Optional

import polars as pl
import pybamm
from pydantic import Field, field_validator

from pyprobe.result import Result

logger = logging.getLogger(__name__)

required_columns = [
    "Time [s]",
    "Step",
    "Event",
    "Current [A]",
    "Voltage [V]",
    "Capacity [Ah]",
]

default_column_definitions = {
    "Date": "The timestamp of the data point. Type: datetime.",
    "Time [s]": "The time passed from the start of the procedure.",
    "Step": "The step number.",
    "Cycle": "The cycle number.",
    "Event": "The event number. Counts the changes in cycles and steps.",
    "Current [A]": "The current through the cell.",
    "Voltage [V]": "The terminal voltage.",
    "Capacity [Ah]": "The net charge passed since the start of the procedure.",
    "Temperature [C]": "The temperature of the cell.",
}


class RawData(Result):
    """A class for holding data in the PyProBE format.

    This is the default object returned when data is loaded into PyProBE with the
    standard methods of the `pyprobe.cell.Cell` class. It is a subclass of the
    `pyprobe.result.Result` class so can be used in the same way as other result
    objects.

    The RawData object is stricter than the `pyprobe.result.Result` object in that it
    requires the presence of specific columns in the data. These columns are:
        - `Time [s]`
        - `Step`
        - `Cycle`
        - `Event`
        - `Current [A]`
        - `Voltage [V]`
        - `Capacity [Ah]`

    This defines the PyProBE format.
    """

    column_definitions: Dict[str, str] = Field(
        default_factory=lambda: default_column_definitions.copy()
    )
    step_descriptions: Dict[str, List[Optional[str | int]]] = {}
    """A dictionary containing the fields 'Step' and 'Description'.

    - 'Step' is a list of step numbers.
    - 'Description' is a list of corresponding descriptions in PyBaMM Experiment format.
    """

    @field_validator("base_dataframe")
    @classmethod
    def check_required_columns(
        cls, dataframe: pl.LazyFrame | pl.DataFrame
    ) -> "RawData":
        """Check if the required columns are present in the input_data."""
        column_list = dataframe.collect_schema().names()
        missing_columns = [col for col in required_columns if col not in column_list]
        if missing_columns:
            error_msg = f"Missing required columns: {missing_columns}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        return dataframe

    def zero_column(
        self,
        column: str,
        new_column_name: str,
        new_column_definition: Optional[str] = None,
    ) -> None:
        """Set the first value of a column to zero.

        Args:
            column (str): The column to zero.
            new_column_name (str): The new column name.
            new_column_definition (Optional[str]): The new column definition.

        Returns:
            pl.DataFrame | pl.LazyFrame: The dataframe or lazyframe with the new column.
        """
        self.base_dataframe = self.base_dataframe.with_columns(
            (pl.col(column) - pl.col(column).first()).alias(new_column_name)
        )
        if new_column_definition is not None:
            self.define_column(new_column_name, new_column_definition)

    @property
    def capacity(self) -> float:
        """Calculate the net capacity passed.

        Returns:
            float: The net capacity passed.
        """
        return abs(self.data["Capacity [Ah]"].max() - self.data["Capacity [Ah]"].min())

    def set_SOC(
        self,
        reference_capacity: Optional[float] = None,
        reference_charge: Optional["RawData"] = None,
    ) -> None:
        """Add an SOC column to the data.

        Apply this method on a filtered data object to add an `SOC` column to the data.
        This column remains with the data if the object is filtered further.


        The SOC column is calculated either relative to a provided reference capacity
        value, a reference charge (provided as a RawData object), or the maximum
        capacity delta across the data in the RawData object upon which this method
        is called.

        Args:
            reference_capacity (Optional[float]): The reference capacity value.
            reference_charge (Optional[RawData]):
                A RawData object containing a charge to use as a reference.
        """
        if reference_capacity is None:
            reference_capacity = (
                pl.col("Capacity [Ah]").max() - pl.col("Capacity [Ah]").min()
            )
        if reference_charge is None:
            self.base_dataframe = self.base_dataframe.with_columns(
                (
                    (
                        pl.col("Capacity [Ah]")
                        - pl.col("Capacity [Ah]").max()
                        + reference_capacity
                    )
                    / reference_capacity
                ).alias("SOC")
            )
        else:
            if self.contains_lazyframe:
                reference_charge_data = reference_charge.base_dataframe.select(
                    "Time [s]", "Capacity [Ah]"
                )
                self.base_dataframe = self.base_dataframe.join(
                    reference_charge_data, on="Time [s]", how="left"
                )
                self.base_dataframe = self.base_dataframe.with_columns(
                    pl.col("Capacity [Ah]_right")
                    .max()
                    .alias("Full charge reference capacity"),
                ).drop("Capacity [Ah]_right")
            else:
                full_charge_reference_capacity = (
                    reference_charge.data.select("Capacity [Ah]").max().item()
                )
                self.base_dataframe = self.base_dataframe.with_columns(
                    pl.lit(full_charge_reference_capacity).alias(
                        "Full charge reference capacity"
                    ),
                )

            self.base_dataframe = self.base_dataframe.with_columns(
                (
                    (
                        pl.col("Capacity [Ah]")
                        - pl.col("Full charge reference capacity")
                        + reference_capacity
                    )
                    / reference_capacity
                ).alias("SOC")
            )
        self.define_column("SOC", "The full cell State-of-Charge.")

    def set_reference_capacity(
        self, reference_capacity: Optional[float] = None
    ) -> None:
        """Fix the capacity to a reference value.

        Apply this method on a filtered data object to fix the capacity to a reference.
        This calculates a permanent column named `Capacity - Referenced [Ah]` in the
        data, which remains if this object is filtered further.

        The reference value is either the maximum capacity delta across the data in the
        RawData object upon which this method is called or a user-specified value.

        Args:
            reference_capacity (Optional[float]): The reference capacity value.
        """
        if reference_capacity is None:
            reference_capacity = (
                pl.col("Capacity [Ah]").max() - pl.col("Capacity [Ah]").min()
            )
        self.base_dataframe = self.base_dataframe.with_columns(
            (
                pl.col("Capacity [Ah]")
                - pl.col("Capacity [Ah]").max()
                + reference_capacity
            ).alias("Capacity - Referenced [Ah]")
        )

    @property
    def pybamm_experiment(self) -> pybamm.Experiment:
        """Return a PyBaMM experiment object for the filtered section of data.

        Returns:
            pybamm.Experiment: The PyBaMM experiment object.
        """
        step_description_df = pl.LazyFrame(self.step_descriptions)
        no_step_descriptions = step_description_df.filter(
            pl.col("Description").is_null()
        )
        missing_steps = (
            no_step_descriptions.select("Step").collect().to_numpy().flatten()
        )
        if len(missing_steps) > 0:
            error_msg = (
                f"Descriptions for steps {str(missing_steps)} are missing."
                f" Unable to create a PyBaMM experiment object. Please "
                f"filter the data to a section with descriptions for all "
                f"steps to create an experiment."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # reduce the full dataframe to only the steps as they appear in order in
        # the data
        only_steps = self.base_dataframe.filter(
            pl.col("Step") != pl.col("Step").shift(1)
        ).select("Step")
        # match the step with its description
        all_steps_with_descriptions = only_steps.join(
            step_description_df, on="Step", how="left"
        )
        if isinstance(all_steps_with_descriptions, pl.LazyFrame):
            all_steps_with_descriptions = all_steps_with_descriptions.select(
                "Description"
            ).collect()
        # form a list of all the descriptions
        all_steps_with_descriptions = all_steps_with_descriptions.to_numpy().flatten()
        description_list = []
        for description in all_steps_with_descriptions:
            line = description.split(",")
            for item in line:
                description_list.append(item.strip())
        return pybamm.Experiment(description_list)
