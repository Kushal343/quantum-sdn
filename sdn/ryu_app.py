"""Ryu OpenFlow 1.3 controller with a local authenticated decision API.

Run using the isolated Linux controller image; see linux/README.md.
"""
import hmac
import json
import os
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.lib import hub
from webob import Response
from sdn.ryu_core import RyuFlowService, flow
from sdn.openflow import COOKIE


class QKDRyu(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = os.environ.get('QKD_SDN_TOKEN', '')
        if len(self.token) < 24:
            raise RuntimeError('Set QKD_SDN_TOKEN to at least 24 characters')
        self.datapaths, self.waiters = {}, {}
        self.lock = hub.Semaphore(1)
        self.service = RyuFlowService(self.datapaths, self.transact)
        kwargs['wsgi'].register(DecisionAPI, dict(app=self))

    def transact(self, dp, messages):
        event = hub.Event()
        entry = dict(event=event, error=None)
        keys = []
        try:
            barrier = dp.ofproto_parser.OFPBarrierRequest(dp)
            for msg in messages + [barrier]:
                dp.set_xid(msg)
                key = (dp.id, msg.xid)
                keys.append(key)
                self.waiters[key] = entry
            # Record the barrier xid so errors and earlier barriers cannot ack a batch.
            entry['barrier'] = barrier.xid
            for msg in messages + [barrier]:
                dp.send_msg(msg)
            with hub.Timeout(5, RuntimeError('OpenFlow barrier timeout')):
                event.wait()
            if entry['error']:
                raise RuntimeError(entry['error'])
            if self.datapaths.get(dp.id) is not dp:
                raise RuntimeError('Switch disconnected during transaction')
        finally:
            for key in keys:
                self.waiters.pop(key, None)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def connected(self, ev):
        dp = ev.msg.datapath
        if dp.id not in (1,2):
            dp.close()
            return
        self.datapaths[dp.id] = dp
        self.service.initialized = False
        # Fail closed while waiting for explicit initialization/replay.
        dp.send_msg(flow(dp, COOKIE+0x7f, 65535, {}, []))

    @set_ev_cls(ofp_event.EventOFPStateChange, DEAD_DISPATCHER)
    def disconnected(self, ev):
        dp = ev.datapath
        if self.datapaths.get(dp.id) is dp:
            self.datapaths.pop(dp.id, None)
            self.service.initialized = False
        for (dpid, _), entry in list(self.waiters.items()):
            if dpid == dp.id:
                entry['error'] = 'Switch disconnected'
                entry['event'].set()

    @set_ev_cls(ofp_event.EventOFPBarrierReply, MAIN_DISPATCHER)
    def barrier(self, ev):
        entry = self.waiters.get((ev.msg.datapath.id, ev.msg.xid))
        if entry and entry['barrier'] == ev.msg.xid:
            entry['event'].set()

    @set_ev_cls(ofp_event.EventOFPErrorMsg, [CONFIG_DISPATCHER, MAIN_DISPATCHER])
    def error(self, ev):
        entry = self.waiters.get((ev.msg.datapath.id, ev.msg.xid))
        if entry:
            entry['error'] = 'Switch rejected OpenFlow message: type=%s code=%s' % (ev.msg.type, ev.msg.code)
            entry['event'].set()
        self.logger.error('OpenFlow error: %s', ev.msg)


class DecisionAPI(ControllerBase):
    def __init__(self, req, link, data, **config):
        super().__init__(req, link, data, **config)
        self.app = data['app']

    @route('qkd', '/qkd/status', methods=['GET'])
    def status(self, req, **kwargs):
        return self.handle(req, False)

    @route('qkd_init', '/qkd/initialize', methods=['POST'])
    def initialize(self, req, **kwargs):
        return self.handle(req, True, initialize=True)

    @route('qkd_decision', '/qkd/decision', methods=['POST'])
    def decision(self, req, **kwargs):
        return self.handle(req, True)

    def handle(self, req, mutate, initialize=False):
        if not hmac.compare_digest(req.headers.get('Authorization',''), 'Bearer '+self.app.token):
            return Response(status=401)
        try:
            with self.app.lock:
                if mutate:
                    if initialize:
                        self.app.service.initialize()
                    else:
                        if len(req.body) > 4096:
                            raise ValueError('Request too large')
                        data = req.json
                        if set(data) != {'channel','action'}:
                            raise ValueError('Expected channel and action')
                        self.app.service.apply(data['channel'], data['action'])
                data = self.app.service.status()
            return Response(content_type='application/json', body=json.dumps(data).encode())
        except (ValueError, TypeError, KeyError):
            return Response(status=400)
        except RuntimeError as exc:
            return Response(status=503, text=str(exc))
