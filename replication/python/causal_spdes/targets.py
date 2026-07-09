from __future__ import annotations
import math
import numpy as np
from scipy.stats import norm


def integrated_mode_variance(rate: float | np.ndarray, sigma: float, q: float | np.ndarray, horizon: float) -> np.ndarray:
    rate = np.asarray(rate, dtype=float)
    q = np.asarray(q, dtype=float)
    if np.any(rate <= 0) or sigma <= 0 or horizon <= 0:
        raise ValueError("positive rates, sigma, and horizon required")
    bracket = (
        horizon
        - 2.0 * (-np.expm1(-rate * horizon)) / rate
        + (-np.expm1(-2.0 * rate * horizon)) / (2.0 * rate)
    )
    return sigma**2 * q**2 * bracket / rate**2


def gaussian_cdf(z: np.ndarray | float, mean: np.ndarray | float, variance: np.ndarray | float) -> np.ndarray:
    variance = np.asarray(variance, dtype=float)
    if np.any(variance <= 0):
        raise ValueError("variance must be positive")
    return norm.cdf((np.asarray(z) - np.asarray(mean)) / np.sqrt(variance))


def gaussian_quantile(p: np.ndarray | float, mean: np.ndarray | float, variance: np.ndarray | float) -> np.ndarray:
    p = np.asarray(p, dtype=float)
    if np.any((p <= 0) | (p >= 1)):
        raise ValueError("p must lie in (0,1)")
    return np.asarray(mean) + np.sqrt(np.asarray(variance)) * norm.ppf(p)


def gaussian_w2(mean1: float, variance1: float, mean2: float, variance2: float) -> float:
    return math.sqrt((mean1 - mean2) ** 2 + (math.sqrt(variance1) - math.sqrt(variance2)) ** 2)
