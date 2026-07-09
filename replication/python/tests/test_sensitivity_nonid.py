import numpy as np
from causal_spdes.sensitivity import semigroup_directional_derivative, finite_difference_derivative
from causal_spdes.nonidentification import feedback_gauge_example, crossworld_effect_variance

def test_noncommuting_derivative():
    A=np.diag([-1.,-2.,-3.]); B=np.array([[0.,.3,0.],[.1,0.,.2],[0.,-.2,0.]])
    exact=semigroup_directional_derivative(A,B,.6,quadrature=1500)
    fd=finite_difference_derivative(A,B,.6,1e-4)
    assert np.linalg.norm(exact-fd)<2e-5

def test_gauge_merge_split():
    out=feedback_gauge_example()
    assert out['factual_gap']<1e-14
    assert abs(out['cf_variance_1']-out['cf_variance_2'])>1e-3

def test_crossworld_coupling():
    assert crossworld_effect_variance(.3,.7,.8)!=crossworld_effect_variance(.3,.7,-.5)
