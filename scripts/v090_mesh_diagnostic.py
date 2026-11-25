"""Exploratory v0.9.0a mesh diagnostic; leaves original solver unchanged.
Run OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python scripts/v090_mesh_diagnostic.py
"""
from pathlib import Path
import numpy as np
import hybrid_p2d as h
s=Path(h.__file__).read_text()
old='S=np.eye(n*m)[m-1::m];B=S.T*n/w[-1];M='
rad='''S=np.eye(n*m)[m-1::m];B=S.T*n/w[-1]
    edges=np.linspace(0,1,m+1);rbar=.75*np.diff(edges**4)/w
    e=(1-rbar[-1])/(rbar[-1]-rbar[-2]);S=S*(1+e)-e*np.eye(n*m)[m-2::m]
    M='''
assert s.count(old)==1 and s.count('V-.25*J')==1
ax=lambda src:src.replace('V-.25*J','V-(.25+(.25+.7)/(2*n))*J')
variants={'original':s,'radial':s.replace(old,rad),'axial':ax(s),'both':ax(s.replace(old,rad))}
meshes=[(8,12),(16,12),(8,24),(16,24),(32,48)]
pairs=[((8,12),(16,12)),((8,12),(8,24)),((8,12),(16,24)),((16,24),(32,48))]
for name,src in variants.items():
    ns={'__name__':'candidate'}
    exec(compile(src,'<mesh-diagnostic>','exec'),ns)
    print(name)
    for k in h.BLOCKS:
        j=h.profile(k);v={};a={}
        for n,m in meshes:
            v[n,m],a[n,m]=ns['cell'](j,n,m)
        print(k,[float(np.max(abs(v[p]-v[q]))*1000) for p,q in pairs],
              'mass',max(x['mass'] for x in a.values()),
              'charge',max(x['charge'] for x in a.values()))
