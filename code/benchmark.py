#!/usr/bin/env python3
"""Small controlled scaling experiment; writes timing evidence, not proof."""
from fractions import Fraction as F
from pathlib import Path
from math import comb
import json,platform,time,sys
from exact_audit import min_quadratic,jsonable
ROOT=Path(__file__).resolve().parents[1]
rows=[]
for n,R in [(n,1) for n in range(1,6)]+[(2,R) for R in [4,8,16]]:
    Q=[[F(int(i==j)) for j in range(n)] for i in range(n)];l=[F(-2,3)]*n;c=F(n,9)-F(1,7)
    start=time.perf_counter();candidates=0
    for _ in range(R):
        result=min_quadratic(Q,l,c,[0]*n,[1]*n)
        if result.minimum!=-F(1,7):raise ValueError('Benchmark minimum mismatch')
        candidates+=len(result.candidates)
    rows.append({'dimension':n,'independent_regime_copies':R,'active_subsets_enumerated':R*sum(comb(2*n,k) for k in range(n+1)),'stationary_candidates':candidates,'elapsed_seconds':round(time.perf_counter()-start,6),'minimum_each':'-1/7'})
out={'python':sys.version.split()[0],'platform':platform.platform(),'processor':platform.machine(),'threads':1,'method':'one run per setting; no warmup; identical boxed separable quadratics repeated to isolate regime-count growth; not a country workload','measurements':rows}
(ROOT/'results/benchmark.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
