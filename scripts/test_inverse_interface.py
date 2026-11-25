import numpy as np
import torch
from inverse_interface import P,K,grid,voltage,state,ls,jac_ratio,PINN

def test_single_exact_confounding():
    t,j=grid(np.arange(30.),[1.]);p=P.copy();p[3]=1.2
    shift=K*(np.arcsinh(1/(2*P[3]))-np.arcsinh(1/(2*p[3])))/2
    p[:2]+=shift
    np.testing.assert_allclose(voltage(t,j,p),voltage(t,j,P),atol=1e-10)
    assert jac_ratio(t,j)<1e-9

def test_multicurrent_exact_recovery():
    t,j=grid(np.arange(30.),[.25,.5,1.,2.,4.]);np.testing.assert_allclose(ls(t,j,voltage(t,j,P)),P,rtol=1e-7);assert jac_ratio(t,j)>.01

def test_network_passivity_initial_and_odd_voltage():
    m=PINN().double();x=torch.linspace(0,1,11,dtype=torch.float64).reshape(-1,1);j=torch.ones_like(x)
    assert torch.all(m.state(x)>0);torch.testing.assert_close(m.state(x[:1]).reshape(()),m.params()[0]);torch.testing.assert_close(m(x,j),-m(x,-j))
