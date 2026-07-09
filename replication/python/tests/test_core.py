import numpy as np
from causal_spdes.core import heat_eigenvalues, noise_loadings
from causal_spdes.targets import integrated_mode_variance, gaussian_w2

def test_heat_eigenvalues():
    lam=heat_eigenvalues(3)
    assert np.allclose(lam,np.pi**2*np.array([1,4,9]))

def test_variance_decreases_with_rate():
    v=integrated_mode_variance(np.array([0.5,1.0,2.0]),0.8,1.0,1.0)
    assert np.all(np.diff(v)<0)

def test_gaussian_w2_identity():
    assert np.isclose(gaussian_w2(0,1,0,4),1.0)
