from __future__ import annotations
import numpy as np
from scipy.linalg import expm


def semigroup_directional_derivative(A: np.ndarray, B: np.ndarray, t: float, quadrature: int = 600) -> np.ndarray:
    grid=np.linspace(0.0,t,quadrature+1)
    vals=np.stack([expm((t-s)*A)@B@expm(s*A) for s in grid])
    return np.trapezoid(vals,grid,axis=0)


def finite_difference_derivative(A: np.ndarray, B: np.ndarray, t: float, eps: float) -> np.ndarray:
    return (expm(t*(A+eps*B))-expm(t*(A-eps*B)))/(2.0*eps)
