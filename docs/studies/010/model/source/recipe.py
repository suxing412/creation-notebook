"""SLOT 010. Units metres. Finite input contract, not manufacturing assurance."""
import math
VERSION='1.1.0'
KEYS={'name','length','depth','divider_height','dividers','thickness','rail_height','clearance'}
def validate(c):
 if set(c)!=KEYS:raise ValueError('Exact keys required')
 if c['name'] not in ['slot','span','rise','test']:raise ValueError('Unknown preset name')
 if type(c['dividers']) is not int or not 3<=c['dividers']<=6:raise ValueError('dividers 3..6 integer')
 for k in KEYS-{'name','dividers'}:
  if type(c[k]) not in (int,float) or not math.isfinite(c[k]):raise ValueError('finite numeric inputs')
 for k,lo,hi in [('length',.25,.48),('depth',.12,.23),('divider_height',.10,.19),('thickness',.006,.012),('rail_height',.05,.08),('clearance',.0004,.0012)]:
  if not lo<=c[k]<=hi:raise ValueError(k+' outside permitted input envelope')
 if c['divider_height']<c['rail_height']+.035:raise ValueError('divider shoulder too low')
 if c['length']/(c['dividers']+1)<c['thickness']*4:raise ValueError('ligament too narrow')
 return dict(c)
def stations(c):return [-c['length']/2+c['length']*(i+1)/(c['dividers']+1) for i in range(c['dividers'])]
def rail_profile(c,revision=1):
 L=c['length'];H=c['rail_height'];w=c['thickness']+c['clearance'];mid=H/2
 # CCW in x,z. Top slots are traversed right to left.
 p=[(-L/2,0),(L/2,0),(L/2,H)]
 for x in reversed(stations(c)):p += [(x+w/2,H),(x+w/2,mid),(x-w/2,mid),(x-w/2,H)]
 p.append((-L/2,H));return p

def divider_profile(c,revision=1):
 D=c['depth'];H=c['divider_height'];T=c['thickness'];w=T+c['clearance'];mid=c['rail_height']/2
 # bottom-open slots, then softly curved top shoulders in revision 2
 p=[(-D/2-.018,0)]
 for y in [-D/2,D/2]:p += [(y-w/2,0),(y-w/2,mid+c['clearance']),(y+w/2,mid+c['clearance']),(y+w/2,0)]
 p += [(D/2+.018,0)]
 if revision==1:p += [(D/2+.018,H),(-D/2-.018,H)]
 else:
  R=.018;right=D/2+.018;left=-right
  p +=[(right,H-R)]
  for i in range(1,13):
   a=i/12*math.pi/2;p.append((right-R+R*math.cos(a),H-R+R*math.sin(a)))
  p +=[(left+R,H)]
  for i in range(1,13):
   a=math.pi/2+i/12*math.pi/2;p.append((left+R+R*math.cos(a),H-R+R*math.sin(a)))
 return p
