from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from scipy.optimize import minimize_scalar


def transition_parameters(theta: float, sigma: float, lam: np.ndarray, q: np.ndarray, dt: float):
    rho = np.exp(-theta * lam * dt)
    h = -np.expm1(-2.0 * theta * lam * dt) / (2.0 * theta * lam)
    return rho, sigma**2 * q**2 * h


def simulate_exact_ou(theta: float, sigma: float, lam: np.ndarray, q: np.ndarray, n_times: int, horizon: float, seed: int = 1, u0: np.ndarray | None = None) -> np.ndarray:
    if n_times < 1:
        raise ValueError("n_times must be positive")
    rng = np.random.default_rng(seed)
    lam = np.asarray(lam, dtype=float); q = np.asarray(q, dtype=float)
    dt = horizon / n_times
    rho, var = transition_parameters(theta, sigma, lam, q, dt)
    y = np.zeros((n_times + 1, len(lam)), dtype=float)
    if u0 is not None:
        y[0] = np.asarray(u0, dtype=float)
    for j in range(n_times):
        y[j + 1] = rho * y[j] + np.sqrt(var) * rng.standard_normal(len(lam))
    return y


def sufficient_statistics(y: np.ndarray):
    x = y[:-1]; nxt = y[1:]
    return np.sum(x*x, axis=0), np.sum(x*nxt, axis=0), np.sum(nxt*nxt, axis=0)


def profile_mle(y: np.ndarray, lam: np.ndarray, q: np.ndarray, horizon: float, theta_bounds=(0.05, 3.0), sigma_bounds=None):
    """Exact conditional profile MLE.

    With ``sigma_bounds=(lo, hi)`` this implements the *corrected constrained*
    profile of Proposition 9.13 (paper v3): for every drift candidate theta the
    scale is the unconstrained stationary point clamped to [lo^2, hi^2], and
    the clamped value enters the profile criterion before the drift profile is
    minimised (clamp-then-profile, never profile-then-project once).  With
    ``sigma_bounds=None`` the historical unconstrained profile is retained for
    backwards compatibility of archived tables.
    """
    y = np.asarray(y, dtype=float); lam=np.asarray(lam,dtype=float); q=np.asarray(q,dtype=float)
    n_times = y.shape[0] - 1; n_modes = y.shape[1]; dt = horizon / n_times
    sxx, sxy, syy = sufficient_statistics(y)

    def clamp(v: float) -> float:
        if sigma_bounds is None:
            return max(v, np.finfo(float).tiny)
        lo2, hi2 = sigma_bounds[0]**2, sigma_bounds[1]**2
        return min(max(v, lo2), hi2)

    def objective(theta: float):
        rho = np.exp(-theta * lam * dt)
        h = -np.expm1(-2.0 * theta * lam * dt) / (2.0 * theta * lam)
        rss = np.sum((syy - 2*rho*sxy + rho*rho*sxx)/(q*q*h))
        s2 = rss/(n_modes*n_times)
        v = clamp(s2)
        return n_modes*n_times*(np.log(v) + s2/v) + n_times*np.sum(np.log(q*q*h))
    result = minimize_scalar(objective, bounds=theta_bounds, method='bounded', options={'xatol':1e-10})
    if not result.success:
        raise RuntimeError(result.message)
    theta_hat=float(result.x)
    rho=np.exp(-theta_hat*lam*dt)
    h=-np.expm1(-2*theta_hat*lam*dt)/(2*theta_hat*lam)
    rss=np.sum((syy-2*rho*sxy+rho*rho*sxx)/(q*q*h))
    sigma_hat=float(np.sqrt(clamp(rss/(n_modes*n_times))))
    return theta_hat, sigma_hat


def limiting_information(theta: float, sigma: float, horizon: float) -> np.ndarray:
    return np.diag([horizon/(2.0*theta), 2.0/sigma**2])
