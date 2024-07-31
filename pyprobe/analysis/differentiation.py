"""A module for differentiating experimental data."""

from typing import List

import numpy as np
from pydantic import BaseModel

import pyprobe.analysis.base.differentiation_functions as diff_functions
from pyprobe.analysis.utils import AnalysisValidator
from pyprobe.result import Result
from pyprobe.typing import PyProBEDataType


class Differentiation(BaseModel):
    """A class for differentiating experimental data.

    Args:
        input_data (PyProBERawDataType): The raw data to analyse.
    """

    input_data: PyProBEDataType
    required_columns: List[str] = []

    def differentiate_FD(
        self,
        x: str,
        y: str,
        gradient: str = "dydx",
    ) -> Result:
        """Differentiate smooth data with the finite difference method.

        A light wrapper of the numpy.gradient function.

        Args:
            x (str): The name of the x variable.
            y (str): The name of the y variable.
            gradient (str, optional):
                The gradient to calculate, either 'dydx' or 'dxdy'.
                Defaults to "dydx".

        Returns:
            Result:
                A result object containing the columns, `x`, `y` and the
                calculated gradient.
        """
        validator = AnalysisValidator(
            input_data=self.input_data, required_columns=[x, y]
        )
        x_data, y_data = validator.variables
        if gradient == "dydx":
            gradient_title = f"d({y})/d({x})"
            gradient_data = np.gradient(y_data, x_data)
        elif gradient == "dxdy":
            gradient_title = f"d({x})/d({y})"
            gradient_data = np.gradient(x_data, y_data)
        else:
            raise ValueError("Gradient must be either 'dydx' or 'dxdy'.")

        gradient_result = self.input_data.clean_copy(
            {x: x_data, y: y_data, gradient_title: gradient_data}
        )
        gradient_result.column_definitions = {
            x: self.input_data.column_definitions[x],
            y: self.input_data.column_definitions[y],
            gradient_title: "The calculated gradient.",
        }
        return gradient_result

    def differentiate_LEAN(
        self,
        x: str,
        y: str,
        k: int = 1,
        gradient: str = "dydx",
        smoothing_filter: List[float] = [0.0668, 0.2417, 0.3830, 0.2417, 0.0668],
        section: str = "longest",
    ) -> Result:
        r"""A method for differentiating noisy data.

        Uses 'Level Evaluation ANalysis' (LEAN) method described in the paper of
        :footcite:t:`Feng2020`.

        This method assumes :math:`x` datapoints to be evenly spaced, it can return
        either :math:`\frac{dy}{dx}` or :math:`\frac{dx}{dy}` depending on the argument
        provided to the `gradient` parameter.

        Args:
            x (str):
                The name of the x variable.
            y (str):
                The name of the y variable.
            k (int, optional):
                The integer multiple to apply to the sampling interval for the bin size
                (:math:`\delta R` in paper). Default is 1.
            gradient (str, optional):
                The gradient to calculate, either 'dydx' or 'dxdy'. Default is 'dydx'.
            smoothing_filter (List[float], optional):
                The coefficients of the smoothing matrix.

                Examples provided by :footcite:t:`Feng2020` include:
                    - [0.25, 0.5, 0.25] for a 3-point smoothing filter.
                    - [0.0668, 0.2417, 0.3830, 0.2417, 0.0668] (default) for a 5-point
                    smoothing filter.
                    - [0.1059, 0.121, 0.1745, 0.1972, 0.1745, 0.121, 0.1059] for a
                    7-point smoothing filter.
            section (str, optional):
                The section of the data with constant sample rate in x to be considered.
                Default is 'longest', which just returns the longest unifomly sampled
                section. Alternative is 'all', which returns all sections.

        Returns:
            Result:
                A result object containing the columns, `x`, `y` and the calculated
                gradient.
        """
        # validate and identify variables
        validator = AnalysisValidator(
            input_data=self.input_data, required_columns=[x, y]
        )
        x_data, y_data = validator.variables

        # split input data into uniformly sampled sections
        x_sections = diff_functions.get_x_sections(x_data)
        if section == "longest":
            x_sections = [max(x_sections, key=lambda x: x.stop - x.start)]
        x_all = np.array([])
        y_all = np.array([])
        calc_gradient_all = np.array([])

        # over each uniformly sampled section, calculate the gradient
        for i in range(len(x_sections)):
            x_data = x_data[x_sections[i]]
            y_data = y_data[x_sections[i]]
            x_pts, y_pts, calculated_gradient = diff_functions.calc_gradient_with_LEAN(
                x_data, y_data, k, gradient
            )
            x_all = np.append(x_all, x_pts)
            y_all = np.append(y_all, y_pts)
            calc_gradient_all = np.append(calc_gradient_all, calculated_gradient)

        # smooth the calculated gradient
        smoothed_gradient = diff_functions.smooth_gradient(
            calc_gradient_all, smoothing_filter
        )

        # output the results
        gradient_title = f"d({y})/d({x})" if gradient == "dydx" else f"d({x})/d({y})"
        gradient_result = self.input_data.clean_copy(
            {x: x_all, y: y_all, gradient_title: smoothed_gradient}
        )
        gradient_result.column_definitions = {
            x: self.input_data.column_definitions[x],
            y: self.input_data.column_definitions[y],
            gradient_title: "The calculated gradient.",
        }
        return gradient_result
