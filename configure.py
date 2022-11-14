import meraki
import getopt
import sys
import json


def getnetworkid(_orgnetworks, _networkname):
    for network in _orgnetworks:
        if network['name'] == _networkname:
            return network['id']
        

def main(argv):
    org = ''
    network = ''
    configfile = ''
    orgnetworks = ''
    networkid = ''
    
    try:
        opts, args = getopt.getopt(argv, "a:b:c:")  # Collect cmd argument inputs
    except Exception as e:
        var = None
    for opt, arg in opts:
        if opt == '-a':
            org = arg
        elif opt == '-b':
            network = arg
        elif opt == '-c':
            configfile = arg

    dashboard = meraki.DashboardAPI(print_console=False, output_log=False, suppress_logging=True)  # Create session with Dashboard
    my_orgs = dashboard.organizations.getOrganizations()  # Get Orgs
    for o in my_orgs:
        if o['name'] == org:
            orgnetworks = dashboard.organizations.getOrganizationNetworks(o['id'], total_pages='all')
            
    networkid = getnetworkid(orgnetworks, network)
    
    json_data = open(configfile, "r")
    json_dict = json.load(json_data)

    i = 0
    while i < len(json_dict['Network']['Firewalls']):
        dashboard.devices.updateDevice(json_dict['Network']['Firewalls']['MX'+str(i)]['Serial'], name=str(json_dict['Network']['Firewalls']['MX'+str(i)]['Name']))
        if json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['usingStaticIp'] and json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['usingStaticIp']:
            dashboard.devices.updateDeviceManagementInterface(json_dict['Network']['Firewalls']['MX'+str(i)]['Serial'], wan1={
                'wanEnabled': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['wanEnabled'],
                'usingStaticIp': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['usingStaticIp'],
                'staticIp': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['staticIp'],
                'staticSubnetMask': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['staticSubnetMask'],
                'staticGatewayIp': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['staticGatewayIp'],
                'staticDns': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['staticDns'],
                'vlan': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['vlan']},
                                                              wan2={'wanEnabled': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['wanEnabled'],
                                                                    'usingStaticIp': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['usingStaticIp'],
                                                                    'staticIp': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['staticIp'],
                                                                    'staticSubnetMask': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['staticSubnetMask'],
                                                                    'staticGatewayIp': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['staticGatewayIp'],
                                                                    'staticDns': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['staticDns'],
                                                                    'vlan': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['vlan']})
        elif json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['usingStaticIp'] and not json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['usingStaticIp']:
            dashboard.devices.updateDeviceManagementInterface(json_dict['Network']['Firewalls']['MX'+str(i)]['Serial'], wan1={
                                                                                     'wanEnabled': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['wanEnabled'],
                                                                                     'usingStaticIp': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['usingStaticIp'],
                                                                                     'staticIp': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['staticIp'],
                                                                                     'staticSubnetMask': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['staticSubnetMask'],
                                                                                     'staticGatewayIp': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['staticGatewayIp'],
                                                                                     'staticDns': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['staticDns'],
                                                                                     'vlan': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['vlan']},
                                                              wan2={'wanEnabled': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['wanEnabled'],
                                                                    'usingStaticIp': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['usingStaticIp'],
                                                                    'vlan': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['vlan']})
        elif not json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['usingStaticIp'] and json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['usingStaticIp']:
            dashboard.devices.updateDeviceManagementInterface(json_dict['Network']['Firewalls']['MX'+str(i)]['Serial'],
                                                              wan1={'wanEnabled': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['wanEnabled'],
                                                                    'usingStaticIp': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['usingStaticIp'],
                                                                    'vlan': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['vlan']},
                                                              wan2={'wanEnabled': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['wanEnabled'],
                                                                    'usingStaticIp': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['usingStaticIp'],
                                                                    'staticIp': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['staticIp'],
                                                                    'staticSubnetMask': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['staticSubnetMask'],
                                                                    'staticGatewayIp':json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['staticGatewayIp'],
                                                                    'staticDns': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['staticDns'],
                                                                    'vlan': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['vlan']})
        elif not json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['usingStaticIp'] and not json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['usingStaticIp']:
            dashboard.devices.updateDeviceManagementInterface(json_dict['Network']['Firewalls']['MX'+str(i)]['Serial'],
                                                              wan1={'wanEnabled': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['wanEnabled'],
                                                                    'usingStaticIp': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['usingStaticIp'],
                                                                    'vlan': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN1']['vlan']},
                                                              wan2={'wanEnabled': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['wanEnabled'],
                                                                    'usingStaticIp': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['usingStaticIp'],
                                                                    'vlan': json_dict['Network']['Firewalls']['MX'+str(i)]['WAN2']['vlan']})

        # need to pass from GUI which ORG we are in. Field sites MX ports are set by the template
        if org != 'Compass Group Field Sites':
            j = 0
            while j < len(json_dict['Network']['Firewalls']['MX'+str(i)]['Ports']):
                if json_dict['Network']['Firewalls']['MX'+str(i)]['Ports'][j]['type'] == 'trunk':
                    dashboard.appliance.updateNetworkAppliancePort(networkid, portId=json_dict['Network']['Firewalls']['MX'+str(i)]['Ports'][j]['number'],
                                                                   enabled=json_dict['Network']['Firewalls']['MX'+str(i)]['Ports'][j]['enabled'],
                                                                   type=json_dict['Network']['Firewalls']['MX'+str(i)]['Ports'][j]['type'],
                                                                   vlan=json_dict['Network']['Firewalls']['MX'+str(i)]['Ports'][j]['vlan'],
                                                                   dropUntaggedTraffic=json_dict['Network']['Firewalls']['MX'+str(i)]['Ports'][j]['dropUntaggedTraffic'],
                                                                   allowedVlans=json_dict['Network']['Firewalls']['MX'+str(i)]['Ports'][j]['allowedVlans'])
                else:
                    dashboard.appliance.updateNetworkAppliancePort(networkid, portId=json_dict['Network']['Firewalls']['MX'+str(i)]['Ports'][j]['number'],
                                                                   enabled=json_dict['Network']['Firewalls']['MX'+str(i)]['Ports'][j]['enabled'],
                                                                   type=json_dict['Network']['Firewalls']['MX'+str(i)]['Ports'][j]['type'],
                                                                   dropUntaggedTraffic=json_dict['Network']['Firewalls']['MX'+str(i)]['Ports'][j]['dropUntaggedTraffic'],
                                                                   vlan=json_dict['Network']['Firewalls']['MX'+str(i)]['Ports'][j]['vlan'])
                j += 1
        j = 0
        while j < len(json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans']): # Field sites vlans are set by template.
            if org != 'Compass Group Field Sites':
                vlanexists = False
                try:
                    vlantocheck = dashboard.appliance.getNetworkApplianceVlan(networkid, json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['id'])
                    if json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['id'] == vlantocheck['id']:
                        vlanexists = True
                except meraki.APIError as e:
                    print(str(e))

                if vlanexists is False:
                    try:
                        dashboard.appliance.createNetworkApplianceVlan(networkid, id=json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['id'],
                                                                       name=json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['name'],
                                                                       applianceIp=json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['applianceIp'],
                                                                       subnet=json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['subnet'])
                    except meraki.APIError as e:
                        print(str(e))
                try:
                    dashboard.appliance.updateNetworkApplianceVlan(networkid, json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['id'],
                                                                   name=json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['name'],
                                                                   applianceIp=json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['applianceIp'],
                                                                   subnet=json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['subnet'],
                                                                   fixedIpAssignments=json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['fixedIpAssignments'],
                                                                   reservedIpRanges=json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['reservedIpRanges'],
                                                                   dnsNameservers=json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['dnsNameservers'],
                                                                   dhcpHandling=json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['dhcpHandling'],
                                                                   dhcpLeaseTime=json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['dhcpLeaseTime'],
                                                                   dhcpBootOptionsEnabled=json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['dhcpBootOptionsEnabled'],
                                                                   dhcpOptions=json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['dhcpOptions'])
                except meraki.APIError as e:
                    print(str(e))
            else:
                if str(json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][str(i)]['id']) not in ['1', '150', '151', '152', '153']:
                    try:
                        dashboard.appliance.updateNetworkApplianceVlan(networkid, json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['id'],
                                                                       applianceIp=json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['applianceIp'],
                                                                       subnet=json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['subnet'],
                                                                       fixedIpAssignments=json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['fixedIpAssignments'],
                                                                       reservedIpRanges=json_dict['Network']['Firewalls']['MX' + str(i)]['Vlans'][j]['reservedIpRanges'])
                    except meraki.APIError as e:
                        print(str(e))
            j += 1

        try:
            dashboard.appliance.updateNetworkApplianceFirewallOneToManyNatRules(networkid, json_dict['Network']['Firewalls']['MX' + str(i)]['1:M NAT']['rules'])
        except meraki.APIError as e:
            print(str(e))
        try:
            dashboard.appliance.updateNetworkApplianceFirewallOneToOneNatRules(networkid, json_dict['Network']['Firewalls']['MX' + str(i)]['1:1 NAT']['rules'])
        except meraki.APIError as e:
            print(str(e))
        try:
            dashboard.appliance.updateNetworkApplianceFirewallPortForwardingRules(networkid, json_dict['Network']['Firewalls']['MX' + str(i)]['Port Forwards']['rules'])
        except meraki.APIError as e:
            print(str(e))
        i += 1

    i = 0
    while i < len(json_dict['Network']['Switches']):
        dashboard.devices.updateDevice(json_dict['Network']['Switches']['MS'+str(i)]['Serial'], name=json_dict['Network']['Switches']['MS'+str(i)]['Name'])

        j = 0
        while j < len(json_dict['Network']['Switches']['MS'+str(i)]['Ports']):
            if json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['type'] == 'access':
                dashboard.switch.updateDeviceSwitchPort(json_dict['Network']['Switches']['MS'+str(i)]['Serial'],
                                                        json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['portId'],
                                                        name=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['name'],
                                                        tags=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['tags'],
                                                        enabled=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['enabled'],
                                                        type=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['type'],
                                                        vlan=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['vlan'],
                                                        voiceVlan=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['voiceVlan'],
                                                        poeEnabled=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['poeEnabled'],
                                                        isolationEnabled=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['isolationEnabled'],
                                                        rstpEnabled=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['rstpEnabled'],
                                                        stpGuard=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['stpGuard'],
                                                        linkNegotiation=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['linkNegotiation'],
                                                        portScheduleId=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['portScheduleId'],
                                                        udld=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['udld'],
                                                        accessPolicyType=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['accessPolicyType'],
                                                        )
            else:
                dashboard.switch.updateDeviceSwitchPort(json_dict['Network']['Switches']['MS'+str(i)]['Serial'],
                                                        json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['portId'],
                                                        name=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['name'],
                                                        tags=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['tags'],
                                                        enabled=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['enabled'],
                                                        type=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['type'],
                                                        vlan=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['vlan'],
                                                        allowedVlans=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['allowedVlans'],
                                                        poeEnabled=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['poeEnabled'],
                                                        isolationEnabled=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['isolationEnabled'],
                                                        rstpEnabled=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['rstpEnabled'],
                                                        stpGuard=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['stpGuard'],
                                                        linkNegotiation=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['linkNegotiation'],
                                                        portScheduleId=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['portScheduleId'],
                                                        udld=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['udld'],
                                                        accessPolicyType=json_dict['Network']['Switches']['MS'+str(i)]['Ports'][j]['accessPolicyType'],
                                                        )
            j += 1
        i += 1

    i = 0
    while i < len(json_dict['Network']['AccessPoints']):
        dashboard.devices.updateDevice(json_dict['Network']['AccessPoints']['MR'+str(i)]['Serial'], name=json_dict['Network']['AccessPoints']['MR'+str(i)]['Name'])
        i += 1


if __name__ == '__main__':
    main(sys.argv[1:])