"""One-use polynomial authentication with a fresh field pad per packet.

No key reuse. For a message degree <=D, one substitution attempt has probability
<=D/p under independent uniform field keys. This is a simulation implementation.
"""
import json
import secrets
from math import ceil

PRIME = 2**127-1
MAX_BYTES = 262144
MAX_DEGREE = 1+ceil(MAX_BYTES/15)


def body(message):
    return json.dumps(message,sort_keys=True,separators=(',',':')).encode()


def polynomial(data, point, prime=PRIME):
    if len(data)>MAX_BYTES: raise ValueError('Message size cap exceeded')
    coefficients=[len(data)]+[int.from_bytes(data[i:i+15].ljust(15,b'\0'),'big') for i in range(0,len(data),15)]
    value=0
    for c in reversed(coefficients): value=(value*point+c)%prime
    return value*point%prime # all message-dependent terms have positive degree


class OneUseAuthenticator:
    def __init__(self, key, session, sender):
        self.point,self.pad=key
        if not all(0<=x<PRIME for x in key): raise ValueError('Invalid field key')
        self.session,self.sender=session,sender
        self.signed=self.checked=False

    @staticmethod
    def new_key(): return secrets.randbelow(PRIME),secrets.randbelow(PRIME)

    def sign(self,kind,payload):
        if self.signed: raise ValueError('Authentication key already used')
        self.signed=True
        message=dict(session=self.session,sender=self.sender,sequence=0,kind=kind,payload=payload)
        return message,(polynomial(body(message),self.point)+self.pad)%PRIME

    def receive(self,packet):
        if self.checked: raise ValueError('Replay or repeated authentication attempt')
        self.checked=True
        try:
            message,tag=packet
            if (message['session']!=self.session or message['sender']!=self.sender or message['sequence']!=0
                or type(tag) is not int or not 0<=tag<PRIME
                or tag!=(polynomial(body(message),self.point)+self.pad)%PRIME):
                raise ValueError('Authentication failed')
            return message
        except (KeyError,TypeError,IndexError) as e:
            raise ValueError('Malformed authenticated packet') from e


def authentication_budget(messages):
    return dict(authentication_failure_bound=messages*MAX_DEGREE/PRIME,
                authentication_secret_bits=messages*254,
                max_authenticated_bytes=MAX_BYTES,
                assumption='Fresh independent uniform field key and pad, one attempt per packet; no reuse')
