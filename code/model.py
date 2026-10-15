"""Exact affine cash-flow compiler and branch audit; integer payment dates only."""
from fractions import Fraction as F
from itertools import product
from exact_audit import metrics, min_quadratic, affine_space, dot

def cf(obj):
    return {int(t):F(v) for t,v in obj.items()}

def affine(obj):
    return {int(t):list(map(F,v)) for t,v in obj.items()}

def val(a,x):
    return a[0]+sum((b*t for b,t in zip(a[1:],x)),F(0))

def at(stream,x):
    return {t:val(a,x) for t,a in stream.items()}

def add(a,b): return [x+y for x,y in zip(a,b)]
def scale(a,s): return [s*x for x in a]
def moments(stream,rate,start,end):
    n=len(next(iter(stream.values())))
    V=M=S=None
    V=[F(0)]*n; M=V[:]; S=V[:]
    for t,a in stream.items():
        if len(a)!=n: raise ValueError('Affine dimension mismatch')
        d=(1+rate)**(-t)
        V=add(V,scale(a,d)); M=add(M,scale(a,t*d))
        if start<=t<=end: S=add(S,a)
    return V,M,S

def mul(a,b):
    n=len(a)-1
    return ([[ (a[i+1]*b[j+1]+a[j+1]*b[i+1])/2 for j in range(n)] for i in range(n)],
            [a[0]*b[i+1]+b[0]*a[i+1] for i in range(n)],a[0]*b[0])

def qsum(*terms):
    n=len(terms[0][1][1]); Q=[[F(0)]*n for _ in range(n)]; l=[F(0)]*n; c=F(0)
    for s,(A,b,d) in terms:
        c+=s*d
        for i in range(n):
            l[i]+=s*b[i]
            for j in range(n): Q[i][j]+=s*A[i][j]
    return Q,l,c

def aq(a):
    n=len(a)-1
    return [[F(0)]*n for _ in range(n)],a[1:],a[0]

def minimum(q,lo,hi,A=(),b=()):
    return min_quadratic(*q,lo,hi,A,b)

def audit(old_i,old_r,ci,cr,rate,start,end,lo,hi,A=(),b=(),tolerances=(F(0),)*3):
    oi,orr=metrics(old_i,rate,end,start),metrics(old_r,rate,end,start)
    if min(oi.programme_service,orr.programme_service)<=0: raise ValueError('Old service denominator not positive')
    Vi,Mi,Si=moments(ci,rate,start,end); Vr,Mr,Sr=moments(cr,rate,start,end)
    ev,es,ed=tolerances
    if min(ev,es,ed)<0: raise ValueError('Negative tolerance')
    domains={}
    for label,stream in [('candidate',ci),('reference',cr)]:
        for t,a in stream.items():
            check=minimum(aq(a),lo,hi,A,b)
            if check.minimum<0: raise ValueError(f'Negative {label} cash flow at date {t}')
    for label,v in [('candidate',Vi),('reference',Vr)]:
        check=minimum(aq(v),lo,hi,A,b)
        if check.minimum<=0: raise ValueError('New PV denominator not strictly positive on closure')
        domains[label]=check.minimum
    pv=add(scale(Vr,oi.pv/orr.pv),scale(Vi,-1));pv[0]+=oi.pv*ev
    ps=add(scale(Sr,oi.programme_service/orr.programme_service),scale(Si,-1));ps[0]+=oi.programme_service*es
    dq=qsum((1,mul(Mi,Vr)),(-1,mul(Mr,Vi)),(-(oi.duration-orr.duration-ed),mul(Vi,Vr)))
    constraints={}
    for label,q in [('present_value',aq(pv)),('programme_service',aq(ps)),('duration',dq)]:
        result=minimum(q,lo,hi,A,b)
        constraints[label]={'polynomial':{'Q':q[0],'linear':q[1],'constant':q[2]},'certificate':result,'passes':result.minimum>=0}
    return {'domain':{'lower':lo,'upper':hi,'A':A,'b':b},'denominator_lower_bounds':domains,
            'old_candidate':oi,'old_reference':orr,'constraints':constraints,
            'passes':all(q['passes'] for q in constraints.values())}

def vertices(lo,hi,A=(),b=()):
    n=len(lo);AA=[];bb=[]
    for i in range(n):
        r=[F(0)]*n;r[i]=-1;AA.append(r);bb.append(-lo[i]);r=r[:];r[i]=1;AA.append(r);bb.append(hi[i])
    AA+=list(A);bb+=list(b)
    from itertools import combinations
    out=set()
    for J in combinations(range(len(AA)),n):
        s=affine_space([AA[j] for j in J],[bb[j] for j in J],n)
        if s and not s[1] and all(dot(a,s[0])<=v for a,v in zip(AA,bb)): out.add(tuple(s[0]))
    return sorted(out)

def regimes(data):
    lo,hi=list(map(F,data['lower'])),list(map(F,data['upper']))
    for bits in product([False,True],repeat=len(data['triggers'])):
        A=[];b=[];strict=[];ids={}
        for active,t in zip(bits,data['triggers']):
            if t['true_operator']!='>=' or t['false_operator']!='<': raise ValueError('Unsupported boundary convention')
            a=list(map(F,t['coefficients']));h=F(t['threshold']);ids[t['id']]=active
            A.append(scale(a,-1) if active else a);b.append(-h if active else h)
            if not active: strict.append(len(A)-1)
        vv=vertices(lo,hi,A,b)
        # Average of all vertices is relative-interior. It detects every strict
        # constraint which is not identically tight, including lower-dimensional cells.
        x=[sum(v[i] for v in vv)/len(vv) for i in range(len(lo))] if vv else None
        reachable=x is not None and all(dot(A[j],x)<b[j] for j in strict)
        yield {'id':''.join(str(int(v)) for v in bits),'active':ids,'A':A,'b':b,'vertices':vv,'reachability_witness':x if reachable else None,'reachable':reachable}

def multi_streams(data,active,policy='implemented'):
    cr=affine(data['reference_affine'])
    for key,delta in data['reference_trigger_additions'].items():
        if active[key]:
            for t,a in affine(delta).items(): cr[t]=add(cr.get(t,[F(0)]*len(a)),a)
    alpha=F(data['candidate_late_scale']['base'])+sum((F(v) for k,v in data['candidate_late_scale'].items() if k!='base' and active[k]),F(0))
    ci={t:scale(a,alpha) for t,a in cr.items()}
    pd=int(data['payment_date']);ci[pd]=[F(data['candidate_early_base']),F(0),F(0)]
    if policy=='implemented':
        pp=data['implemented_payment'];p=F(pp['base'])+sum((F(v) for k,v in pp.items() if k!='base' and active[k]),F(0))
        ci[pd][0]+=p
    elif policy=='raw': ci[pd]=add(ci[pd],list(map(F,data['raw_payment_affine'])))
    elif policy!='base': raise ValueError('Unknown policy')
    return ci,cr,alpha
