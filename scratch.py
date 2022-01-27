import meraki


def getnetworkid(_orgnetworks, _networkname):
    for network in _orgnetworks:
        if network['name'] == _networkname:
            return network['id']

class Switch:
    def __init__(self, serial, name, ports):
        self.serial = serial
        self.name = name
        self.ports = ports


def main():
    dashboard = meraki.DashboardAPI(print_console=False, output_log=False, suppress_logging=False)
    my_orgs = dashboard.organizations.getOrganizations()
    orgid = ''
    newnetworkname = 'LAB-FortM'
    claimlist = ['Q2QN-KUMG-BEVA', 'Q2PD-3GT8-WKKE', 'Q2HP-FYW2-PBP5']

    for org in my_orgs:
        if 'Compass Group Field Sites' in org['name']:
            orgid = org['id']

    orgnetworks = dashboard.organizations.getOrganizationNetworks(orgid, total_pages='all')

    newnetworkid = getnetworkid(orgnetworks, newnetworkname)

    # orgnetworks = dashboard.organizations.getOrganizationNetworks(orgid)
    name = dashboard.devices.getDevice('Q2QN-KUMG-BEVA')
    print(name)
    dashboard.devices.updateDevice('Q2QN-KUMG-BEVA', name=str(name['name']))


if __name__ == '__main__':
    main()