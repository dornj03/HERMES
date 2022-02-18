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
import xml.etree.ElementTree as ET


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


def networkbind(dashboard, templatename, networkname, orgid):
    orgnetworks = dashboard.organizations.getOrganizationNetworks(orgid)
    orgtemplates = dashboard.organizations.getOrganizationConfigTemplates(orgid)
    networkid = getnetworkid(orgnetworks, networkname)
    autobind = True
    templateid = ''

    for template in orgtemplates:
        if template['name'] == templatename:
            templateid = template['id']
            if 'Canteen Template' == template['name']:
                autobind = False

    try:
        dashboard.networks.bindNetwork(networkid, templateid, autoBind=autobind)
    except meraki.APIError as e:
        print('Bind failed. Error: ' + str(e))
    else:
        print('Network bound!')


def claimdevices(dashboard, claimserials, orgid, networkname):
    orgnetworks = dashboard.organizations.getOrganizationNetworks(orgid)
    networkid = getnetworkid(orgnetworks, networkname)
    claimerrors = ''
    while True:
        # Claim new devices
        try:
            print('Attempting claim...')
            dashboard.organizations.claimIntoOrganization(orgid, serials=claimserials)
            dashboard.networks.claimNetworkDevices(networkid, claimserials)
        except meraki.APIError as error:
            print('There was an error while claiming. You may need to wait a few minutes before trying again.')
            print('ERROR MESSAGE:' + str(error))

            if 'timeout' in str(error):
                dashboard = meraki.DashboardAPI(print_console=False, output_log=False, suppress_logging=True)

            claimeddevices = dashboard.networks.getNetworkDevices(networkid)

            for device in claimeddevices:
                if device['serial'] not in claimserials:
                    print(device['serial'] + ' was not claimed.')
                else:
                    print(device['serial'] + ' is claimed and is in the network ' + networkname)
            input('Press enter to try claiming again...')
        else:
            claimeddevices = dashboard.networks.getNetworkDevices(networkid)

            for device in claimeddevices:
                if device['serial'] not in claimserials:
                    print(device['serial'] + ' was not claimed.')
                    claimerrors += device['serial']
            if claimerrors == '':
                print('Claiming complete.')
                break
            else:
                input('Press enter to try claiming again...')


def all_same(items):
    return all(x == items[0] for x in items)


def createnetwork(orgid, nwparams):
    # creates network if one does not already exist with the same name
    p_apikey = os.getenv('MERAKI_DASHBOARD_API_KEY')

    try:
        print('Creating network with the following:\nName: ' +  nwparams['name'] + '\nTimezone: '
              + nwparams['timeZone'] + '\nType: ' + nwparams['type'])
        r = requests.post('https://%s/api/v0/organizations/%s/networks' % ("api.meraki.com", orgid),
                          data=json.dumps(
                              {'timeZone': nwparams['timeZone'], 'name': nwparams['name'],
                               'organizationId': orgid, 'type': nwparams['type']}),
                          headers={'X-Cisco-Meraki-API-Key': p_apikey, 'Content-Type': 'application/json'})
    except ValueError:
        print('Unable to create network')
    else:
        print('\nNetwork successfully created.')


def doesnetworkexist(_orgid, _orgnetworks, _networkname):
    # check if network exists
    nwresult = 'null'
    print('\nChecking for network duplicates for ' + _networkname)
    for network in _orgnetworks:
        if network['name'] == _networkname:
            nwresult = 'Network Exists.'
            break

    if nwresult != 'null':
        print('This network exists already. Skipping creation.')
        return 'true'
    else:
        print('No duplicates found.')
        return 'false'


def getnetworkid(_orgnetworks, _networkname):
    for network in _orgnetworks:
        if network['name'] == _networkname:
            return network['id']


def main(argv):
    dashboard = meraki.DashboardAPI(print_console=False, output_log=False, suppress_logging=True)  # Create session with Dashboard
    my_orgs = dashboard.organizations.getOrganizations()  # Get Orgs
    orglist = []  # List of Orgs
    orgid = ''  # ID of the org to pull networks from
    oldorg = ''  # old org networks are moving from
    runmode = ''  # mode the script will run in
    mxlist = []  # list of MX devices
    mslist = []  # list of Switching devices
    mrlist = []  # list of wireless devices
    claimserials = []  # serials to be claimed into new network
    sourcenetworks = []  # networks to be used to pull down devices and settings
    networkdevicelist = []  # list for network devices
    timezones = []  # list of old network timezones
    configfilename = ''  # out file for the config downloaded from source networks
    userinput = ''  # variable for input use later
    inputfile = ''  # xml file for config mode

    try:
        opts, args = getopt.getopt(argv, "hgbtc:")  # Collect cmd argument inputs
    except getopt.GetoptError:
        print('Error. Try again.')
        sys.exit(2)  # exit script as args didnt match what we look for
    for opt, arg in opts:
        if opt == '-h':
            print('Hermes Help Menu')
            print('-g Guided run mode')
            print('-c Config file mode')
            print('-t Template rebind mode')
            print('-b Backup network settings mode')
            sys.exit(2)
        elif opt == '-g':
            runmode = 'Guided'
        elif opt == '-c':
            runmode = 'ConfigFile'
            inputfile = arg
        elif opt == '-t':
            runmode = 'Template'
        elif opt == '-b':
            runmode = 'Backup'
        else:
            print('Error. Try again.')
            sys.exit(2)  # exit script as args didnt match what we look for

    #  Figure out which Org to use.
    if runmode == 'Guided' or 'Backup' or 'Template':
        print('Which Org are you moving from? Enter the number.')
        i = 0
        for org in my_orgs:
            if org['name'] != 'Compass Group Surveillance':
                orglist.append(org)
                print(str(i + 1) + ') ' + org['name'])
                i = i + 1
        orginput = input()
        if orginput == '1':
            orgid = orglist[0]['id']
            print(orglist[0]['name'] + ' selected.')
            oldorg = orglist[0]['name']
        elif orginput == '2':
            orgid = orglist[1]['id']
            print(orglist[1]['name'] + ' selected.')
            oldorg = orglist[1]['name']
        elif orginput == '3':
            orgid = orglist[2]['id']
            print(orglist[2]['name'] + ' selected.')
            oldorg = orglist[2]['name']
    elif runmode == 'ConfigFile':
        root = ET.parse(inputfile).getroot()  # config file root
        for child in root:
            if child.tag == 'SourceOrg':
                oldorg = child.text

        for org in my_orgs:
            if org['name'] == oldorg:
                orgid = org['id']

    #  Get the networks from the Org from last step
    orgnetworks = dashboard.organizations.getOrganizationNetworks(orgid, total_pages='all')

    # Figure out the networks we want to use.
    if runmode == 'Guided':
        print('What is the name of the source network(s)? Enter one at a time. Type \'end\' when done.')

        while 'end' not in userinput:
            userinput = input()
            if 'lab' == userinput.lower():
                sourcenetworks = []
                break
            if 'end' not in userinput.lower():
                sourcenetworks.append(userinput)
    elif runmode == 'ConfigFile':
        for xmlnetwork in root.iter("Network"):
            sourcenetworks.append(xmlnetwork.text)
        print(sourcenetworks)
    elif runmode == 'Backup':
        print('What is the name of the network(s) to backup? Enter one at a time. Type \'end\' when done.')
        while 'end' not in userinput:
            userinput = input()
            if 'lab' == userinput.lower():
                sourcenetworks = []
                break
            if 'end' not in userinput.lower():
                sourcenetworks.append(userinput)
    elif runmode == 'Template':
        print('What is the name of the network you are rebinding?')
        userinput = input()
        sourcenetworks.append(userinput)

    print('Downloading settings for network.')

    #  Get the network devices from the selected networks
    for network in sourcenetworks:
        netid = getnetworkid(orgnetworks, network)
        networkdevicelist.append(NetworkDevices(netid, dashboard.networks.getNetworkDevices(netid)))
        networkresponse = dashboard.networks.getNetwork(netid)
        timezones.append(networkresponse['timeZone'])

    #  Get the settings from the devices in the networks.
    for networkdevices in networkdevicelist:
        for devices in networkdevices.devices:
            claimserials.append(devices['serial'])
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
    with open(r'networkconfig' + str(datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")).replace(' ', '') + '.txt', 'w') as f:
        configfilename = f.name
        f.write('APPLIANCES:\n')
        for mx in mxlist:
            f.write('\n' + 'Serial: ' + str(mx.serial) + '\n')
            f.write('WAN Interfaces: ' + str(mx.mgmtint) + '\n')
            f.write('MX Switching Ports: ' + str(mx.netports) + '\n')
            f.write('1:1 NAT: ' + str(mx.onenat) + '\n')
            f.write('1:M NAT: ' + str(mx.manynat) + '\n')
            f.write('Port Forwarding: ' + str(mx.portforward) + '\n')
            f.write('DHCP Subnets: ' + str(mx.subnets) + '\n')
            f.write('Vlans: ' + str(mx.netvlans) + '\n')

        f.write('\nSWITCHES:\n')
        for ms in mslist:
            f.write('\n' + 'Serial: ' + str(ms.serial) + '\n')
            f.write('Switchports: ' + str(ms.ports) + '\n')

        f.write('\nACCESS POINTs:\n')
        for mr in mrlist:
            f.write('\n' + 'Serial: ' + str(mr.serial) + '\n')
            f.write('Name: ' + str(mr.name) + '\n')

        f.write('\nSerials Downloaded: ' + str(claimserials))

        f.write('\nSource Networks: ' + str(sourcenetworks))
        f.close()

    print('Downloading of settings is complete. Would you like to review whats been downloaded? y/n')
    reviewsettings = input()

    # Open notepad if you want to review the settings.
    if reviewsettings == 'y':
        webbrowser.open(configfilename)

    #  Backup Mode ends here
    #  Setup new network and move devices and upload config
    if runmode == 'ConfigFile' or 'Guided' or 'Template':
        if runmode == 'Guided':
            print('What is the name for the new network?')
            newnetworkname = input()
            if re.search("[US]-[0-9]+[-][a-zA-Z]+|[CA]-[0-9]+[-][a-zA-Z]+", newnetworkname):
                print('Field Site detected. Network will be created in Compass Field Sites Org.')
                workingorg = 'Compass Group Field Sites'
            elif re.search("[US][ ][a-zA-Z]+[ ][-][ ][a-zA-Z]+|[CA][ ][a-zA-Z]+[ ][-][ ][a-zA-Z]+", newnetworkname):
                print('Remote Site detected. Network will be created in Compass Remote Offices Org.')
                workingorg = 'Compass Group Remote Offices'
            else:
                while True:
                    print('Detecting network type failed. Choose manually...enter 1 or 2.')
                    print('1. - Compass Group Field Sites')
                    print('2. - Compass Group Remote Offices')
                    orgchoice = input()
                    if orgchoice == '1':
                        workingorg = 'Compass Group Field Sites'
                        break
                    elif orgchoice == '2':
                        workingorg = 'Compass Group Remote Offices'
                        break
                    else:
                        print('You entered neither a 1 or a 2. Try again.')
        elif runmode == 'ConfigFile':
            workingorg = ''
            newnetworkname = ''

            for child in root:
                if child.tag == 'NewNetwork':
                    newnetworkname = child.text
                if child.tag == 'DestinationOrg':
                    workingorg = child.text
        if runmode in ('ConfigFile', 'Guided'):
            while True:
                print('The following serial numbers will be unclaimed:')
                print(claimserials)
                print('Proceed with unclaiming devices from org ' + oldorg + ' y/n')
                unclaimresponse = input()

                if unclaimresponse == 'y':
                    for networkdevices in networkdevicelist:
                        for devices in networkdevices.devices:
                            print('Removing:' + devices['serial'])
                            dashboard.networks.removeNetworkDevices(networkdevices.networkid, devices['serial'])
                    break
                else:
                    print('Script paused. Input anything to continue.')
                    input()

            for org in my_orgs:
                if workingorg == org['name']:
                    neworgid = org['id']

            neworgnetworks = dashboard.organizations.getOrganizationNetworks(neworgid, total_pages='all')

            result = doesnetworkexist(neworgid, neworgnetworks, newnetworkname)

            if result == 'false':
                print('Checking source network timezones.')
                if all_same(timezones) is True:
                    print('All timezones match. New network will use: ' + timezones[0])
                    timezone = timezones[0]

                else:
                    print('Source networks have mismatching timezones. Defaulting to EST')
                    timezone = 'America/New_York'

                nwparams = {'name': newnetworkname, 'timeZone': timezone, 'organizationId': neworgid,
                            'type': 'appliance switch wireless'}

                createnetwork(neworgid, nwparams)

            print('Claiming devices into the new network.')
            claimdevices(dashboard, claimserials, neworgid, newnetworkname)

        if runmode == 'Guided':
            print('Which template do you want to bind this network to? Enter NA to skip.')
            templates = dashboard.organizations.getOrganizationConfigTemplates(neworgid)

            for template in templates:
                print(str(template['name']))

            while True:
                templateinput = input()

                if templateinput != '':
                    template = templateinput
                    break
        elif runmode == 'Template':
            print('Unbinding from current template.')
            print(sourcenetworks[0])
            dashboard.networks.unbindNetwork(getnetworkid(orgnetworks, sourcenetworks[0]))
            print('Which template do you want to bind this network to? Enter NA to skip.')
            templates = dashboard.organizations.getOrganizationConfigTemplates(orgid)

            for template in templates:
                print(str(template['name']))

            while True:
                templateinput = input()

                if templateinput != '':
                    template = templateinput
                    break
            neworgid = orgid
            newnetworkname = sourcenetworks[0]
            workingorg = oldorg
        else:
            template = ''
            for child in root:
                if child.tag == 'NewTemplate':
                    template = child.text

        if template.lower() != 'na':
            print('Binding to template: ' + template)
            networkbind(dashboard, template, newnetworkname, neworgid)
        else:
            print('Skipping template bind.')

        input('It is recommended to wait a few minutes before uploading config....press any key to continue...')
        print('Uploading config to devices.')

        neworgnetworks = dashboard.organizations.getOrganizationNetworks(neworgid, total_pages='all')
        newnetworkid = getnetworkid(neworgnetworks, newnetworkname)

        for mxdevice in mxlist:
            dashboard.devices.updateDevice(mxdevice.serial, name=str(mxdevice.name))
            if mxdevice.mgmtint['wan1']['usingStaticIp'] and mxdevice.mgmtint['wan2']['usingStaticIp']:
                dashboard.devices.updateDeviceManagementInterface(mxdevice.serial, wan1={
                    'wanEnabled': mxdevice.mgmtint['wan1']['wanEnabled'],
                    'usingStaticIp': mxdevice.mgmtint['wan1']['usingStaticIp'],
                    'staticIp': mxdevice.mgmtint['wan1']['staticIp'],
                    'staticSubnetMask': mxdevice.mgmtint['wan1'][
                        'staticSubnetMask'], 'staticGatewayIp': mxdevice.mgmtint['wan1'][
                        'staticGatewayIp'], 'staticDns': mxdevice.mgmtint['wan1'][
                        'staticDns'], 'vlan': mxdevice.mgmtint['wan1']['vlan']},
                                                              wan2={'wanEnabled': mxdevice.mgmtint['wan2']['wanEnabled'],
                                                                    'usingStaticIp': mxdevice.mgmtint['wan2'][
                                                                        'usingStaticIp'],
                                                                    'staticIp': mxdevice.mgmtint['wan2']['staticIp'],
                                                                    'staticSubnetMask': mxdevice.mgmtint['wan2'][
                                                                        'staticSubnetMask'],
                                                                    'staticGatewayIp': mxdevice.mgmtint['wan2'][
                                                                        'staticGatewayIp'],
                                                                    'staticDns': mxdevice.mgmtint['wan2'][
                                                                        'staticDns'],
                                                                    'vlan': mxdevice.mgmtint['wan2']['vlan']})
            elif mxdevice.mgmtint['wan1']['usingStaticIp'] and not mxdevice.mgmtint['wan2']['usingStaticIp']:
                dashboard.devices.updateDeviceManagementInterface(mxdevice.serial, wan1={'wanEnabled': mxdevice.mgmtint['wan1']['wanEnabled'],
                                                                                         'usingStaticIp': mxdevice.mgmtint['wan1']['usingStaticIp'],
                                                                                         'staticIp': mxdevice.mgmtint['wan1']['staticIp'],
                                                                                         'staticSubnetMask': mxdevice.mgmtint['wan1'][
                                                                                         'staticSubnetMask'], 'staticGatewayIp': mxdevice.mgmtint['wan1'][
                                                                                         'staticGatewayIp'], 'staticDns': mxdevice.mgmtint['wan1'][
                                                                                         'staticDns'], 'vlan': mxdevice.mgmtint['wan1']['vlan']},
                                                                  wan2={'wanEnabled': mxdevice.mgmtint['wan2']['wanEnabled'],
                                                                        'usingStaticIp': mxdevice.mgmtint['wan2']['usingStaticIp'],
                                                                        'vlan': mxdevice.mgmtint['wan2']['vlan']})
            elif not mxdevice.mgmtint['wan1']['usingStaticIp'] and mxdevice.mgmtint['wan2']['usingStaticIp']:
                dashboard.devices.updateDeviceManagementInterface(mxdevice.serial,
                                                                  wan1={'wanEnabled': mxdevice.mgmtint['wan1']['wanEnabled'],
                                                                        'usingStaticIp': mxdevice.mgmtint['wan1']['usingStaticIp'],
                                                                        'vlan': mxdevice.mgmtint['wan1']['vlan']},
                                                                  wan2={'wanEnabled': mxdevice.mgmtint['wan2']['wanEnabled'],
                                                                        'usingStaticIp': mxdevice.mgmtint['wan2']['usingStaticIp'],
                                                                        'staticIp': mxdevice.mgmtint['wan2']['staticIp'],
                                                                        'staticSubnetMask': mxdevice.mgmtint['wan2'][
                                                                              'staticSubnetMask'], 'staticGatewayIp': mxdevice.mgmtint['wan2'][
                                                                          'staticGatewayIp'], 'staticDns': mxdevice.mgmtint['wan2'][
                                                                          'staticDns'], 'vlan': mxdevice.mgmtint['wan2']['vlan']})
            elif not mxdevice.mgmtint['wan1']['usingStaticIp'] and not mxdevice.mgmtint['wan2']['usingStaticIp']:
                dashboard.devices.updateDeviceManagementInterface(mxdevice.serial,
                                                                  wan1={'wanEnabled': mxdevice.mgmtint['wan1']['wanEnabled'],
                                                                        'usingStaticIp': mxdevice.mgmtint['wan1']['usingStaticIp'],
                                                                        'vlan': mxdevice.mgmtint['wan1']['vlan']},
                                                                  wan2={'wanEnabled': mxdevice.mgmtint['wan2']['wanEnabled'],
                                                                        'usingStaticIp': mxdevice.mgmtint['wan2']['usingStaticIp'],
                                                                        'vlan': mxdevice.mgmtint['wan2']['vlan']})

            if workingorg != 'Compass Group Field Sites':
                for port in mxdevice.netports:
                    if port['type'] == 'trunk':
                        dashboard.appliance.updateNetworkAppliancePort(newnetworkid, portId=port['number'],
                                                                       enabled=port['enabled'],
                                                                       type=port['type'],
                                                                       vlan=port['vlan'],
                                                                       dropUntaggedTraffic=port['dropUntaggedTraffic'],
                                                                       allowedVlans=port['allowedVlans'])
                    else:
                        dashboard.appliance.updateNetworkAppliancePort(newnetworkid, portId=port['number'],
                                                                       enabled=port['enabled'],
                                                                       type=port['type'],
                                                                       dropUntaggedTraffic=port['dropUntaggedTraffic'],
                                                                       vlan=port['vlan'])
            for vlan in mxdevice.netvlans:
                if workingorg != 'Compass Group Field Sites':
                    vlanexists = False
                    try:
                        vlantocheck = dashboard.appliance.getNetworkApplianceVlan(newnetworkid, vlan['id'])
                        if vlan['id'] == vlantocheck['id']:
                            vlanexists = True
                    except meraki.APIError as e:
                        print(str(e))

                    if vlanexists is False:
                        dashboard.appliance.createNetworkApplianceVlan(newnetworkid, id=vlan['id'], name=vlan['name'],
                                                                       applianceIp=vlan['applianceIp'],
                                                                       subnet=vlan['subnet'])
                    dashboard.appliance.updateNetworkApplianceVlan(newnetworkid, vlan['id'], name=vlan['name'],
                                                                   applianceIp=vlan['applianceIp'],
                                                                   subnet=vlan['subnet'],
                                                                   fixedIpAssignments=vlan['fixedIpAssignments'],
                                                                   reservedIpRanges=vlan['reservedIpRanges'],
                                                                   dnsNameservers=vlan['dnsNameservers'],
                                                                   dhcpHandling=vlan['dhcpHandling'],
                                                                   dhcpLeaseTime=vlan['dhcpLeaseTime'],
                                                                   dhcpBootOptionsEnabled=vlan['dhcpBootOptionsEnabled'],
                                                                   dhcpOptions=vlan['dhcpOptions'])
                else:
                    if str(vlan['id']) not in ['1', '150', '151', '152', '153', '20', '60', '70', '80']:
                        if str(vlan['id']) == '10':
                            mxvlan = '125'
                        elif str(vlan['id']) == '30':
                            mxvlan = '135'
                        else:
                            mxvlan = vlan['id']
                        dashboard.appliance.updateNetworkApplianceVlan(newnetworkid, mxvlan,
                                                                       applianceIp=vlan['applianceIp'],
                                                                       subnet=vlan['subnet'],
                                                                       fixedIpAssignments=vlan['fixedIpAssignments'],
                                                                       reservedIpRanges=vlan['reservedIpRanges'])
            try:
                dashboard.appliance.updateNetworkApplianceFirewallOneToManyNatRules(newnetworkid, mxdevice.manynat['rules'])
            except meraki.APIError as e:
                print(str(e))
            try:
                dashboard.appliance.updateNetworkApplianceFirewallOneToOneNatRules(newnetworkid, mxdevice.onenat['rules'])
            except meraki.APIError as e:
                print(str(e))
            try:
                dashboard.appliance.updateNetworkApplianceFirewallPortForwardingRules(newnetworkid, mxdevice.portforward['rules'])
            except meraki.APIError as e:
                print(str(e))

        if runmode != 'Template':
            for msdevice in mslist:
                dashboard.devices.updateDevice(msdevice.serial, name=str(msdevice.name))
                for switchport in msdevice.ports:
                    if switchport['type'] == 'access':
                        if str(switchport['vlan']) == '10':
                            portvlan = '125'
                        elif str(switchport['vlan']) == '30':
                            portvlan = '135'
                        else:
                            portvlan = '120'
                        dashboard.switch.updateDeviceSwitchPort(msdevice.serial, switchport['portId'], name=switchport['name'],
                                                                tags=switchport['tags'], enabled=switchport['enabled'],
                                                                type=switchport['type'], vlan=portvlan,
                                                                voiceVlan='110',
                                                                poeEnabled=switchport['poeEnabled'],
                                                                isolationEnabled=switchport['isolationEnabled'],
                                                                rstpEnabled=switchport['rstpEnabled'],
                                                                stpGuard=switchport['stpGuard'],
                                                                linkNegotiation=switchport['linkNegotiation'],
                                                                portScheduleId=switchport['portScheduleId'],
                                                                udld=switchport['udld'],
                                                                accessPolicyType=switchport['accessPolicyType'],
                                                                )
                    else:
                        if str(switchport['vlan']) == '10':
                            portvlan = '125'
                        else:
                            portvlan = '1'
                        dashboard.switch.updateDeviceSwitchPort(msdevice.serial, switchport['portId'], name=switchport['name'],
                                                                tags=switchport['tags'], enabled=switchport['enabled'],
                                                                type=switchport['type'], vlan=portvlan,
                                                                allowedVlans=switchport['allowedVlans'],
                                                                poeEnabled=switchport['poeEnabled'],
                                                                isolationEnabled=switchport['isolationEnabled'],
                                                                rstpEnabled=switchport['rstpEnabled'],
                                                                stpGuard=switchport['stpGuard'],
                                                                linkNegotiation=switchport['linkNegotiation'],
                                                                portScheduleId=switchport['portScheduleId'],
                                                                udld=switchport['udld'],
                                                                accessPolicyType=switchport['accessPolicyType'],
                                                                )
        else:
            for msdevice in mslist:
                dashboard.devices.updateDevice(msdevice.serial, name=str(msdevice.name))
                for switchport in msdevice.ports:
                    if switchport['type'] == 'access':
                        dashboard.switch.updateDeviceSwitchPort(msdevice.serial, switchport['portId'], name=switchport['name'],
                                                                tags=switchport['tags'], enabled=switchport['enabled'],
                                                                type=switchport['type'], vlan=switchport['vlan'],
                                                                voiceVlan=switchport['voiceVlan'],
                                                                poeEnabled=switchport['poeEnabled'],
                                                                isolationEnabled=switchport['isolationEnabled'],
                                                                rstpEnabled=switchport['rstpEnabled'],
                                                                stpGuard=switchport['stpGuard'],
                                                                linkNegotiation=switchport['linkNegotiation'],
                                                                portScheduleId=switchport['portScheduleId'],
                                                                udld=switchport['udld'],
                                                                accessPolicyType=switchport['accessPolicyType'],
                                                                )
                    else:
                        dashboard.switch.updateDeviceSwitchPort(msdevice.serial, switchport['portId'], name=switchport['name'],
                                                                tags=switchport['tags'], enabled=switchport['enabled'],
                                                                type=switchport['type'], vlan=switchport['vlan'],
                                                                allowedVlans=switchport['allowedVlans'],
                                                                poeEnabled=switchport['poeEnabled'],
                                                                isolationEnabled=switchport['isolationEnabled'],
                                                                rstpEnabled=switchport['rstpEnabled'],
                                                                stpGuard=switchport['stpGuard'],
                                                                linkNegotiation=switchport['linkNegotiation'],
                                                                portScheduleId=switchport['portScheduleId'],
                                                                udld=switchport['udld'],
                                                                accessPolicyType=switchport['accessPolicyType'],
                                                                )

        for mrdevice in mrlist:
            dashboard.devices.updateDevice(mrdevice.serial, name=str(mrdevice.name))

        print('Configuration complete. Settings file can be found at ' + str(pathlib.Path().resolve()) + '\\' + configfilename)
    else:
        sys.exit(2)


if __name__ == '__main__':
    main(sys.argv[1:])

