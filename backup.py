import datetime
import meraki
import webbrowser
import json
import os
import requests
import re
import pathlib
import getopt
import sys


class NetworkDevices:
    def __init__(self, networkid, devices):
        self.networkid = networkid
        self.devices = devices


class AccessPoint:
    def __init__(self, serial, name):
        self.serial = serial
        self.name = name


class Switch:
    def __init__(self, serial, name, ports):
        self.serial = serial
        self.name = name
        self.ports = ports


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


def getnetworkid(_orgnetworks, _networkname):
    for network in _orgnetworks:
        if network['name'] == _networkname:
            return network['id']


def main(argv):
    dashboard = meraki.DashboardAPI(print_console=False, output_log=False, suppress_logging=True)  # Create session with Dashboard
    my_orgs = dashboard.organizations.getOrganizations()  # Get Orgs
    orgid = ''  # ID of the org to pull networks from
    orglist = []  # List of Orgs
    org = ''  # org the network exists in we want to backup
    network = '' # network to backup
    mxlist = []  # list of MX devices
    mslist = []  # list of Switching devices
    mrlist = []  # list of wireless devices
    networkdevicelist = []  # list for network devices
    configfilename = ''  # out file for the config downloaded from source networks
    """
    try:
        opts, args = getopt.getopt(argv, "a:b:")  # Collect cmd argument inputs
    except Exception as e:
        var = None
    for opt, arg in opts:
        if opt == '-a':
            org = args
        elif opt == '-b':
            network = args
    """
    org = 'Compass Group Remote Offices'
    network = 'US LAB - Greenwood'

    for orgs in my_orgs:
        if orgs['name'] == org:
            #  Get the networks from the Org from last step
            orgnetworks = dashboard.organizations.getOrganizationNetworks(orgs['id'], total_pages='all')

    #  Get the network devices from the selected network
    netid = getnetworkid(orgnetworks, network)
    networkdevicelist.append(NetworkDevices(netid, dashboard.networks.getNetworkDevices(netid)))

    for networkdevices in networkdevicelist:
        for devices in networkdevices.devices:
            name = 'placeholder'
            if 'name' in devices:
                name = devices['name']

            if 'MS' in devices['model']:
                mslist.append(Switch(devices['serial'], name, dashboard.switch.getDeviceSwitchPorts(devices['serial'])))

            elif 'MX' in devices['model']:
                mxlist.append(Appliance(devices['serial'], name,
                              dashboard.devices.getDeviceManagementInterface(devices['serial']),
                              dashboard.appliance.getDeviceApplianceDhcpSubnets(devices['serial']),
                              dashboard.appliance.getNetworkApplianceFirewallOneToManyNatRules(networkdevices.networkid),
                              dashboard.appliance.getNetworkApplianceFirewallOneToOneNatRules(networkdevices.networkid),
                              dashboard.appliance.getNetworkApplianceFirewallPortForwardingRules(networkdevices.networkid),
                              dashboard.appliance.getNetworkAppliancePorts(networkdevices.networkid),
                              dashboard.appliance.getNetworkApplianceVlans(networkdevices.networkid)
                                        )
                              )
            else:
                mrlist.append(AccessPoint(devices['serial'], name))

    #  Write out the downloaded settings to the out file.
    json_data = {
        "Network":
            {
                "NetworkName": network,
                "Firewalls": {},
                "Switches": {},
                "AccessPoints": {},
            }
    }
    for mx in mxlist:
        json_data['Network']['Firewalls'][mx.name] = {
            "Serial": mx.serial,
            "WAN": mx.mgmtint['wan1'],
            "Ports": mx.netports,
            "1:1 NAT": mx.onenat,
            "1:M NAT": mx.manynat,
            "Port Forwards": mx.portforward,
            "DHCP Subnets": mx.subnets,
            "Vlans": mx.netvlans
            }
    for ms in mslist:
        json_data['Network']['Switches'][ms.name] = {
            "Serial": ms.serial,
            "Ports": ms.ports,
        }
    for mr in mrlist:
        json_data['Network']['AccessPoints'][mr.name] = {
            "Serial": mr.serial,
        }

    json_string = json.dumps(json_data)
    with open(r'networkconfig' + str(datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")).replace(' ', '') + '.json', 'w') as datafile:
        configfilename = datafile.name
        datafile.write(json_string)


if __name__ == '__main__':
    main(sys.argv[1:])