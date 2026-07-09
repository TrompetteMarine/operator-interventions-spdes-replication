from __future__ import annotations
from dataclasses import dataclass
import numpy as np


def heat_eigenvalues(n_modes: int, dimension: int = 1) -> np.ndarray:
    if n_modes < 1:
        raise ValueError("n_modes must be positive")
    if dimension != 1:
        raise NotImplementedError("The reference implementation uses D=(0,1)")
    k = np.arange(1, n_modes + 1, dtype=float)
    return np.pi**2 * k**2


def noise_loadings(lam: np.ndarray, beta: float = 0.75) -> np.ndarray:
    if beta < 0:
        raise ValueError("beta must be non-negative")
    return (1.0 + np.asarray(lam, dtype=float)) ** (-0.5 * beta)


@dataclass(frozen=True)
class HeatModel:
    theta: float = 0.7
    sigma: float = 0.8
    horizon: float = 1.0
    beta: float = 0.75

    def validate(self) -> None:
        if self.theta <= 0 or self.sigma <= 0 or self.horizon <= 0:
            raise ValueError("theta, sigma, and horizon must be positive")
