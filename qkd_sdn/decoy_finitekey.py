"""Lim et al. arXiv:1311.7129v1 equations (1)-(5), three-intensity bounds.

Inputs are X/Z detections by intensity, with ALL X intensities forming raw key.
The existing pooled-basis, signal-only telemetry is deliberately incompatible.
"""
from math import exp,log,log2,sqrt,floor,isfinite
from .physics import entropy


def budget(nx,nz,mz,leak_ec,intensities=(.6,.12,0.),probabilities=(.75,.20,.05),
           eps_sec=1e-9,eps_cor=1e-12,phase_tolerance=.11):
    arrays=(nx,nz,mz)
    if any(len(v)!=3 for v in arrays) or len(intensities)!=3 or len(probabilities)!=3:
        raise ValueError('Require three intensity-resolved counts for each basis')
    if any(type(x) is not int or x<0 for v in arrays for x in v):
        raise ValueError('Counts must be nonnegative integers')
    if any(e>n for e,n in zip(mz,nz)):raise ValueError('Errors exceed detections')
    mu,nu,omega=intensities;p=probabilities
    if (not all(isfinite(x) for x in (*intensities,*p,leak_ec,eps_sec,eps_cor,phase_tolerance))
        or not mu>nu+omega or not nu>omega>=0 or any(x<=0 for x in p)
        or abs(sum(p)-1)>1e-12 or leak_ec<0 or not 0<eps_sec<1
        or not 0<eps_cor<1 or not 0<phase_tolerance<.5):
        raise ValueError('Invalid protocol parameters')
    tau0=sum(q*exp(-a) for a,q in zip(intensities,p))
    tau1=sum(q*a*exp(-a) for a,q in zip(intensities,p))
    def intervals(counts):
        delta=sqrt(sum(counts)/2*log(21/eps_sec))
        return ([exp(a)/q*max(0,c-delta) for a,q,c in zip(intensities,p,counts)],
                [exp(a)/q*(c+delta) for a,q,c in zip(intensities,p,counts)])
    def yields(counts):
        lower,upper=intervals(counts)
        s0=max(0.,tau0*(nu*lower[2]-omega*upper[1])/(nu-omega))
        s1=max(0.,tau1*mu*(lower[1]-upper[2]-(nu**2-omega**2)/mu**2*(upper[0]-s0/tau0))
               /(mu*(nu-omega)-nu**2+omega**2))
        return s0,s1
    x0,x1=yields(nx);z0,z1=yields(nz)
    lower,upper=intervals(mz)
    v1=max(0.,tau1*(upper[1]-lower[2])/(nu-omega))
    result=dict(raw_bits=sum(nx),test_bits=sum(nz),vacuum_lower=x0,single_x_lower=x1,
                single_z_lower=z1,single_z_errors_upper=v1,leak_ec_bits=leak_ec,
                epsilon_secrecy=eps_sec,epsilon_correctness=eps_cor,
                epsilon_qkd=eps_sec+eps_cor,phase_upper=None,length=0,
                status='insufficient_statistics',source='arXiv:1311.7129v1 Eqs 1-5',
                raw_key_definition='all three intensities in X basis')
    if x0+x1>sum(nx) or z0+z1>sum(nz):
        result['status']='inconsistent_bounds';return result
    if x1<=0 or z1<=0:return result
    b=v1/z1
    # Singular/domain cases fail closed; never clip an unsafe rate downward.
    if not 0<b<.5:
        result['status']='phase_bound_unavailable';return result
    argument=(z1+x1)/(z1*x1*(1-b)*b)*(21/eps_sec)**2
    if argument<=1:return result
    gamma=sqrt((z1+x1)*(1-b)*b/(z1*x1*log(2))*log2(argument))
    phase=b+gamma;result['phase_upper']=phase
    if phase>=phase_tolerance:
        result['status']='phase_abort';return result
    penalty=6*log2(21/eps_sec)+log2(2/eps_cor)
    result['finite_penalty_bits']=penalty
    length=max(0,floor(x0+x1*(1-entropy(phase))-leak_ec-penalty))
    result.update(length=length,status='positive_bound' if length else 'no_positive_length')
    return result
