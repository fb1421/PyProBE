"""A module containing functions for degradation mode analysis."""

from typing import Tuple

import numpy as np
from numpy.typing import NDArray


def calc_electrode_capacities(
    x_pe_lo: float,
    x_pe_hi: float,
    x_ne_lo: float,
    x_ne_hi: float,
    cell_capacity: float,
) -> Tuple[float, float, float]:
    """Calculate the electrode capacities.

    Args:
        x_pe_lo (float): The cathode stoichiometry at lowest cell SOC.
        x_pe_hi (float): The cathode stoichiometry at highest cell SOC.
        x_ne_lo (float): The anode stoichiometry at lowest cell SOC.
        x_ne_hi (float): The anode stoichiometry at highest cell SOC.

    Returns:
        Tuple[float, float, float]:
            - NDArray: The cathode capacity.
            - NDArray: The anode capacity.
            - NDArray: The lithium inventory.
    """
    pe_capacity = cell_capacity / (x_pe_lo - x_pe_hi)
    ne_capacity = cell_capacity / (x_ne_hi - x_ne_lo)
    li_inventory = (pe_capacity * x_pe_lo) + (ne_capacity * x_ne_lo)
    return pe_capacity, ne_capacity, li_inventory


def calc_full_cell_OCV(
    SOC: NDArray[np.float64],
    x_pe_lo: NDArray[np.float64],
    x_pe_hi: NDArray[np.float64],
    x_ne_lo: NDArray[np.float64],
    x_ne_hi: NDArray[np.float64],
    x_pe: NDArray[np.float64],
    ocp_pe: NDArray[np.float64],
    x_ne: NDArray[np.float64],
    ocp_ne: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Calculate the full cell OCV.

    Args:
        SOC (NDArray[np.float64]): The full cell SOC.
        x_pe_lo (float): The cathode stoichiometry at lowest cell SOC.
        x_pe_hi (float): The cathode stoichiometry at highest cell SOC.
        x_ne_lo (float): The cathode stoichiometry at lowest cell SOC.
        x_ne_hi (float): The anode stoichiometry at highest cell SOC.
        x_pe (NDArray[np.float64]): The cathode stoichiometry data.
        ocp_pe (NDArray[np.float64]): The cathode OCP data.
        x_ne (NDArray[np.float64]): The anode stoichiometry data.
        ocp_ne (NDArray[np.float64]): The anode OCP data.

    Returns:
        NDArray: The full cell OCV.
    """
    n_points = 10000
    # make vectors between stoichiometry limits during charge
    z_ne = np.linspace(x_ne_lo, x_ne_hi, n_points)
    z_pe = np.linspace(
        x_pe_lo, x_pe_hi, n_points
    )  # flip the cathode limits to match charge direction

    # make an SOC vector with the same number of points
    SOC_sampling = np.linspace(0, 1, n_points)

    # interpolate the real electrode OCP data with the created stoichiometry vectors
    OCP_ne = np.interp(z_ne, x_ne, ocp_ne)
    OCP_pe = np.interp(z_pe, x_pe, ocp_pe)
    # OCP_pe = np.flip(OCP_pe) # flip the cathode OCP to match charge direction

    # interpolate the final OCV curve with the original SOC vector
    OCV = np.interp(SOC, SOC_sampling, OCP_pe - OCP_ne)
    return OCV


def calculate_dma_parameters(
    cell_capacity: NDArray[np.float64],
    pe_capacity: NDArray[np.float64],
    ne_capacity: NDArray[np.float64],
    li_inventory: NDArray[np.float64],
) -> Tuple[
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
    NDArray[np.float64],
]:
    """Calculate the DMA parameters.

    Args:
        pe_stoich_limits (NDArray[np.float64]): The cathode stoichiometry limits.
        ne_stoich_limits (NDArray[np.float64]): The anode stoichiometry limits.
        pe_capacity (NDArray[np.float64]): The cathode capacity.
        ne_capacity (NDArray[np.float64]): The anode capacity.
        li_inventory (NDArray[np.float64]): The lithium inventory.

    Returns:
        Tuple[float, float, float, float]: The SOH, LAM_pe, LAM_ne, and LLI.
    """
    SOH = cell_capacity / cell_capacity[0]
    LAM_pe = 1 - pe_capacity / pe_capacity[0]
    LAM_ne = 1 - ne_capacity / ne_capacity[0]
    LLI = 1 - li_inventory / li_inventory[0]
    return SOH, LAM_pe, LAM_ne, LLI
