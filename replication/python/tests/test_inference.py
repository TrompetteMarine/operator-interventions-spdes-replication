import numpy as np
from causal_spdes.bootstrap import gaussian_parameter_multiplier, floor_standard_error, simultaneous_critical
from causal_spdes.approximation import law_k_rate, balanced_truncation

def test_multiplier_covariance():
    d=gaussian_parameter_multiplier(0.7,0.8,1.0,100000,seed=2)
    assert abs(np.var(d[:,0])-1.4)<0.03
    assert abs(np.var(d[:,1])-0.32)<0.01

def test_floor_and_critical():
    se=floor_standard_error(np.array([0.0,1.0]),0.1)
    assert np.allclose(se,[0.1,1.0])
    c=simultaneous_critical(np.array([[1.,2.],[3.,1.]]),alpha=.5)
    assert c==2.5

def test_rate_allocation():
    rho=law_k_rate(1,1.2,0.75,0.2)
    assert rho>0
    assert balanced_truncation(100,rho)>=2
