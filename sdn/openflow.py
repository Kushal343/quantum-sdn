"""Central OpenFlow 1.3 rule controller via OVS management connections.

No learning-switch fallback: unmatched traffic drops. VLANs represent logical
QKD channel-associated application traffic, never quantum photons themselves.
"""
import subprocess

SWITCHES=('qkds1','qkds2')
TRUNK=10
COOKIE=0x514b4400


class OpenFlowController:
    def __init__(self,runner=None):
        self.runner=runner or subprocess.run
        self.states={i:'active' for i in range(1,5)}
        self.initialized=False
        self.commands=[]

    def command(self,operation,switch,flow=None):
        if switch not in SWITCHES:raise ValueError('Unexpected experiment switch')
        args=['ovs-ofctl','-O','OpenFlow13',operation,switch]
        if flow is not None:args.append(flow)
        result=self.runner(args,check=True,capture_output=True,text=True,timeout=10)
        self.commands.append(args)
        return result.stdout

    def initialize(self):
        if self.initialized:raise RuntimeError('Already initialized')
        # Only experiment-owned cookies are removed; never clear an arbitrary bridge.
        for switch in SWITCHES:
            self.command('del-flows',switch,f'cookie=0x{COOKIE:x}/0xffffff00')
            self.command('add-flow',switch,f'cookie=0x{COOKIE:x},table=0,priority=0,actions=drop')
            for i in range(1,5):
                vlan=100+i
                self.command('add-flow',switch,f'cookie=0x{COOKIE+i:x},table=0,priority=100,in_port={i},dl_vlan=0xffff,actions=mod_vlan_vid:{vlan},output:{TRUNK}')
                self.command('add-flow',switch,f'cookie=0x{COOKIE+i:x},table=0,priority=100,in_port={TRUNK},dl_vlan={vlan},actions=strip_vlan,output:{i}')
            # ovs-ofctl flow modification commands wait on their own barriers.
        self.initialized=True

    def apply(self,channel,action):
        if type(channel) is not int or channel not in self.states:raise ValueError('Invalid channel')
        if action not in ('continue','hold','isolate','isolated','retune','verify','keep','rollback'):
            raise ValueError('Invalid QKD action')
        if not self.initialized:raise RuntimeError('Initialize switches first')
        old=self.states[channel]
        desired='isolated' if old=='isolated' or action in ('isolate','isolated') else 'held' if action=='hold' else 'active'
        if old==desired:return desired
        cookie=COOKIE+0x80+channel
        # Update local state only after BOTH switches acknowledge commands.
        # Failures propagate to the topology owner, which tears down the lab.
        for switch in SWITCHES:
            if desired=='active':
                self.command('del-flows',switch,f'cookie=0x{cookie:x}/0xffffffffffffffff')
            elif old=='active':
                self.command('add-flow',switch,f'cookie=0x{cookie:x},table=0,priority=1000,in_port={channel},actions=drop')
                self.command('add-flow',switch,f'cookie=0x{cookie:x},table=0,priority=1000,in_port={TRUNK},dl_vlan={100+channel},actions=drop')
        self.states[channel]=desired
        return desired

    def snapshot(self):
        return {s:self.command('dump-flows',s) for s in SWITCHES}
