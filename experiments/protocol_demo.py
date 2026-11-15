"""Aer basis/sifting plus separate authenticated classical participants."""
import hashlib,json,multiprocessing as mp,secrets
from math import ceil,log2
from pathlib import Path
import numpy as np
from qkd_sdn.asymmetric import prepare
from qkd_sdn.authentication import OneUseAuthenticator,authentication_budget
from qkd_sdn.finitekey import key_budget
from qkd_sdn.reconciliation import graph,syndrome,decode
from qkd_sdn.postprocessing import toeplitz


def participant(role,conn,private,n,k,keys,session,selection_seed,fault,output):
    sent=received=0
    peer='bob' if role=='alice' else 'alice'
    def send(kind,payload):
        nonlocal sent
        packet=OneUseAuthenticator(keys[role][sent],session+str(sent),role).sign(kind,payload)
        if fault=='tamper' and role=='alice' and sent==2:packet[0]['payload']['syndrome'][0]^=1
        sent+=1;conn.send(packet)
    def receive():
        nonlocal received
        if not conn.poll(60):raise TimeoutError('Peer timeout')
        message=OneUseAuthenticator(keys[peer][received],session+str(received),peer).receive(conn.recv())
        received+=1
        return message['payload']
    try:
        own=dict(bases=private['bases'])
        if role=='bob':own['detected']=private['detected']
        if role=='alice':send('bases',own);other=receive()
        else:other=receive();send('bases',own)
        detected=np.array(other['detected'] if role=='alice' else own['detected'],dtype=bool)
        a,b=np.array(own['bases']),np.array(other['bases'])
        x=np.flatnonzero(detected&(a==0)&(b==0));z=np.flatnonzero(detected&(a==1)&(b==1))
        rng=np.random.default_rng(selection_seed)
        xi=rng.choice(x,n,replace=False);zi=rng.choice(z,k,replace=False)
        raw=np.array(private['bits'])[xi];test=np.array(private['bits'])[zi]
        if role=='alice':send('test',dict(bits=test.tolist()));errors=receive()['errors']
        else:
            revealed=receive()['bits'];errors=int(np.count_nonzero(test!=revealed));send('test_result',dict(errors=errors))
        budget=key_budget(n,k,errors,n//3+1+ceil(log2(k+1)))
        budget['authentication']='one-use polynomial field authentication; see run-level budget'
        if not budget['length']:
            output.put((role,dict(accepted=False,status='parameter_or_length_abort',budget=budget)));return
        g=graph(n,n//3)
        def random_bits(size):
            return np.unpackbits(np.frombuffer(secrets.token_bytes((size+7)//8),dtype=np.uint8))[:size].astype(int)
        if role=='alice':
            vs=random_bits(n+budget['verification_bits']-1);ps=random_bits(n+budget['length']-1)
            send('reconciliation',dict(syndrome=syndrome(raw,g,n//3).tolist(),vs=vs.tolist(),
                tag=toeplitz(raw,vs,budget['verification_bits']).tolist(),ps=ps.tolist()))
            accepted=receive()['verified'];corrected=raw
        else:
            data=receive();corrected,it=decode(raw,np.array(data['syndrome']),g,n//3)
            accepted=bool(np.array_equal(toeplitz(corrected,data['vs'],budget['verification_bits']),data['tag']))
            ps=data['ps'];send('verified',dict(verified=accepted))
        candidate=toeplitz(corrected,ps,budget['length']) if accepted else np.array([],dtype=int)
        output.put((role,dict(accepted=accepted,length=len(candidate),budget=budget,
            fingerprint=hashlib.sha256(candidate.astype('uint8').tobytes()).hexdigest())))
    except (ValueError,KeyError,TypeError,EOFError,TimeoutError) as e:
        output.put((role,dict(accepted=False,error=str(e))))
    finally:conn.close()


def run(n=8192,k=8192,noise=.005,seed=42,fault=None,eve=0):
    quantum=prepare(n,k,seed,noise,eve_fraction=eve)
    keys={role:[OneUseAuthenticator.new_key() for _ in range(3)] for role in ['alice','bob']}
    session=secrets.token_hex(16);selection=secrets.randbits(128)
    left,right=mp.Pipe();out=mp.Queue()
    ps=[mp.Process(target=participant,args=(role,conn,quantum[role],n,k,keys,session,selection,fault,out))
        for role,conn in [('alice',left),('bob',right)]]
    answers={}
    try:
        for p in ps:p.start()
        left.close();right.close()
        answers=dict(out.get(timeout=90) for _ in ps)
    finally:
        for p in ps:
            p.join(2)
            if p.is_alive():p.terminate();p.join()
    matched=all(v.get('accepted') for v in answers.values()) and answers['alice']['fingerprint']==answers['bob']['fingerprint']
    for v in answers.values():v.pop('fingerprint',None)
    auth=authentication_budget(6)
    length=answers['alice'].get('length',0) if matched else 0
    return dict(participants=answers,keys_match=bool(matched),gross_bits=length,
        net_bits_after_authentication=length-auth['authentication_secret_bits'],
        authentication=auth,epsilon_total_bound=1e-9+1e-12+auth['authentication_failure_bound'],
        pulses=quantum['pulses'],aer_shots=quantum['aer_shots'],
        scope='Ideal single-photon protocol simulation; theorem mapping requires independent review; excludes decoy source')


if __name__=='__main__':
    out=Path('results/protocol');out.mkdir(parents=True,exist_ok=True)
    result=run();(out/'summary.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
