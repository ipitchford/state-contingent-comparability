#!/usr/bin/env python3
"""Meaningful mathematical and mutation regressions, active under python -O."""
from fractions import Fraction as F
from pathlib import Path
from copy import deepcopy
import importlib.util,json,random,subprocess,sys,tempfile,shutil
from verify import calculate,require,ROOT
from exact_audit import metrics,payment_rows,interval_from_rows,min_quadratic
from model import regimes

def main():
    data=json.loads((ROOT/'data/contracts.json').read_text());base=calculate(data);rng=random.Random(20261013)
    require(base['cap_example']['interval'][:2]==(F(0),F(8)),'Original cap changed')
    require(base['interior_failure']['constraints']['duration']['certificate'].point==(F(1,2),),'Interior numerator minimum changed')
    require(all(b['implemented_audit']['passes'] and not b['raw_audit']['passes'] for b in base['multi_regime']['branches'] if b['reachable']),'Multi-regime verdict failure')
    strengthening=base['nonproportional_oblique_family']
    require(strengthening['implemented_robust_cap']==F(110,7),'Oblique-family robust cap changed')
    require(strengthening['binding_switch_parameter']==F(75,7),'Oblique-family switch threshold changed')
    require({b['id']:b['binding_constraint'] for b in strengthening['branches'] if b['reachable']}=={'0':'programme','1':'duration'},'Oblique trigger no longer changes the binding constraint')
    # Strict endpoint strengthening: positive endpoint duration margins coexist
    # with a negative midpoint margin for every pair of positive discounts.
    eta=F(1,8);d1,d3=F(20,21),F(20,21)**3
    strict=lambda x:4*d1*d3*(x*x-x+eta)
    require(strict(F(0))>0 and strict(F(1))>0 and strict(F(1,2))<0,'Strict endpoint perturbation failed')
    # Identity about duration under removal, with strictly positive residual PV.
    for _ in range(200):
        cf={t:F(rng.randint(2,30)) for t in range(1,7)};removed={t:cf[t]*F(rng.randint(0,8),10) for t in cf};new={t:cf[t]-removed[t] for t in cf};r=F(rng.randint(0,10),100)
        b,n=metrics(cf,r,3,1),metrics(new,r,3,1)
        dv=sum((v/(1+r)**t for t,v in removed.items()),F(0));dm=sum((t*v/(1+r)**t for t,v in removed.items()),F(0))
        require(n.duration-b.duration==(b.duration*dv-dm)/(b.pv-dv),'Removal identity failed')
    # Vary old profiles, rates, payment timing and all three tolerances.
    comparisons=0;floors=0
    for _ in range(100):
        old_i,old_r,bb,rr=[{t:F(rng.randint(1,15)) for t in range(1,5)} for j in range(4)];shape={t:F(rng.randint(0,3)) for t in range(1,5)}
        r=F(rng.randint(-2,5),10);eps=(F(rng.randint(0,2),20),F(rng.randint(0,2),20),F(rng.randint(0,2),4))
        oi,orr,b,ref=[metrics(x,r,2,1) for x in [old_i,old_r,bb,rr]]
        it=interval_from_rows(payment_rows(oi,orr,b,ref,shape,r,2,eps,1),F(10));floors+=bool(it and it[0]>0)
        for p in [F(j,4) for j in range(41)]:
            nn=metrics({t:bb[t]+p*shape[t] for t in bb},r,2,1)
            actual=(nn.pv/oi.pv<=ref.pv/orr.pv+eps[0] and nn.programme_service/oi.programme_service<=ref.programme_service/orr.programme_service+eps[1] and nn.duration-oi.duration>=ref.duration-orr.duration-eps[2])
            require(actual==(it is not None and it[0]<=p<=it[1]),'Payment interval disagrees with direct metrics');comparisons+=1
    # Explicit boundary ownership and unreachable closure-only ghost branches.
    require([b['id'] for b in regimes(data['multi_regime']) if not b['reachable']]==['001','110'],'Strict branch reachability failure')
    triggers=data['multi_regime']['triggers']
    for point,want in [((F(1,2),F(1,2)),'111'),((F(1,4),F(3,4)),'011'),((F(3,4),F(1,4)),'101')]:
        got=''.join(str(int(sum(F(a)*v for a,v in zip(t['coefficients'],point))>=F(t['threshold']))) for t in triggers)
        require(got==want,'Equality ownership failure')
    # Data dependence: substantive edits must change calculation or be rejected.
    mutations=[('interior_failure','candidate_affine','1',0,'1000000'),('cap_example','candidate_base','1',None,'11'),('mixed_triggers','candidate_enhanced','1',None,'28'),('paris_club_example_I','new_cashflows_1','4',None,'21'),('floor_and_information','unobserved_K_values',0,None,'3'),('multi_regime','reference_affine','4',0,'21'),('nonproportional_oblique_family','reference_trigger_addition_shape','6',None,'2')]
    mutation_results=[]
    for section,field,key,index,value in mutations:
        changed=deepcopy(data)
        if index is None:changed[section][field][key]=value
        else:changed[section][field][key][index]=value
        try:
            different=calculate(changed)!=base;require(different,'Substantive data mutation was ignored');outcome='calculation changed'
        except ValueError as exc:
            if str(exc)=='Substantive data mutation was ignored':raise
            outcome='explicit rejection: '+str(exc)
        mutation_results.append({'field':f'{section}.{field}.{key}','result':outcome})
    changed=deepcopy(data);changed['nonproportional_oblique_family']['late_uplift_parameter']='21'
    require(calculate(changed)!=base,'Late-uplift parameter mutation was ignored')
    mutation_results.append({'field':'nonproportional_oblique_family.late_uplift_parameter','result':'calculation changed'})
    changed=deepcopy(data);changed['nonproportional_oblique_family']['late_uplift_parameter_range'][1]='20'
    try:
        calculate(changed)
        require(False,'Late-uplift range mutation was ignored')
    except ValueError as exc:
        require('outside its declared half-open range' in str(exc),'Unexpected range-mutation failure')
    mutation_results.append({'field':'nonproportional_oblique_family.late_uplift_parameter_range','result':'explicit rejection'})
    # Reproduce the reviewer's exact data mutation and corrupt one certificate.
    negative=[]
    with tempfile.TemporaryDirectory() as tmp:
        dst=Path(tmp)/'package';shutil.copytree(ROOT/'code',dst/'code');shutil.copytree(ROOT/'data',dst/'data');shutil.copytree(ROOT/'results',dst/'results');shutil.copy2(ROOT/'input-lock.json',dst/'input-lock.json')
        path=dst/'data/contracts.json';changed=deepcopy(data);changed['interior_failure']['candidate_affine']['1'][0]='1000000';path.write_text(json.dumps(changed))
        run=subprocess.run([sys.executable,'-B','-O',str(dst/'code/verify.py')],capture_output=True,text=True)
        require(run.returncode!=0 and 'integrity failure' in run.stderr,'Mutated input not rejected under -O');negative.append('reviewer input mutation rejected under -O')
        shutil.copy2(ROOT/'data/contracts.json',path);p=dst/'results/certificates.json';bad=json.loads(p.read_text());bad['results']['interior_failure']['constraints']['duration']['certificate']['minimum']='0';p.write_text(json.dumps(bad))
        run=subprocess.run([sys.executable,'-B','-O',str(dst/'code/check_certificates.py')],capture_output=True,text=True)
        require(run.returncode!=0 and 'Minimum or witness mismatch' in run.stderr,'False certificate accepted under -O');negative.append('false minimum rejected by separate checker under -O')
        shutil.copy2(ROOT/'results/certificates.json',p);bad=json.loads(p.read_text());record=bad['results']['interior_failure'];record['domain']['upper']=['0']
        for constraint in record['constraints'].values():
            minimum=F(constraint['polynomial']['constant']);constraint['certificate']['minimum']=str(minimum);constraint['certificate']['point']=['0'];constraint['passes']=minimum>=0
        record['passes']=all(c['passes'] for c in record['constraints'].values());p.write_text(json.dumps(bad))
        run=subprocess.run([sys.executable,'-B','-O',str(dst/'code/check_certificates.py')],capture_output=True,text=True)
        require(run.returncode!=0 and 'Certificate domain does not match declared model' in run.stderr,'Truncated certificate domain accepted under -O');negative.append('self-consistent truncated domain rejected by separate checker under -O')
    print(json.dumps({'status':'passed','removal_identity_models':200,'payment_models':100,'direct_payment_comparisons':comparisons,'positive_floor_models':floors,
        'strict_endpoint_perturbation':'eta=1/8 passes both endpoints and fails at x=1/2',
        'oblique_family':{'off_trigger_cap':'25','on_trigger_cap':'110/7','binding_switch':'75/7'},
        'data_dependence_mutations':mutation_results,'negative_controls':negative,'assert_statements_required':False},indent=2))

if __name__=='__main__':main()
