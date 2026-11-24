import numpy as np
import pytest
from solid_pinn.comsol_transfer import TransferFEM, table, read_model


def synthetic_model():
    # Artificial fixture, not the collaborator's input tables.
    return dict(eps=.3,epsl=.3,fs=.2,wch=.5,wdch=.5,j0=5.,j0li=100.,sigma=.17,kappa=.43,L=4e-5,Ls=725e-6,rp=1e-5,cmax=47664.,T=323.15,F=96487.,R=8.314,area=2.83e-5,loading=5.,capacity=165.,D=2e-13,tables={
        'Uch':np.array([[0.,3.],[100.,4.2]]),'Udis':np.array([[0.,4.2],[100.,2.7]]),
        'Ds_delithiation_theta':np.array([[0.,1e-13],[1.,2e-13]]),'Ds_lithiation_theta':np.array([[0.,2e-13],[1.,1e-13]]),
        'Rc_node':np.array([[0.,.01],[1.,.02]]),'Rd_node':np.array([[0.,.03],[1.,.04]])})


def test_current_and_mass_balance():
    m=synthetic_model();s=TransferFEM(m,4,6)
    c=np.tile(np.linspace(.65,.7,len(s.r)),(len(s.x),1))
    for stage,sign in [('charge',-1),('discharge',1)]:
        I=sign*s.p.current_a(20);f=s.fields(c[:,-1],I,stage)
        assert s.aL*(s.wx@f.reaction)==pytest.approx(I/m['area'],abs=1e-10)
        dc=s.rhs(c,I,stage)
        expected=I/(m['area']*m['L']*m['eps']*m['F']*m['cmax'])
        assert s.wx@dc@s.wr==pytest.approx(expected,rel=1e-10)


def test_resistance_has_correct_sign_and_table_clamps():
    m=synthetic_model();a=TransferFEM(m,3,5);b=TransferFEM(m,3,5,use_R=False)
    theta=np.full(len(a.x),.7)
    for stage,sign in [('charge',-1),('discharge',1)]:
        I=sign*a.p.current_a(20)
        delta=a.fields(theta,I,stage).voltage-b.fields(theta,I,stage).voltage
        assert delta==pytest.approx(-I/m['area']*table(m,'Rc_node' if sign<0 else 'Rd_node',.7),abs=1e-10)
    assert table(m,'Rc_node',-1)==pytest.approx(.01)
