from __future__ import annotations
import numpy as np


def mean_tail_bound(lambda_next: float, r0: float, s: float, constant: float = 1.0) -> float:
    mu=(r0+1.0+2.0*s)/2.0
    return constant*lambda_next**(-mu)


def variance_tail_bound(lambda_next: float, beta: float, s: float, constant: float = 1.0) -> float:
    mu=beta+2.0+2.0*s
    return constant*lambda_next**(-mu)


def law_k_rate(dimension: int, r0: float, beta: float, s: float) -> float:
    return min((r0+1+2*s)/dimension, 2*(beta+2+2*s)/dimension)


def balanced_truncation(rate: float, rho: float, undersmooth_factor: float = 1.0) -> int:
    if rate <= 1 or rho <= 0 or undersmooth_factor < 1:
        raise ValueError("invalid rate allocation")
    return int(np.ceil((rate*undersmooth_factor)**(1.0/rho)))
