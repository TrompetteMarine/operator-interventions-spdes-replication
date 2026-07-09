from __future__ import annotations
import numpy as np


def integrated_ou_variance(rate: float, sigma: float, horizon: float) -> float:
    bracket=horizon-2*(-np.expm1(-rate*horizon))/rate+(-np.expm1(-2*rate*horizon))/(2*rate)
    return float(sigma**2*bracket/rate**2)


def feedback_gauge_example(a0=1.0, gamma=0.5, intervention=1.5, sigma=0.6, horizon=1.0):
    factual1=integrated_ou_variance(a0,sigma,horizon)
    factual2=integrated_ou_variance((a0+gamma)-gamma,sigma,horizon)
    cf1=integrated_ou_variance(intervention,sigma,horizon)
    cf2=integrated_ou_variance(intervention-gamma,sigma,horizon)
    return {'factual_gap':abs(factual1-factual2),'cf_variance_1':cf1,'cf_variance_2':cf2}


def crossworld_effect_variance(va: float, vb: float, rho: float) -> float:
    if not -1 <= rho <= 1:
        raise ValueError("rho must be in [-1,1]")
    return va+vb-2*rho*np.sqrt(va*vb)
