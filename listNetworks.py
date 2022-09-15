import meraki
import getopt
import sys


def main(argv):
    dashboard = meraki.DashboardAPI(print_console=False, output_log=False, suppress_logging=True)  # Create session with Dashboard
    my_orgs = dashboard.organizations.getOrganizations()  # Get Orgs

    try:
        opts, args = getopt.getopt(argv, "a:")  # Collect cmd argument inputs
    except Exception as e:
        var = None
    for opt, arg in opts:
        if opt == '-a':
            orgname = arg

    for org in my_orgs:
        if org['name'] == orgname:
            #  Get the networks from the Org from last step
            orgnetworks = dashboard.organizations.getOrganizationNetworks(org['id'], total_pages='all')
    for network in orgnetworks:
        print(network['name'])


if __name__ == '__main__':
    main(sys.argv[1:])
