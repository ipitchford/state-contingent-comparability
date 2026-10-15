#!/usr/bin/env python3
"""Separate exact checker: no imports from the producer or optimisation kernel.

Checks 1D/2D polynomial minima by interval/edge calculus and direct 2x2 solves.
It checks each financial polynomial against directly summed cash-flow moments.
This is a separate implementation within the same development effort, not an
external independent reproduction or proof-assistant certification.
"""
from fractions import Fraction as F
from itertools import combinations, product
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def require(p,m):
    if not p: raise ValueError(m)
def dot(a,b): return sum((x*y for x,y in zip(a,b)),F(0))
def val(q,x):
    return F(q['constant'])+dot(list(map(F,q['linear'])),x)+sum((x[i]*F(q['Q'][i][j])*x[j] for i in range(len(x)) for j in range(len(x))),F(0))
def affine(a,x): return F(a[0])+dot(list(map(F,a[1:])),x)

def domain(lower,upper,A=(),b=()):
    return {'lower':list(map(F,lower)),'upper':list(map(F,upper)),
            'A':[list(map(F,row)) for row in A],'b':list(map(F,b))}

def same_domain(got,want):
    return (list(map(F,got['lower']))==want['lower'] and
            list(map(F,got['upper']))==want['upper'] and
            [list(map(F,row)) for row in got['A']]==want['A'] and
            list(map(F,got['b']))==want['b'])

def domain_vertices(d):
    lo,hi=d['lower'],d['upper'];n=len(lo);A=[row[:] for row in d['A']];b=d['b'][:]
    for i in range(n):
        e=[F(0)]*n;e[i]=1;A.append(e);b.append(hi[i]);A.append([-v for v in e]);b.append(-lo[i])
    out=set()
    for J in combinations(range(len(A)),n):
        if n==1:
            if not A[J[0]][0]: continue
            x=(b[J[0]]/A[J[0]][0],)
        else:
            a,c=A[J[0]],A[J[1]];det=a[0]*c[1]-a[1]*c[0]
            if not det: continue
            x=((b[J[0]]*c[1]-a[1]*b[J[1]])/det,
               (a[0]*b[J[1]]-b[J[0]]*c[0])/det)
        if all(dot(row,x)<=rhs for row,rhs in zip(A,b)): out.add(x)
    return sorted(out)

def independent_regimes(spec):
    lo,hi=list(map(F,spec['lower'])),list(map(F,spec['upper']))
    out=[]
    for bits in product([False,True],repeat=len(spec['triggers'])):
        A=[];b=[];strict=[];active={}
        for flag,t in zip(bits,spec['triggers']):
            require(t['true_operator']=='>=' and t['false_operator']=='<','Unsupported trigger boundary convention')
            a=list(map(F,t['coefficients']));h=F(t['threshold']);active[t['id']]=flag
            A.append([-v for v in a] if flag else a);b.append(-h if flag else h)
            if not flag: strict.append(len(A)-1)
        d=domain(lo,hi,A,b);vv=domain_vertices(d)
        centre=tuple(sum(v[i] for v in vv)/len(vv) for i in range(len(lo))) if vv else None
        reachable=centre is not None and all(dot(A[j],centre)<b[j] for j in strict)
        out.append({'id':''.join(str(int(v)) for v in bits),'active':active,'domain':d,'reachable':reachable})
    return out

def plain_metrics(stream,r,start,end):
    cash={int(t):F(v) for t,v in stream.items()}
    V=sum((v/(1+r)**t for t,v in cash.items()),F(0));M=sum((t*v/(1+r)**t for t,v in cash.items()),F(0))
    S=sum((v for t,v in cash.items() if start<=t<=end),F(0))
    require(V>0,'Nonpositive present value in independent scalar check')
    return V,M,M/V,S

def plain_rows(old_i,old_r,base,reference,shape,r,start,end):
    Oi,_,Di,Si=plain_metrics(old_i,r,start,end);Or,_,Dr,Sr=plain_metrics(old_r,r,start,end)
    Vb,Mb,_,Sb=plain_metrics(base,r,start,end);Vr,_,Dref,Sref=plain_metrics(reference,r,start,end)
    v,m,_,s=plain_metrics(shape,r,start,end);target=Di+Dref-Dr
    return [('NPV',v,Oi*Vr/Or-Vb),('programme',s,Si*Sref/Sr-Sb),('duration',target*v-m,Mb-target*Vb)]

def interval_from_rows(rows,upper):
    lo=F(0);hi=F(upper)
    for _,a,b in rows:
        if a>0: hi=min(hi,b/a)
        elif a<0: lo=max(lo,b/a)
        else: require(b>=0,'Inconsistent scalar row')
    require(lo<=hi,'Empty scalar interval')
    return lo,hi

def polyminimum(q,d):
    lo,hi=list(map(F,d['lower'])),list(map(F,d['upper']));n=len(lo)
    A=[list(map(F,r)) for r in d['A']];b=list(map(F,d['b']))
    for i in range(n):
        e=[F(0)]*n;e[i]=1;A.append(e);b.append(hi[i]);A.append([-t for t in e]);b.append(-lo[i])
    feasible=lambda x:all(dot(a,x)<=v for a,v in zip(A,b))
    if n==1:
        for a,v in zip(A,b):
            if a[0]>0: hi[0]=min(hi[0],v/a[0])
            elif a[0]<0: lo[0]=max(lo[0],v/a[0])
            else: require(v>=0,'Empty interval')
        require(lo[0]<=hi[0],'Empty interval');pts=[tuple(lo),tuple(hi)]
        a=F(q['Q'][0][0]);l=F(q['linear'][0])
        if a>0 and lo[0]<=-l/(2*a)<=hi[0]: pts.append((-l/(2*a),))
    elif n==2:
        vv=set()
        for i,j in combinations(range(len(A)),2):
            a,c=A[i],A[j];det=a[0]*c[1]-a[1]*c[0]
            if det:
                x=((b[i]*c[1]-a[1]*b[j])/det,(a[0]*b[j]-b[i]*c[0])/det)
                if feasible(x): vv.add(x)
        require(bool(vv),'Empty polygon');pts=list(vv)
        # Restrict to every boundary segment; sample at 0, 1 and 1/2 to recover
        # its scalar quadratic without using the producer's Hessian algebra.
        for a,rhs in zip(A,b):
            edge=[x for x in vv if dot(a,x)==rhs]
            for u,v in combinations(edge,2):
                midpoint=tuple((x+y)/2 for x,y in zip(u,v))
                c0,c1,ch=val(q,u),val(q,v),val(q,midpoint)
                aa=2*(c1+c0-2*ch);bb=c1-c0-aa
                if aa>0 and 0<-bb/(2*aa)<1:
                    s=-bb/(2*aa);pts.append(tuple(x+s*(y-x) for x,y in zip(u,v)))
        a,c=F(q['Q'][0][0]),F(q['Q'][1][1]);bq=F(q['Q'][0][1]);l0,l1=map(F,q['linear']);det=a*c-bq*bq
        if det:
            x=((bq*l1-c*l0)/(2*det),(bq*l0-a*l1)/(2*det))
            if feasible(x): pts.append(x)
        # With singular Hessian any interior stationary flat reaches a boundary;
        # its constant value is therefore already represented.
    else: raise ValueError('Checker covers only one and two state dimensions')
    return min(val(q,x) for x in pts),feasible

def financial(old_i,old_r,ci,cr,r,start,end,x):
    def moments(s,aff=False):
        c={int(t):(affine(v,x) if aff else F(v)) for t,v in s.items()}
        V=sum((v/(1+r)**t for t,v in c.items()),F(0));M=sum((t*v/(1+r)**t for t,v in c.items()),F(0));S=sum((v for t,v in c.items() if start<=t<=end),F(0))
        return V,M,S
    Oi,Mi0,Si0=moments(old_i);Or,Mr0,Sr0=moments(old_r)
    Vi,Mi,Si=moments(ci,True);Vr,Mr,Sr=moments(cr,True)
    return {'present_value':Oi*Vr/Or-Vi,'programme_service':Si0*Sr/Sr0-Si,'duration':Mi*Vr-Mr*Vi-(Mi0/Oi-Mr0/Or)*Vi*Vr}

def main():
    env=json.loads((ROOT/'results/certificates.json').read_text());data=json.loads((ROOT/'data/contracts.json').read_text());cert=env['results']
    for name,expected in env['bindings'].items(): require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,'Certificate input or code hash mismatch')
    digest=hashlib.sha256(json.dumps(env['bindings'],sort_keys=True).encode()).hexdigest()
    jobs=[];r=F(data['default_rate']);x=data['interior_failure']
    lo,hi=map(F,x['state_domain'])
    jobs.append((cert['interior_failure'],domain([lo],[hi]),x['old'],x['old'],x['candidate_affine'],x['reference_affine'],r,x['programme_start'],x['programme_end']))
    x=data['mixed_triggers']
    lo,hi=map(F,x['state_domain']);a,b=F(x['candidate_threshold']),F(x['reference_threshold'])
    mixed_domains=[domain([lo],[a]),domain([a],[b]),domain([b],[hi])]
    for rec,want,(ck,rk) in zip(cert['mixed_triggers'],mixed_domains,[('candidate_base','reference_base'),('candidate_enhanced','reference_base'),('candidate_enhanced','reference_enhanced')]):
        ci={t:[v,'0'] for t,v in x[ck].items()};cr={t:[v,'0'] for t,v in x[rk].items()}
        jobs.append((rec['audit'],want,x['old'],x['old'],ci,cr,r,x['programme_start'],x['programme_end']))
    x=data['multi_regime'];r=F(x['rate'])
    expected_branches=independent_regimes(x);shipped=cert['multi_regime']['branches']
    require(len(shipped)==len(expected_branches),'Wrong trigger branch count')
    for got,want in zip(shipped,expected_branches):
        require(got['id']==want['id'] and got['active']==want['active'] and got['reachable']==want['reachable'],'Trigger inventory or reachability mismatch')
        require([list(map(F,row)) for row in got['A']]==want['domain']['A'] and list(map(F,got['b']))==want['domain']['b'],'Trigger region mismatch')
    require([b['id'] for b in expected_branches if b['reachable']]==['000','010','011','100','101','111'],'Unexpected independently reconstructed branch inventory')
    for b,want in zip(shipped,expected_branches):
        if not want['reachable']: continue
        flags=want['active'];alpha=F(x['candidate_late_scale']['base'])+sum((F(v) for k,v in x['candidate_late_scale'].items() if k!='base' and flags[k]),F(0))
        cr={t:list(map(F,a)) for t,a in x['reference_affine'].items()}
        for key,delta in x['reference_trigger_additions'].items():
            if flags[key]:
                for t,a in delta.items():cr[t]=[v+F(w) for v,w in zip(cr[t],a)]
        for policy in ['implemented','raw']:
            ci={t:[alpha*v for v in a] for t,a in cr.items()};t=str(x['payment_date'])
            if policy=='implemented':
                pp=x['implemented_payment'];pay=[F(pp['base'])+sum((F(v) for k,v in pp.items() if k!='base' and flags[k]),F(0)),F(0),F(0)]
            else: pay=list(map(F,x['raw_payment_affine']))
            ci[t]=pay[:];ci[t][0]+=F(x['candidate_early_base'])
            jobs.append((b[policy+'_audit'],want['domain'],x['old_candidate'],x['old_reference'],ci,cr,r,x['programme_start'],x['programme_end']))

    # Independently reconstruct the added scalar family and its oblique regions.
    x=data['nonproportional_oblique_family'];r=F(x['rate']);expected_family=independent_regimes(x)
    parameter=F(x['late_uplift_parameter']);parameter_lower,parameter_upper=map(F,x['late_uplift_parameter_range'])
    require(parameter_lower<=parameter<parameter_upper,'Late-uplift parameter lies outside its declared half-open range')
    addition_shape={t:F(v) for t,v in x['reference_trigger_addition_shape'].items()}
    require(addition_shape and all(v>=0 for v in addition_shape.values()) and any(v>0 for v in addition_shape.values()),'Invalid independent uplift shape')
    def reference_at(lam):
        reference={t:F(v) for t,v in x['reference_base'].items()}
        for t,v in addition_shape.items(): reference[t]=reference.get(t,F(0))+lam*v
        return reference
    shipped_family=cert['nonproportional_oblique_family']['branches'];scalar_checked=0
    require(len(shipped_family)==len(expected_family),'Wrong strengthening-family branch count')
    for got,want in zip(shipped_family,expected_family):
        require(got['id']==want['id'] and got['active']==want['active'] and got['reachable']==want['reachable'],'Strengthening-family trigger mismatch')
        require([list(map(F,row)) for row in got['A']]==want['domain']['A'] and list(map(F,got['b']))==want['domain']['b'],'Strengthening-family region mismatch')
        if not want['reachable']: continue
        reference=reference_at(parameter) if want['active']['g'] else {t:F(v) for t,v in x['reference_base'].items()}
        rows=plain_rows(x['old_candidate'],x['old_reference'],x['candidate_base'],reference,x['payment_shape'],r,x['programme_start'],x['programme_end'])
        got_rows=[(row[0],F(row[1]),F(row[2])) for row in got['rows']]
        require(got_rows==rows,'Strengthening-family scalar rows mismatch')
        expected_interval=interval_from_rows(rows,F(x['raw_payment_upper']))
        require(tuple(map(F,got['interval'][:2]))==expected_interval,'Strengthening-family interval mismatch')
        positive={name:b/a for name,a,b in rows if a>0}
        require(got['binding_constraint']==min(positive,key=positive.get),'Strengthening-family binding label mismatch')
        scalar_checked+=1
    family_certificate=cert['nonproportional_oblique_family'];formula=family_certificate['duration_cap_family']
    require(formula['variable']=='lambda','Wrong duration-family variable')
    require(F(formula['valid_parameter_range']['lower_inclusive'])==parameter_lower and F(formula['valid_parameter_range']['upper_exclusive'])==parameter_upper,
        'Duration-family range is not bound to the source declaration')
    programme_rows=plain_rows(x['old_candidate'],x['old_reference'],x['candidate_base'],reference_at(parameter),x['payment_shape'],r,x['programme_start'],x['programme_end'])
    programme_cap=next(b/a for name,a,b in programme_rows if name=='programme')
    def gap_numerator(lam):
        reference=reference_at(lam);rows=plain_rows(x['old_candidate'],x['old_reference'],x['candidate_base'],reference,x['payment_shape'],r,x['programme_start'],x['programme_end'])
        # Recompute the cross-multiplied gap without trusting the producer's
        # affine coefficients. plain_rows has a common reference-PV denominator.
        reference_pv=plain_metrics(reference,r,x['programme_start'],x['programme_end'])[0]
        a,b=next((a,b) for name,a,b in rows if name=='duration')
        return (b-programme_cap*a)*reference_pv
    require(parameter_upper-parameter_lower>1,'Independent switch reconstruction needs two distinct interior probes')
    g0=gap_numerator(parameter_lower);g1=gap_numerator(parameter_lower+1);slope=g1-g0
    require(slope!=0,'Independent duration/programme gap has no isolated switch')
    switch=parameter_lower-g0/slope
    require(parameter_lower<=switch<parameter_upper and gap_numerator(switch)==0,'Independently reconstructed switch is invalid')
    require(F(family_certificate['binding_switch_parameter'])==switch,'Incorrect strengthening-family switch point')
    n0,n1=map(F,formula['numerator_affine_ascending']);d0,d1=map(F,formula['denominator_affine_ascending'])
    for probe in [parameter_lower,parameter,switch,(parameter_lower+parameter_upper)/2]:
        rows=plain_rows(x['old_candidate'],x['old_reference'],x['candidate_base'],reference_at(probe),x['payment_shape'],r,x['programme_start'],x['programme_end'])
        direct=next(b/a for name,a,b in rows if name=='duration')
        require(d0+d1*probe!=0 and (n0+n1*probe)/(d0+d1*probe)==direct,'Duration-family formula disagrees with independent cash-flow reconstruction')
    require(F(family_certificate['implemented_robust_cap'])==min(F(b['interval'][1]) for b in shipped_family if b['reachable']),
        'Incorrect strengthening-family robust cap')

    checked=0;identities=0;domains=0
    for record,want_domain,oi,orr,ci,cr,r,s,e in jobs:
        require(same_domain(record['domain'],want_domain),'Certificate domain does not match declared model')
        domains+=1
        n=len(record['domain']['lower']);points=[(F(0),),(F(1),),(F(2),)] if n==1 else [(F(0),F(0)),(F(1),F(0)),(F(0),F(1)),(F(1),F(1)),(F(2),F(0)),(F(0),F(2))]
        for name,c in record['constraints'].items():
            require(c['input_sha256']==env['bindings']['data/contracts.json'] and c['calculation_sha256']==digest and c['calculation_version']=='3.0.0','Missing or incorrect certificate binding')
            for pt in points:
                require(val(c['polynomial'],pt)==financial(oi,orr,ci,cr,r,s,e,pt)[name],'Financial polynomial compilation mismatch');identities+=1
            true_min,feasible=polyminimum(c['polynomial'],want_domain);w=c['certificate'];p=tuple(map(F,w['point']))
            require(true_min==F(w['minimum']) and feasible(p) and val(c['polynomial'],p)==true_min,'Minimum or witness mismatch')
            require(c['passes']==(true_min>=0),'Incorrect constraint verdict');checked+=1
        require(record['passes']==all(v['passes'] for v in record['constraints'].values()),'Incorrect combined verdict')
    print(json.dumps({'status':'passed','exact_minima_checked':checked,'unisolvent_financial_identity_evaluations':identities,
        'model_domains_reconstructed':domains,'trigger_regions_reconstructed':len(expected_branches)+len(expected_family),
        'scalar_family_intervals_checked':scalar_checked,
        'scope':'separate 1D/2D implementation; same development effort; no legal authentication'},indent=2))

if __name__=='__main__': main()
