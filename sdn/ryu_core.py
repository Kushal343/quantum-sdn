"""Framework-independent OpenFlow message construction; no shell flow injection."""
from .openflow import COOKIE, TRUNK

ACTIONS = ('continue','hold','isolate','isolated','retune','verify','keep','rollback')


def desired_state(old, action):
    if action not in ACTIONS:
        raise ValueError('Invalid QKD action')
    return 'isolated' if old == 'isolated' or action in ('isolate','isolated') else 'held' if action == 'hold' else 'active'


def flow(dp, cookie, priority, match, actions):
    p, of = dp.ofproto_parser, dp.ofproto
    instructions = [p.OFPInstructionActions(of.OFPIT_APPLY_ACTIONS, actions)] if actions else []
    return p.OFPFlowMod(datapath=dp, cookie=cookie, table_id=0, priority=priority,
        match=p.OFPMatch(**match), instructions=instructions)


def delete(dp, cookie, mask):
    p, of = dp.ofproto_parser, dp.ofproto
    return p.OFPFlowMod(datapath=dp, cookie=cookie, cookie_mask=mask, table_id=0,
        command=of.OFPFC_DELETE, out_port=of.OFPP_ANY, out_group=of.OFPG_ANY,
        match=p.OFPMatch())


def blocking_flows(dp, channel):
    return [flow(dp, COOKIE+0x80+channel, 1000, dict(in_port=channel), []),
            flow(dp, COOKIE+0x80+channel, 1000,
                 dict(in_port=TRUNK, vlan_vid=dp.ofproto.OFPVID_PRESENT | (100+channel)), [])]


def initial_flows(dp, states):
    p, of = dp.ofproto_parser, dp.ofproto
    result = [delete(dp, COOKIE, 0xffffff00), flow(dp, COOKIE, 0, {}, [])]
    # Install block rules before forwarding rules when replaying quarantine.
    for channel, state in states.items():
        if state != 'active':
            result.extend(blocking_flows(dp, channel))
    for channel in range(1,5):
        vlan = of.OFPVID_PRESENT | (100+channel)
        result.extend([
            flow(dp, COOKIE+channel, 100, dict(in_port=channel, vlan_vid=of.OFPVID_NONE),
                 [p.OFPActionPushVlan(0x8100), p.OFPActionSetField(vlan_vid=vlan), p.OFPActionOutput(TRUNK)]),
            flow(dp, COOKIE+channel, 100, dict(in_port=TRUNK, vlan_vid=vlan),
                 [p.OFPActionPopVlan(), p.OFPActionOutput(channel)])])
    return result


class RyuFlowService:
    def __init__(self, datapaths, transact):
        self.datapaths, self.transact = datapaths, transact
        self.states = {i:'active' for i in range(1,5)}
        self.initialized = False

    def _switches(self):
        if set(self.datapaths) != {1,2}:
            raise RuntimeError('Both expected switches must be connected')
        return [self.datapaths[i] for i in (1,2)]

    def initialize(self):
        switches = self._switches()
        self.initialized = False
        for dp in switches:
            self.transact(dp, initial_flows(dp, self.states))
        if any(self.datapaths.get(dp.id) is not dp for dp in switches):
            raise RuntimeError('Switch changed during initialization')
        self.initialized = True

    def apply(self, channel, action):
        if type(channel) is not int or channel not in self.states:
            raise ValueError('Invalid wavelength')
        desired = desired_state(self.states[channel], action)
        if not self.initialized:
            raise RuntimeError('Switch rules are not initialized')
        switches = self._switches()
        old = self.states[channel]
        if desired != old:
            # Record the restrictive intention first: reconnect must replay it
            # even if an acknowledgement is lost. A failed resume stays blocked.
            if desired != 'active':
                self.states[channel] = desired
            try:
                for dp in switches:
                    messages = ([delete(dp, COOKIE+0x80+channel, 0xffffffffffffffff)]
                                if desired == 'active' else blocking_flows(dp, channel))
                    self.transact(dp, messages)
            except Exception:
                self.initialized = False
                raise
            self.states[channel] = desired
        return desired

    def status(self):
        return dict(ready=self.initialized and set(self.datapaths)=={1,2},
                    switches=sorted(self.datapaths), states=self.states)
