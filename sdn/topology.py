"""Linux-only two-switch lab with four isolated host pairs."""
from .openflow import SWITCHES,TRUNK


def create_network():
    from mininet.net import Mininet
    from mininet.node import OVSSwitch
    from mininet.link import TCLink
    net=Mininet(controller=None,switch=OVSSwitch,link=TCLink,build=False)
    try:
        left=net.addSwitch(SWITCHES[0],protocols='OpenFlow13',failMode='secure')
        right=net.addSwitch(SWITCHES[1],protocols='OpenFlow13',failMode='secure')
        for i in range(1,5):
            a=net.addHost(f'a{i}',ip=f'10.{i}.0.1/24',mac=f'02:00:00:00:{i:02x}:01')
            b=net.addHost(f'b{i}',ip=f'10.{i}.0.2/24',mac=f'02:00:00:00:{i:02x}:02')
            net.addLink(a,left,port2=i)
            net.addLink(b,right,port2=i)
        net.addLink(left,right,port1=TRUNK,port2=TRUNK,bw=100,delay='2ms')
        net.build();net.start()
        return net
    except BaseException:
        net.stop();raise


def connectivity(net):
    result={}
    for i in range(1,5):
        a,b=net.get(f'a{i}',f'b{i}')
        _,_,code=a.pexec(['ping','-n','-c','1','-W','1',b.IP()])
        result[f'lambda_{i}']=code==0
    return result
