import numpy as np
import requests
import pandas as pd

"""
A module to compute Modified Berggren Frost Depth.
"""


def compute_volumetric_latent_heat_of_fusion(dry_ro, wc_pct):
    """Compute the amount of heat required to melt all the ice or freeze the pore water) in a unit volume of soil.
    Args:
        dry_ro: soil dry density (lbs per cubic foot)
        wc_pct: percent water content (percent)
    Returns:
        L: volumetric latent heat of fusion (BTUs per cubic foot)
    """
    L = 144 * dry_ro * (wc_pct / 100)
    return round(L, 2)


def compute_frozen_volumetric_specific_heat(dry_ro, wc_pct):
    """Compute quantity of heat required to change the temperature of a frozen unit volume of soil by 1°F. The specific heat of soil solids is 0.17 BTU/lb • °F for most soils.
    Args:
        dry_ro: soil dry density (lbs per cubic foot)
        wc_pct: percent water content (percent)
    Returns:
        c: volumetric specific heat (BTUs per cubic foot) • °F
    """
    c = dry_ro * (0.17 + (0.5 * (wc_pct / 100)))
    return round(c, 2)


def compute_unfrozen_volumetric_specific_heat(dry_ro, wc_pct):
    """Compute quantity of heat required to change the temperature of an unfrozen unit volume of soil by 1°F. The specific heat of soil solids is 0.17 BTU/lb • °F for most soils.
    Args:
        dry_ro: soil dry density (lbs per cubic foot)
        wc_pct: percent water content (percent)
    Returns:
        c: volumetric specific heat (BTUs per cubic foot) • °F
    """
    c = dry_ro * (0.17 + (1.0 * (wc_pct / 100)))
    return round(c, 2)


def compute_avg_volumetric_specific_heat(dry_ro, wc_pct):
    """Compute quantity of heat required to change the temperature of an average unit volume of soil by 1°F. The specific heat of soil solids is 0.17 BTU/lb • °F for most soils.
    Args:
        dry_ro: soil dry density (lbs per cubic foot)
        wc_pct: percent water content (percent)
    Returns:
        c: volumetric specific heat (BTUs per cubic foot) • °F
    """
    c = dry_ro * (0.17 + (0.75 * (wc_pct / 100)))
    return round(c, 2)


def compute_seasonal_v_s(nFI, d):
    """Compute the v_s parameter.

    v_s has one of two possible meanings depending on the problem being studied. In this case, v_s is useful for computing a seasonal depth of freeze.

    Args:
        d: optional length of freezing duration (days)
        nFI: optional surface freezing index (°F • days)
    Returns:
         v_s
    """
    v_s = nFI / d
    return v_s


def get_projected_mat_from_api(lat, lon, model, scenario, year_start, year_end):
    """Query the SNAP Data API for mean annual temperature."""

    api_url = f"https://earthmaps.io/mmm/temperature/all/{lat}/{lon}"
    resp = requests.get(api_url).json()[model][scenario]
    df = pd.json_normalize(resp, sep="_").T
    years = [int(j.split('_')[0]) for j in df.index.values]
    df["year"] = years
    df.set_index("year", inplace=True)
    mean_temp_degC = df.loc[year_start:year_end].mean()
    mat_degF = (mean_temp_degC * 1.8) + 32
    return float(round(mat_degF, 1))


def get_projected_design_fi_from_api(lat, lon, model, era):
    """Query the SNAP Data API for design freezing index."""
    api_url = f"https://earthmaps.io/design_index/freezing/all/point/{lat}/{lon}"
    design_freezing_index_degF = requests.get(api_url).json()[model][era]["di"]
    return design_freezing_index_degF


def compute_multiyear_v_s(mat):
    """Compute the v_s parameter.

    v_s has one of two possible meanings depending on the problem being studied. In this case, v_s is useful in computing multiyear freeze depths that may develop as a long-term change in the heat balance at the ground surface.

    Args:
        mat: mean annual temperature (°F)
    Returns:
         v_s
    """
    v_s = abs(mat - 32)
    return v_s


def compute_v_o(magt):
    """Compute the v_o parameter.

    v_o is the absolute value of the difference between the mean annual temperature BELOW THE GROUND SURFACE and 32 °F.

    Args:
        magt: mean annual temperature below the ground surface (°F)
    Returns:
         v_o
    """
    v_o = abs(magt - 32)
    return v_o


def compute_thermal_ratio(v_o, v_s):
    """Compute the the thermal ratio.

    The thermal ratio is the ratio of two deltas: ground temperature - freezing and surface temperature - freezing.

    Args:
        v_o
        v_s
    Returns:
        thermal_ratio: dimensionless
    """
    thermal_ratio = v_o / v_s
    return round(thermal_ratio, 3)


def compute_fusion_parameter(v_s, c, L):
    """Compute the fusion parameter.

    Args:
        v_s
        c: volumetric specific heat ((BTUs per cubic foot) • °F)
        L: volumetric latent heat of fusion (BTUs per cubic foot)
    Returns:
        mu: (dimensionless)
    """
    mu = v_s * (c / L)
    return round(mu, 3)


def compute_coeff(mu, thermal_ratio):
    """Compute the lambda coeffcient (dimensionless).

    Citation: H. P. Aldrich and H. M. Paynter, “Analytical Studies of Freezing and Thawing of Soils,” Arctic Construction and Frost Effects Laboratory, Corps of Engineers, U.S. Army, Boston, MA, First Interim Technical Report 42, Jun. 1953.

    Other implementations:
    lc2 = 0.707 / (np.sqrt(1 + (mu * (thermal_ratio + 0.5))))
    lc_mean = round(np.mean([lc1, lc2]), 2)

    These are included because:
    lc may overestimate frost depth - but is suited to high latitudes
    lc2 may underestimate frost depth - but is better for lower latitudes
    lc_mean is a middle ground

    Args:
        mu: the fusion parameter (dimensionless)
        thermal_ratio: thermal ratio (dimensionless)
    Returns
        lc: the lambda coeffcient value (dimensionless).
    """
    lc = 1.0 / (np.sqrt(1 + (mu * (thermal_ratio + 0.5))))
    return round(lc, 2)


def compute_depth_of_freezing(coeff, k_avg, nFI, L):
    """Compute the depth to which 32 °F temperatures will penetrate into the soil mass.

    Args:
        coeff: the lambda coeffcient (dimensionless)
        k_avg: thermal conductivity of soil, average of frozen and unfrozen (BTU/hr • ft • °F)
        nFI: surface freezing index (°F • days)
        L: volumetric latent heat of fusion (BTUs per cubic foot)
    Returns:
        x: frost depth (feet)
    """
    x = coeff * np.sqrt((48 * k_avg * nFI) / L)
    return round(x, 1)


def compute_modified_bergrenn(dry_ro, wc_pct, mat, magt, d, nFI, k_avg, lat, lon, model, scenario, year_start, year_end):
    """
    Args:
    dry_ro: soil dry density (lbs per cubic foot)
    wc_pct: water content (percent)
    mat: mean annual temperature (°F)
    magt: mean annual GROUND temperature (°F)
    d: length of freezing duration (days)
    nFI: surface freezing index (°F • days)
    k_avg: thermal conductivity of soil, average of frozen and unfrozen (BTU/hr • ft • °F)
    """
    mat = get_projected_mat_from_api(
        lat, lon, model, scenario, year_start, year_end)
    L = compute_volumetric_latent_heat_of_fusion(dry_ro, wc_pct)
    c = compute_avg_volumetric_specific_heat(dry_ro, wc_pct)
    v_s = compute_seasonal_v_s(nFI, d)
    v_o = compute_v_o(magt)
    thermal_ratio = compute_thermal_ratio(v_o, v_s)
    mu = compute_fusion_parameter(v_s, c, L)
    lambda_coeff = compute_coeff(mu, thermal_ratio)
    frost_depth = compute_depth_of_freezing(lambda_coeff, k_avg, nFI, L)
    return frost_depth
