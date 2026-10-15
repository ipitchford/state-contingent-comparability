#!/usr/bin/env python3
"""Generate or check deterministic, input-bound exact financial certificates.

Default is read-only checking. --write regenerates calculation outputs explicitly.
No network, nonstandard dependencies, floating-point financial arithmetic or assert.
"""
from fractions import Fraction as F
from pathlib import Path
import argparse, csv, hashlib, io, json, sys
from exact_audit import metrics, efforts, payment_rows, interval_from_rows, jsonable
from model import cf, affine, at, add, scale, audit, regimes, multi_streams, moments, mul, qsum, minimum

ROOT=Path(__file__).resolve().parents[1]
VERSION='3.0.0'

def require(condition,message):
    if not condition: raise ValueError(message)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def bindings():
    return {str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'data/contracts.json',*sorted((ROOT/'code').glob('*.py'))]}

def metric(d,r,start,end): return metrics(cf(d),r,end,start)

def weighted_bound(oi,orr,base,ref,shape,r,start,end,weights,upper):
    wH,wL,wD=weights
    v=sum((c/(1+r)**t for t,c in shape.items()),F(0))
    m=sum((t*c/(1+r)**t for t,c in shape.items()),F(0))
    s=sum((c for t,c in shape.items() if start<=t<=end),F(0))
    target=sum((a*b for a,b in zip(weights,efforts(orr,ref))),F(0))
    A=wH*v/oi.pv+wL*s/oi.programme_service
    B=wH*(1-base.pv/oi.pv)+wL*(1-base.programme_service/oi.programme_service)-wD*oi.duration-target
    poly=[B*base.pv+wD*base.moment,B*v-A*base.pv+wD*m,-A*v]
    def value(p): return poly[0]+poly[1]*p+poly[2]*p*p
    require(value(0)>=0,'Weighted base must pass in this cap example')
    if value(upper)>=0: bracket=[upper,upper]
    else:
        lo,hi=F(0),upper
        for _ in range(80):
            mid=(lo+hi)/2
            if value(mid)>=0: lo=mid
            else: hi=mid
        bracket=[lo,hi]
    return {'weights':weights,'nonnegative_polynomial_ascending':poly,'maximum_payment_bracket':bracket}

def calculate(data):
    def exact_input(x):
        if isinstance(x,float): raise ValueError('Floating input rejected; use rational strings')
        if isinstance(x,dict):
            for v in x.values(): exact_input(v)
        if isinstance(x,list):
            for v in x: exact_input(v)
    exact_input(data)
    require(data['version']==VERSION,'Unsupported data schema')
    r=F(data['default_rate']);out={'calculation_version':VERSION,'scope':'Declared synthetic financial screens; no country verdict'}
    x=data['cap_example'];start,end=x['programme_start'],x['programme_end']
    oi=metric(x['old'],r,start,end);ref=metric(x['reference'],r,start,end);base=metric(x['candidate_base'],r,start,end)
    shape=cf(x['bonus_shape']);rows=payment_rows(oi,oi,base,ref,shape,r,end,programme_start=start)
    domain=list(map(F,x['state_domain']));raw=list(map(F,x['raw_bonus_affine']));P=max(raw[0]+raw[1]*q for q in domain)
    inter=interval_from_rows(rows,P)
    require(inter is not None,'Cap example infeasible')
    out['cap_example']={'rows':rows,'individual_bounds':{name:b/a for name,a,b in rows if a>0},'interval':inter,'raw_maximum':P,
        'weighted':weighted_bound(oi,oi,base,ref,shape,r,start,end,list(map(F,x['weighted_weights'])),P)}
    sensitivity=[]
    for eps in map(F,data['sensitivity']['duration_tolerances']):
        rr=payment_rows(oi,oi,base,ref,shape,r,end,(F(0),F(0),eps),start)
        sensitivity.append({'duration_tolerance':eps,'interval':interval_from_rows(rr,P)})
    out['duration_tolerance_sensitivity']=sensitivity
    out['weight_sensitivity']=[weighted_bound(oi,oi,base,ref,shape,r,start,end,[F(1),F(1),F(w)],P) for w in data['sensitivity']['duration_weights']]
    out['rate_regressions']=[]
    for rr in map(F,data['sensitivity']['rate_regressions']):
        oo,bb,rf=[metric(x[k],rr,start,end) for k in ['old','candidate_base','reference']]
        out['rate_regressions'].append({'rate':rr,'interval':interval_from_rows(payment_rows(oo,oo,bb,rf,shape,rr,end,programme_start=start),P)})
    # Every original financial example is now compiled from numeric input fields.
    x=data['interior_failure'];ci,cr=affine(x['candidate_affine']),affine(x['reference_affine'])
    lo,hi=map(F,x['state_domain']);old=cf(x['old'])
    out['interior_failure']=audit(old,old,ci,cr,r,x['programme_start'],x['programme_end'],[lo],[hi])
    out['scenario_domain_sensitivity']=[]
    for a,b in data['sensitivity']['state_domains']:
        aa,bb=F(a),F(b)
        result=audit(old,old,ci,cr,r,x['programme_start'],x['programme_end'],[aa],[bb])
        q=result['constraints']['duration']['polynomial'];Q,l,c=q['Q'],q['linear'],q['constant']
        Vi,_,_=moments(ci,r,x['programme_start'],x['programme_end']);Vr,_,_=moments(cr,r,x['programme_start'],x['programme_end'])
        low,high=F(0),F(1)
        for _ in range(65):
            eps=(low+high)/2
            tol=qsum((1,(Q,l,c)),(eps,mul(Vi,Vr)))
            if minimum(tol,[aa],[bb]).minimum>=0: high=eps
            else: low=eps
        out['scenario_domain_sensitivity'].append({'domain':[aa,bb],'numerator_minimum':result['constraints']['duration']['certificate'].minimum,'required_tolerance_bracket':[low,high]})
    x=data['mixed_triggers'];a,b=F(x['candidate_threshold']),F(x['reference_threshold'])
    lo,hi=map(F,x['state_domain']);require(lo<a<b<hi,'Expected ordered mixed-trigger thresholds')
    mixed=[]
    for lower,upper,ck,rk,interval in [(lo,a,'candidate_base','reference_base','[lo,a)'),(a,b,'candidate_enhanced','reference_base','[a,b)'),(b,hi,'candidate_enhanced','reference_enhanced','[b,hi]')]:
        ci={t:[v,F(0)] for t,v in cf(x[ck]).items()};cr={t:[v,F(0)] for t,v in cf(x[rk]).items()}
        result=audit(cf(x['old']),cf(x['old']),ci,cr,r,x['programme_start'],x['programme_end'],[lower],[upper])
        mixed.append({'interval':interval,'bounds':[lower,upper],'audit':result})
    out['mixed_triggers']=mixed
    x=data['floor_and_information'];old=metric(x['old'],r,1,1);base=metric(x['candidate_base'],r,1,1)
    intervals=[]
    for k in map(F,x['unobserved_K_values']):
        rr=cf(x['reference_early'])
        for t,v in cf(x['reference_late_shape']).items(): rr[t]=rr.get(t,F(0))+k*v
        ref=metrics(rr,r,1,1)
        intervals.append(interval_from_rows(payment_rows(old,old,base,ref,cf(x['bonus_shape']),r,1,programme_start=1)))
    lower=max(it[0] for it in intervals if it);upper=min(it[1] for it in intervals if it)
    out['floor_and_information']={'intervals':intervals,'common_interval':None if lower>upper else [lower,upper]}
    x=data['paris_club_example_I'];rr=F(x['rate']);s,e=x['programme_start'],x['programme_end']
    old=metric(x['old_cashflows'],rr,s,e);c1=metric(x['new_cashflows_1'],rr,s,e);c2=metric(x['new_cashflows_2'],rr,s,e)
    out['public_benchmark']={'old':old,'creditor_1':c1,'creditor_2':c2,'efforts_1':efforts(old,c1),'efforts_2':efforts(old,c2),'rounding_assumption':x['rounding_assumption']}
    x=data['multi_regime'];rr=F(x['rate']);s,e=x['programme_start'],x['programme_end'];lo,hi=list(map(F,x['lower'])),list(map(F,x['upper']))
    require(x['observed_for_early_payment']==['u'],'Only the declared observation structure is implemented')
    require(set(x['implemented_payment'])<=set(['base','a']),'Early policy depends on hidden information')
    oi,orr=metric(x['old_candidate'],rr,s,e),metric(x['old_reference'],rr,s,e)
    require(oi.pv==orr.pv and oi.duration==orr.duration,'Analytical multi-regime cap requires matched old PV and duration')
    multi=[]
    for branch in regimes(x):
        rec={**branch}
        if branch['reachable']:
            ci,cr,alpha=multi_streams(x,branch['active']);raw,_,_=multi_streams(x,branch['active'],'raw')
            rec['alpha']=alpha
            rec['implemented_audit']=audit(cf(x['old_candidate']),cf(x['old_reference']),ci,cr,rr,s,e,lo,hi,branch['A'],branch['b'])
            rec['raw_audit']=audit(cf(x['old_candidate']),cf(x['old_reference']),raw,cr,rr,s,e,lo,hi,branch['A'],branch['b'])
            early=int(x['payment_date']);require(cr[early][1:]==[0,0],'Reference early service is not constant')
            rec['statewise_duration_cap']=alpha*cr[early][0]-F(x['candidate_early_base'])
            require(alpha<=oi.programme_service/orr.programme_service,'Programme constraint invalidates the simple cap')
        multi.append(rec)
    out['multi_regime']={'branches':multi,'old_candidate':oi,'old_reference':orr,'observed_policy':x['implemented_payment']}

    # A second exact family removes three simplifying features of the engineering
    # example above: the old claims are unmatched, the late streams are not
    # proportional, and the oblique trigger changes the binding constraint.
    x=data['nonproportional_oblique_family'];rr=F(x['rate']);s,e=x['programme_start'],x['programme_end']
    require(x['observed_for_early_payment']==['u'],'Only the declared early-information structure is implemented')
    oi,orr=metric(x['old_candidate'],rr,s,e),metric(x['old_reference'],rr,s,e)
    require(oi.pv!=orr.pv and oi.duration!=orr.duration,'The strengthening requires unmatched old claims')
    base=metric(x['candidate_base'],rr,s,e);shape=cf(x['payment_shape']);upper=F(x['raw_payment_upper'])
    parameter=F(x['late_uplift_parameter']);parameter_lower,parameter_upper=map(F,x['late_uplift_parameter_range'])
    require(parameter_lower<=parameter<parameter_upper,'Late-uplift parameter lies outside its declared half-open range')
    addition_shape=cf(x['reference_trigger_addition_shape'])
    require(addition_shape and all(v>=0 for v in addition_shape.values()) and any(v>0 for v in addition_shape.values()),
        'Late-uplift shape must be a nonzero nonnegative stream')
    def parameterised_reference(lam):
        reference=cf(x['reference_base'])
        for t,v in addition_shape.items(): reference[t]=reference.get(t,F(0))+lam*v
        return reference
    family=[]
    for branch in regimes(x):
        rec={**branch}
        if branch['reachable']:
            reference=parameterised_reference(parameter) if branch['active']['g'] else cf(x['reference_base'])
            ref=metrics(reference,rr,e,s)
            rows=payment_rows(oi,orr,base,ref,shape,rr,e,programme_start=s)
            interval=interval_from_rows(rows,upper)
            require(interval is not None,'Strengthening family must have a nonempty payment interval')
            positive_bounds={name:b/a for name,a,b in rows if a>0}
            binding=min(positive_bounds,key=positive_bounds.get)
            rec.update({'reference':ref,'rows':rows,'interval':interval,'binding_constraint':binding})
        family.append(rec)
    caps={b['id']:b['interval'][1] for b in family if b['reachable']}
    # Derive the whole duration-cap family from the declared baseline and uplift
    # shape.  Multiplying through the reference PV gives affine numerator and
    # denominator coefficients in lambda, so the binding switch is exact.
    ref0=metric(x['reference_base'],rr,s,e);uplift=metrics(addition_shape,rr,e,s);pay=metrics(shape,rr,e,s)
    delta=oi.duration-orr.duration
    denominator=(
        (delta*ref0.pv+ref0.moment)*pay.pv-pay.moment*ref0.pv,
        (delta*uplift.pv+uplift.moment)*pay.pv-pay.moment*uplift.pv,
    )
    numerator=(
        base.moment*ref0.pv-(delta*ref0.pv+ref0.moment)*base.pv,
        base.moment*uplift.pv-(delta*uplift.pv+uplift.moment)*base.pv,
    )
    duration_cap=lambda lam:(numerator[0]+numerator[1]*lam)/(denominator[0]+denominator[1]*lam)
    require(denominator[0]+denominator[1]*parameter_lower>0 and denominator[0]+denominator[1]*parameter_upper>0,
        'Duration-cap denominator must stay positive on the declared parameter range')
    triggered=next(b for b in family if b['reachable'] and b['active']['g'])
    programme_cap=next(b/a for name,a,b in triggered['rows'] if name=='programme')
    switch_denominator=numerator[1]-programme_cap*denominator[1]
    require(switch_denominator!=0,'Duration and programme caps do not have an isolated switch')
    switch=(programme_cap*denominator[0]-numerator[0])/switch_denominator
    require(parameter_lower<=switch<parameter_upper and duration_cap(switch)==programme_cap,
        'Derived family switch lies outside the declared range or fails equality')
    require(duration_cap(parameter)==next(b/a for name,a,b in triggered['rows'] if name=='duration'),
        'Parameterised duration family disagrees with the implemented triggered branch')
    out['nonproportional_oblique_family']={
        'branches':family,
        'old_candidate':oi,
        'old_reference':orr,
        'duration_cap_family':{
            'variable':'lambda',
            'numerator_affine_ascending':numerator,
            'denominator_affine_ascending':denominator,
            'valid_parameter_range':{'lower_inclusive':parameter_lower,'upper_exclusive':parameter_upper},
        },
        'binding_switch_parameter':switch,
        'implemented_robust_cap':min(caps.values()),
    }
    return out

def envelope(data):
    h=bindings();result=jsonable(calculate(data))
    def bind(o):
        if isinstance(o,dict):
            if 'certificate' in o:
                o['input_sha256']=h['data/contracts.json'];o['calculation_version']=VERSION
                o['calculation_sha256']=hashlib.sha256(json.dumps(h,sort_keys=True).encode()).hexdigest()
            for v in list(o.values()): bind(v)
        elif isinstance(o,list):
            for v in o: bind(v)
    bind(result)
    return {'format':'exact-comparability-v2','bindings':h,'results':result}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');args=ap.parse_args()
    if not args.write:
        require(json.loads((ROOT/'input-lock.json').read_text())==bindings(),'Input or calculation integrity failure')
    data=json.loads((ROOT/'data/contracts.json').read_text());calculated=envelope(data)
    target=ROOT/'results/certificates.json'
    if args.write:
        target.write_text(json.dumps(calculated,indent=2,sort_keys=True)+'\n')
        (ROOT/'input-lock.json').write_text(json.dumps(calculated['bindings'],indent=2,sort_keys=True)+'\n')
        print('Generated input-bound certificates and input lock.')
    else:
        require(json.loads((ROOT/'input-lock.json').read_text())==bindings(),'Input or calculation integrity failure')
        require(json.loads(target.read_text())==calculated,'Certificate replay mismatch')
        print('PASS: exact certificate replay; all consumed inputs and calculation files match their hashes.')
    m=calculated['results']['multi_regime']['branches']
    print(f"Reachable multi-regime cells: {sum(b['reachable'] for b in m)}/8; repaired policy passes: {all(b['implemented_audit']['passes'] for b in m if b['reachable'])}")

if __name__=='__main__': main()
