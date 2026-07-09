from __future__ import annotations
import numpy as np


def gaussian_parameter_multiplier(theta_hat: float, sigma_hat: float, horizon: float, draws: int, seed: int = 1) -> np.ndarray:
    rng=np.random.default_rng(seed)
    out=np.empty((draws,2))
    out[:,0]=np.sqrt(2.0*theta_hat/horizon)*rng.standard_normal(draws)
    out[:,1]=sigma_hat/np.sqrt(2.0)*rng.standard_normal(draws)
    return out


def floor_standard_error(se: np.ndarray, kappa: float) -> np.ndarray:
    se=np.asarray(se,dtype=float)
    if kappa <= 0:
        raise ValueError("kappa must be positive")
    return np.maximum(se, kappa*max(float(np.max(se)), np.finfo(float).eps))


def simultaneous_critical(process_draws: np.ndarray, alpha: float = 0.05) -> float:
    if process_draws.ndim != 2:
        raise ValueError("draws x index array required")
    return float(np.quantile(np.max(np.abs(process_draws),axis=1),1-alpha))
