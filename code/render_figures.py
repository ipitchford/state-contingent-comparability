from pathlib import Path
from fractions import Fraction as F
import json,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from verify import bindings
root=Path(__file__).resolve().parents[1];out=root/'figures'
envelope=json.loads((root/'results/certificates.json').read_text())
if envelope['bindings']!=bindings():
 raise ValueError('Figures require current input-bound certificates; verify or explicitly regenerate the model first.')
c=envelope['results'];data=json.loads((root/'data/contracts.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','figure.facecolor':'white','axes.labelcolor':'#253747','text.color':'#253747','savefig.bbox':'tight'})
navy='#17354A';teal='#007F82';orange='#C65D30'
fig,axs=plt.subplots(1,2,figsize=(10.6,3.5),layout='constrained')
interior=data['interior_failure'];x=np.linspace(*map(lambda t:float(F(t)),interior['state_domain']),601);z=1/(1+float(F(data['default_rate'])))
def duration(flow):
 values={int(t):float(F(a[0]))+float(F(a[1]))*x for t,a in flow.items()}
 pv=sum(amount*z**t for t,amount in values.items())
 if np.any(pv<=0):raise ValueError('Nonpositive PV in plotted stream')
 return sum(t*amount*z**t for t,amount in values.items())/pv
dr=duration(interior['reference_affine']);di=duration(interior['candidate_affine'])
axs[0].plot(x,dr,color=navy,label='Reference');axs[0].plot(x,di,color=orange,label='Candidate')
axs[0].fill_between(x,di,dr,color=orange,alpha=.12);axs[0].set(xlabel='Scenario x',ylabel='Discounted duration (years)',title='Less service can mean shorter duration');axs[0].legend(frameon=False)
axs[1].plot(x,dr-di,color=orange);axs[1].axhline(.05,color=teal,linestyle='--',label='Tolerance: 0.05 years');axs[1].set(xlabel='Scenario x',ylabel='Reference minus candidate (years)',title='Endpoint agreement hides interior failure');axs[1].legend(frameon=False)
fig.savefig(out/'duration-conflict.pdf');fig.savefig(out/'duration-conflict.png',dpi=180);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(10.6,3.5),layout='constrained')
weights=[float(F(t['weights'][2])) for t in c['weight_sensitivity']];caps=[float(F(t['maximum_payment_bracket'][0])) for t in c['weight_sensitivity']]
axs[0].plot(weights,caps,'o-',color=teal);axs[0].axhline(float(F(c['cap_example']['interval'][1])),color=navy,linestyle='--',label='Separate zero-tolerance screen');axs[0].set_xscale('symlog',linthresh=.1);axs[0].set(xlabel='Duration weight (per year)',ylabel='Largest payment',title='Trade-off weights change the answer');axs[0].legend(frameon=False,fontsize=8)
tol=[float(F(t['duration_tolerance'])) for t in c['duration_tolerance_sensitivity']];cap=[float(F(t['interval'][1])) for t in c['duration_tolerance_sensitivity']]
axs[1].plot(tol,cap,'o-',color=orange);axs[1].set(xlim=(-.005,.21),ylim=(7.8,10.3),xlabel='Duration tolerance (years)',ylabel='Largest payment',title='Programme service eventually binds');axs[1].axhline(float(F(c['cap_example']['individual_bounds']['programme'])),color=navy,linestyle='--')
fig.savefig(out/'rule-sensitivity.pdf');fig.savefig(out/'rule-sensitivity.png',dpi=180);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(10.6,4.1),layout='constrained')
multi=data['multi_regime'];u,v=np.meshgrid(np.linspace(float(F(multi['lower'][0])),float(F(multi['upper'][0])),401),np.linspace(float(F(multi['lower'][1])),float(F(multi['upper'][1])),401))
active={t['id']:float(F(t['coefficients'][0]))*u+float(F(t['coefficients'][1]))*v>=float(F(t['threshold'])) for t in multi['triggers']}
cap=np.full_like(u,np.nan)
for branch in c['multi_regime']['branches']:
 if not branch['reachable']:continue
 mask=np.ones_like(u,dtype=bool)
 for key,value in branch['active'].items():mask &= active[key]==value
 cap[mask]=float(F(branch['statewise_duration_cap']))
if np.any(np.isnan(cap)):raise ValueError('Uncovered plotted trigger state')
policy=multi['implemented_payment'];info=np.full_like(u,float(F(policy['base'])))
for key,value in policy.items():
 if key!='base':info+=float(F(value))*active[key]
low,high=float(np.min(cap)),float(np.max(cap))
triggers={t['id']:t for t in multi['triggers']}
if list(map(F,triggers['a']['coefficients']))!=[F(1),F(0)] or list(map(F,triggers['b']['coefficients']))!=[F(0),F(1)]:
 raise ValueError('This illustrative quadrant layout requires a=u threshold and b=v threshold')
split_u=float(F(triggers['a']['threshold']));split_v=float(F(triggers['b']['threshold']))
centres_u=[(float(u.min())+split_u)/2,(split_u+float(u.max()))/2]
centres_v=[(float(v.min())+split_v)/2,(split_v+float(v.max()))/2]
for ax,values,title in zip(axs,[cap,info],['If both variables were known','Payment fixed with only u observed']):
 im=ax.pcolormesh(u,v,values,cmap='YlGnBu',vmin=low,vmax=high,shading='auto',rasterized=True);ax.set(xlabel='Observed state u',ylabel='Later state v',title=title,aspect='equal')
 for trigger in multi['triggers']:
  ca,cb=map(lambda t:float(F(t)),trigger['coefficients']);threshold=float(F(trigger['threshold']));colour=orange if trigger['id']=='g' else 'white'
  if cb:
   line_x=np.linspace(u.min(),u.max(),401);line_y=(threshold-ca*line_x)/cb;inside=(line_y>=v.min())&(line_y<=v.max());ax.plot(line_x[inside],line_y[inside],color=colour,lw=1.7 if trigger['id']=='g' else 1)
  elif ca:ax.axvline(threshold/ca,color=colour,lw=1)
 for xx,yy in [(xx,yy) for xx in centres_u for yy in centres_v]:
  ix=int(np.argmin(abs(u[0]-xx)));iy=int(np.argmin(abs(v[:,0]-yy)));val=float(values[iy,ix]);ax.text(xx,yy,f'{val:g}',ha='center',va='center',fontsize=20,color=navy if val<high else 'white',weight='bold')
fig.colorbar(im,ax=axs,shrink=.72,label='Maximum early payment',ticks=sorted(np.unique(cap)));fig.savefig(out/'information-cap.pdf');fig.savefig(out/'information-cap.png',dpi=180);plt.close(fig)
print('Generated three scientific figures as PDF and PNG.')
