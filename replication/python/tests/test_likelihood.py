import numpy as np
from causal_spdes.core import heat_eigenvalues, noise_loadings
from causal_spdes.likelihood import simulate_exact_ou, profile_mle, transition_parameters

def test_transition_positive():
    lam=heat_eigenvalues(4); q=noise_loadings(lam)
    rho,var=transition_parameters(0.7,0.8,lam,q,0.001)
    assert np.all((rho>0)&(rho<1)); assert np.all(var>0)

def test_profile_mle_smoke():
    lam=heat_eigenvalues(4); q=noise_loadings(lam)
    y=simulate_exact_ou(0.7,0.8,lam,q,600,1.0,seed=44)
    th,sg=profile_mle(y,lam,q,1.0)
    assert 0.05<th<3.0 and sg>0
