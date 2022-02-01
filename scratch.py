import meraki
import xml.etree.ElementTree as ET

def getnetworkid(_orgnetworks, _networkname):
    for network in _orgnetworks:
        if network['name'] == _networkname:
            return network['id']


class AccessPoint:
    def __init__(self, serial, name):
        self.serial = serial
        self.name = name


class Switch:
    def __init__(self, serial, name, ports):
        self.serial = serial
        self.name = name
        self.ports = ports


class NetworkDevices:
    def __init__(self, networkid, devices):
        self.networkid = networkid
        self.devices = devices


class Appliance:
    def __init__(self, serial, name, mgmtint, subnets, manynat, onenat, portforward, netports, netvlans):
        self.serial = serial
        self.name = name
        self.mgmtint = mgmtint
        self.subnets = subnets
        self.manynat = manynat
        self.onenat = onenat
        self.portforward = portforward
        self.netports = netports
        self.netvlans = netvlans


def main():
    root = ET.parse('config.xml').getroot()
    for child in root:
        if child.tag == 'SourceOrg':
            print(child.text)
        elif child.tag == 'SourceNetworks':
            for network in child:
                print(network.text)
        elif child.tag == 'NewNetwork':
            print(child.text)


if __name__ == '__main__':
    main()