"""Separate Alice/Bob processes over authenticated local pipes, reduced channel model."""
import hashlib
import hmac
import json
import multiprocessing as mp
import secrets
from pathlib import Path
import numpy as np
from qkd_sdn.finitekey import key_budget
from qkd_sdn.reconciliation import graph,syndrome,decode
from qkd_sdn.postprocessing import toeplitz


def encode(secret, session, sender, sequence, kind, payload):
    message = dict(session=session,sender=sender,sequence=sequence,kind=kind,payload=payload)
    body = json.dumps(message,sort_keys=True,separators=(',',':')).encode()
    return message,hmac.new(secret,body,hashlib.sha256).hexdigest()


def verify(secret, session, sender, sequence, packet):
    message,tag = packet
    body = json.dumps(message,sort_keys=True,separators=(',',':')).encode()
    if (message['session'] != session or message['sender'] != sender or message['sequence'] != sequence
        or not hmac.compare_digest(tag,hmac.new(secret,body,hashlib.sha256).hexdigest())):
        raise ValueError('Authentication or replay failure')
    return message


def actor(role, conn, key, secret, session, budget, fault):
    try:
        n = len(key); checks = n//3; edges = graph(n,checks)
        rng = np.random.default_rng(secrets.randbits(128))
        if role == 'alice':
            seed_v = rng.integers(0,2,n+budget['verification_bits']-1)
            length = budget['length']; seed_p = rng.integers(0,2,n+length-1)
            payload = dict(syndrome=syndrome(key,edges,checks).tolist(),
                           verify_seed=seed_v.tolist(),tag=toeplitz(key,seed_v,budget['verification_bits']).tolist(),
                           privacy_seed=seed_p.tolist())
            packet = encode(secret,session,'alice',0,'syndrome_and_seeds',payload)
            if fault == 'tamper': packet[0]['payload']['syndrome'][0] ^= 1
            conn.send(packet)
            if not conn.poll(60): raise TimeoutError('Bob timeout')
            response = verify(secret,session,'bob',0,conn.recv())
            ok = response['payload']['verified']
            candidate = toeplitz(key,seed_p,length) if ok else []
        else:
            if not conn.poll(60): raise TimeoutError('Alice timeout')
            payload = verify(secret,session,'alice',0,conn.recv())['payload']
            corrected,_ = decode(key,np.array(payload['syndrome']),edges,checks)
            ok = np.array_equal(toeplitz(corrected,payload['verify_seed'],budget['verification_bits']),payload['tag'])
            conn.send(encode(secret,session,'bob',0,'verification_result',dict(verified=bool(ok))))
            candidate = toeplitz(corrected,payload['privacy_seed'],budget['length']) if ok else []
        # This fingerprint goes only to the trusted test harness, never the wire.
        return dict(accepted=bool(ok),length=len(candidate),fingerprint=hashlib.sha256(bytes(candidate)).hexdigest())
    except (ValueError,TimeoutError,EOFError) as e:
        return dict(accepted=False,error=str(e))
    finally: conn.close()


def worker(*args):
    *actor_args, output = args
    output.put((actor_args[0],actor(*actor_args)))


def run(n=8192,k=8192,noise=.005,seed=42,fault=None):
    rng = np.random.default_rng(seed)
    alice = rng.integers(0,2,n)
    bob = alice ^ (rng.random(n)<noise).astype(int)
    # Reduced post-sifting independent symmetric channel; not a physical source simulation.
    errors = int(rng.binomial(k,noise))
    budget = key_budget(n,k,errors,n//3+1) # syndrome plus Bob's acknowledgement
    if not budget['length']: return dict(budget=budget,status='budget_abort')
    secret, session = secrets.token_bytes(32), secrets.token_hex(16)
    left,right = mp.Pipe(); output = mp.Queue()
    processes = [mp.Process(target=worker,args=(role,conn,key,secret,session,budget,fault,output))
                 for role,conn,key in [('alice',left,alice),('bob',right,bob)]]
    for p in processes: p.start()
    left.close();right.close()
    answers = dict(output.get(timeout=90) for _ in processes)
    for p in processes:
        p.join(5)
        if p.is_alive(): p.terminate();p.join()
    matched = all(a.get('accepted') for a in answers.values()) and answers['alice']['fingerprint']==answers['bob']['fingerprint']
    for a in answers.values(): a.pop('fingerprint',None)
    return dict(budget=budget,participants=answers,keys_match=bool(matched),
                scope='Reduced ideal single-photon model; computational authentication; no decoy proof')


if __name__ == '__main__':
    out=Path('results/distributed');out.mkdir(parents=True,exist_ok=True)
    result=run()
    (out/'summary.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
