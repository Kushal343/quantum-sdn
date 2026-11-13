"""Explicit random bases, Aer outcomes and basis-independent erasure."""
import numpy as np
from .quantum import BB84Engine


def prepare(n,k,seed=42,noise=.005,detection=1.,eve_fraction=0):
    if n<=0 or k<=0 or not 0<detection<=1 or not 0<=noise<=.5 or not 0<=eve_fraction<=1:
        raise ValueError('Invalid channel or quota')
    rng=np.random.default_rng(seed);px=1/(1+np.sqrt(k/n))
    count=int(1.3*max(n/(px*px),k/((1-px)**2))/detection)+100
    if count>1000000: raise ValueError('Demonstration pulse limit exceeded')
    a=rng.integers(0,2,count);ab=(rng.random(count)>=px).astype(int);bb=(rng.random(count)>=px).astype(int)
    detected=rng.random(count)<detection
    # Stop at the first prefix satisfying both publicly observable quotas.
    x=np.cumsum(detected&(ab==0)&(bb==0));z=np.cumsum(detected&(ab==1)&(bb==1))
    valid=np.flatnonzero((x>=n)&(z>=k))
    if not len(valid): raise RuntimeError('Insufficient detections within pulse cap')
    count=int(valid[0])+1;a=a[:count];ab=ab[:count];bb=bb[:count];detected=detected[:count]
    eve=rng.random(count)<eve_fraction;eb=rng.integers(0,2,count)
    engine=BB84Engine(seed);circuits=[];groups=[]
    for bit in [0,1]:
        for basis in [0,1]:
            for measured in [0,1]:
                for e in [None,0,1]:
                    mask=detected&(a==bit)&(ab==basis)&(bb==measured)
                    mask &= ~eve if e is None else eve&(eb==e)
                    ids=np.flatnonzero(mask)
                    if len(ids):
                        circuits.append(engine.circuit(bit,basis,measured,noise,e));groups.append(ids)
    shots=max(map(len,groups));result=engine.backend.run(circuits,shots=shots,memory=True,seed_simulator=seed).result()
    b=np.full(count,-1,dtype=int)
    for i,ids in enumerate(groups):b[ids]=[int(s.replace(' ','')[0]) for s in result.get_memory(i)[:len(ids)]]
    # X/Z labels can be exchanged globally; raw basis 0 and test basis 1 are complementary.
    return dict(alice=dict(bits=a.tolist(),bases=ab.tolist()),
                bob=dict(bits=b.tolist(),bases=bb.tolist(),detected=detected.astype(int).tolist()),
                pulses=count,aer_shots=shots*len(circuits),basis_key_probability=px)
