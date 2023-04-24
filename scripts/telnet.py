import telnetlib
import io_handler as io_h
import sys

HOST = "localhost"


def generate_interface_configuration_telnet(interface_name, ip_address, tn, ip_version=0, interface_intents={"vpn": False}):
    '''
    Configures a given interface over a telnet connection.

    Generates configurations of ipv4 and ipv6 interfaces. It also generates the configuration of the associated VRF if needed. 
    More details on the interface_intents can be found in the documentation. 
        Parameters:
                interface_name (str): the name of the interface (e.g. g1/0).
                ip_address (str): the ip address associated to the interface. It can be ipv4 or ipv6, and the mask has to be specified.
                tn (Telnet): the telnet connection used for the router.
                ip_version (int): (optional) the version of the ip address. If not specified, the configuration will be written for an interior interface (one that is not linked to a router outside of the AS), and the version will be the global version of the network. If specified, the configuration will be writtent for a border interface (one that communicates with the outside of the AS). 
                interface_intents (dict): (optional) a dictionnary that contains the intents of the specified interface. Required if the interface is outside of the AS.
    '''
    global AS_NUMBER
    global IGP
    global vrf_counter

    asbr = True
    literate_version = f'v{ip_version}' if ip_version == 6 else ""
    vpn_client_id = 0
    is_vpn = interface_intents["vpn"]
    if is_vpn:
        vpn_client_id = interface_intents["client_id"]
        remote_as = interface_intents["remote_AS"]

    if ip_version == 0:
        ip_version = IP_VERSION
        literate_version = v6
        asbr = False

    if vpn_client_id:
        tn.write(b'end\r\n')
        tn.write(b'end\r\n')
        tn.write(b'conf t\r\n')
        tn.write(str.encode(f'vrf definition {vrf_counter}\r\n'))
        tn.write(str.encode(f'rd {remote_as}:{vpn_client_id}\r\n'))
        tn.write(str.encode(f'address-family ipv{ip_version}\r\n'))
        tn.write(str.encode(
            f'route-target export {AS_NUMBER}:{vpn_client_id}\r\n'))
        tn.write(str.encode(
            f'route-target import {AS_NUMBER}:{vpn_client_id}\r\n'))
        if "vpn_list" in interface_intents:
            for client in interface_intents["vpn_list"]:
                tn.write(str.encode(
                    f'route-target import {AS_NUMBER}:{client}\r\n'))
        tn.write(b'exit\r\n')

        vrfs_list.append(vpn_client_id)
        vrf_counter += 1

    tn.write(b'end\r\n')
    tn.write(b'end\r\n')
    tn.write(b'conf t\r\n')
    tn.write(str.encode(f'int {interface_name}\r\n'))
    tn.write(b'no ip address\r\n')
    tn.write(b'no ipv6 address\r\n')
    if vpn_client_id:
        tn.write(str.encode(f'vrf forwarding {vrf_counter-1}\r\n'))

    if ip_version == 6:
        tn.write(b'ipv6 enable\r\n')

    tn.write(str.encode(f'ip{literate_version} address {ip_address}\r\n'))
    tn.write(b'no shutdown\r\n')
    tn.write(b'end\r\n')

    if not asbr:
        tn.write(b'conf t\r\n')
        tn.write(str.encode(f'int {interface_name}\r\n'))
        if IP_VERSION == 6:
            if IGP == 'RIP':
                tn.write(str.encode(f'no ipv6 ospf {AS_NUMBER} area 0\r\n'))
                tn.write(b'ipv6 rip ripng enable\r\n')
            if IGP == 'OSPF':
                tn.write(b'no ipv6 rip ripng enable\r\n')
                tn.write(str.encode(f'ipv6 ospf {AS_NUMBER} area 0\r\n'))
        if IP_VERSION == 4:
            tn.write(b'mpls ip\r\n')
            if IGP == 'RIP':
                tn.write(str.encode(f'no ip ospf {AS_NUMBER} area 0\r\n'))
                tn.write(b'ip rip ripng enable\r\n')
            if IGP == 'OSPF':
                tn.write(b'no ip rip ripng enable\r\n')
                tn.write(str.encode(f'ip ospf {AS_NUMBER} area 0\r\n'))
    tn.write(b'no shutdown\r\n')
    tn.write(b'end\r\n')
    tn.read_very_eager()


def generate_eBGP_interface_telnet(router_intents, tn):
    '''
      Configures the external BGP part of a given router over a telnet connection.
        Parameters:
            router_intents (dict): a dictionary with the routers intents. More details in the documentation.
            tn (Telnet): the telnet connection used for the router.
    '''
    global AS_NUMBER
    global IGP

    for ebgp_interfaces in router_intents["eBGP_config"]:
        interface = ebgp_interfaces["interface"]
        ip_address = ebgp_interfaces["IP_address"]
        ip_mask = ebgp_interfaces["link_mask"]
        ip_version = ebgp_interfaces["IP_version"]
        ip_address += f'/{ip_mask}' if ip_version == 6 else f' {ip_mask}'
        generate_interface_configuration_telnet(
            interface, ip_address, tn, ip_version, ebgp_interfaces)


def generate_loopback_configuration_telnet(loopback_address, tn):
    '''
    Configures a given loopback interface over a telnet connection.
    A router can have one loopback address.
        Parameters:
            loopback_address (str): the ip address of the loopback interface. It can be ipv4 or ipv6.
            tn (Telnet): the telnet connection used for the router.
    '''
    global AS_NUMBER
    global IGP
    global IP_MASK

    tn.write(b'end\r\n')
    tn.write(b'end\r\n')
    tn.write(b'conf t\r\n')
    tn.write(b'int Loopback0\r\n')
    tn.write(b'no ip address\r\n')
    tn.write(b'no ipv6 address\r\n')
    if IP_VERSION == 6:
        tn.write(str.encode(
            f'ipv6 address {loopback_address}/{IP_MASK+16}\r\n'))
        tn.write(b'ipv6 enable\r\n')
    if IP_VERSION == 4:
        tn.write(str.encode(
            f'ip address {loopback_address} 255.255.255.255\r\n'))
    tn.write(b'no shutdown\r\n')
    if IGP == 'RIP':
        tn.write(str.encode(f' ip{v6} rip ripng enable\r\n'))
    elif IGP == 'OSPF':
        tn.write(str.encode(f' ip{v6} ospf {AS_NUMBER} area 0\r\n'))

    tn.write(b'end\r\n')
    tn.read_very_eager()


def generate_cost_configuration_telnet(router_intents, tn):
    '''
      Configures the OSPF cost for a router's interfaces over a telnet connection. The router is specified via the router_intents parameter.
        Parameters:
            router_intents (dict): a dictionary describing the intents of the router. More details in the documentation.
            tn (Telnet): the telnet connection used for the router.
    '''
    if "cost_parameters" in router_intents:
        cost_parameters = router_intents["cost_parameters"]
        for cost_configuration in cost_parameters:
            cost = cost_configuration["cost"]
            interface = cost_configuration["interface"]
            tn.write(b'end\r\n')
            tn.write(b'end\r\n')
            tn.write(b'conf t\r\n')
            tn.write(str.encode(f'interface {interface}\r\n'))
            tn.write(str.encode(f'ipv6 ospf cost {cost}\r\n'))
            tn.write(b'end\r\n')
            tn.read_very_eager()


def generate_OSPF_configuration_telnet(router_number, tn):
    tn.write(b'end\r\n')
    tn.write(b'end\r\n')
    tn.write(b'conf t\r\n')
    tn.write(str.encode(f'ip{v6} router ospf {AS_NUMBER}\r\n'))
    tn.read_very_eager()
    if IP_VERSION == 6:
        tn.write(str.encode(
            f'router-id {router_number}.{router_number}.{router_number}.{router_number}\r\n'))
    if IP_VERSION == 4:
        tn.write(str.encode(f' router-id {loopback_address}\r\n'))

    tn.write(b'end\r\n')
    tn.read_very_eager()


def generate_RIP_configuration_telnet(tn):
    tn.write(b'end\r\n')
    tn.write(b'end\r\n')
    tn.write(b'conf t\r\n')
    tn.write(str.encode(f'ip{v6} router rip ripng\r\n'))
    tn.write(b'redistribute connected\r\n')
    tn.write(b'end\r\n')


def generate_eBGP_configuration_telnet(router_intents, tn):
    '''
      Configures the external BGP part of a given router over a telnet connection.
        Parameters:
            router_intents (dict): a dictionary with the routers intents. More details in the documentation.
            tn (Telnet): the telnet connection used for the router.
    '''
    global AS_NUMBER

    tn.write(b'end\r\n')
    tn.write(b'end\r\n')
    tn.write(b'conf t\r\n')
    tn.write(str.encode(f'router bgp {AS_NUMBER}\r\n'))

    for ebgp_neighbors in router_intents["eBGP_config"]:
        remote_address = ebgp_neighbors["remote_IP_address"]
        remote_as = ebgp_neighbors["remote_AS"]
        is_vpn_client = ebgp_neighbors["vpn"]
        if not is_vpn_client:
            tn.write(str.encode(
                f'neighbor {remote_address} remote-as {remote_as}\r\n'))

    for ebgp_neighbors in router_intents["eBGP_config"]:
        remote_address = ebgp_neighbors["remote_IP_address"]
        link_IP = ebgp_neighbors["link_IP"]
        ip_version = "v6" if ebgp_neighbors["IP_version"] == 6 else "v4"
        is_vpn_client = ebgp_neighbors["vpn"]
        remote_as = ebgp_neighbors["remote_AS"]

        if not is_vpn_client:
            tn.write(str.encode(f'address-family ip{ip_version}\r\n'))
            remote_address = ebgp_neighbors["remote_IP_address"]
            link_IP = ebgp_neighbors["link_IP"]
            link_mask = ebgp_neighbors["link_mask"]
            tn.write(str.encode(f'neighbor {remote_address} activate\r\n'))
            if ip_version == "v6":
                tn.write(str.encode(f'network {link_IP}\r\n'))
            else:
                tn.write(str.encode(f'network {link_IP} mask {link_mask}\r\n'))

        if is_vpn_client:
            vpn_client_id = ebgp_neighbors["client_id"]
            tn.write(str.encode(
                f'address-family ip{ip_version} vrf {vrfs_list.index(vpn_client_id)+1}\r\n'))
            tn.write(b'redistribute connected\r\n')
            tn.write(str.encode(
                f'neighbor {remote_address} remote-as {remote_as}\r\n'))
            tn.write(str.encode(f' neighbor {remote_address} activate\r\n'))

    tn.write(b'end\r\n')
    tn.read_very_eager()


def generate_BGP_policies_telnet(router_intents, tn):
    '''
      Configures the BGP policies part of a given router over a telnet connection. The BGP policies are the following:
        -  Local preference configuration
        -  BGP communities to choose to which neighbors a given route has to be advertised
        -  Filtering the private IP addresses
        -  AS prepending
                                   
        Parameters:
            router_intents (dict): a dictionary with the routers intents. More details in the documentation. 
            tn (Telnet): the telnet connection used for the router. 
    '''
    neighbor_count = 0
    for eBGP_neighbor in router_intents["eBGP_config"]:
        local_preference = eBGP_neighbor["local_preference"]
        community_in = eBGP_neighbor["community_in"]
        neighbor_IP_address = eBGP_neighbor["remote_IP_address"]
        neighbor_IP_version = eBGP_neighbor["IP_version"]
        version = "v6" if neighbor_IP_version == 6 else "v4"
        communities_out = []

        tn.write(b'end\r\n')
        tn.write(b'end\r\n')
        tn.write(b'conf t\r\n')
        for community in eBGP_neighbor["community_out"]:
            communities_out.append(community)
            tn.write(str.encode(
                f'ip community-list standard {community}_out permit {community}\r\n'))

        tn.write(b'ipv6 access-list private_ipv6_list\r\n')
        tn.write(b'permit ipv6 FD00::/8 any\r\n')

        tn.write(str.encode(
            f'no route-map map_in_{neighbor_count} permit 10\r\n'))
        tn.write(str.encode(
            f'route-map map_in_{neighbor_count} permit 10\r\n'))
        tn.write(str.encode(f'set community {community_in}\r\n'))
        tn.write(str.encode(f'set local-preference {local_preference}\r\n'))
        tn.write(b'exit\r\n')

        tn.write(str.encode(
            f'no route-map map_in_{neighbor_count} deny 1\r\n'))
        tn.write(str.encode(f'route-map map_in_{neighbor_count} deny 1\r\n'))
        tn.write(b'match ipv6 address private_ipv6_list\r\n')
        tn.write(b'exit\r\n')

        tn.write(str.encode(
            f'no route-map map_out_{neighbor_count} deny 10\r\n'))
        if len(communities_out) > 0:
            tn.write(str.encode(
                f'route-map map_out_{neighbor_count} deny 10\r\n'))
            for community in communities_out:
                tn.write(b'no match community\r\n')
                tn.write(str.encode(f'match community {community}_out\r\n'))
            tn.write(b'exit\r\n')

        tn.write(str.encode(
            f'route-map map_out_{neighbor_count} permit 100\r\n'))
        tn.write(b'exit\r\n')

        tn.write(str.encode(f'router bgp {AS_NUMBER}\r\n'))
        tn.write(str.encode(f'address-family ip{version}\r\n'))
        tn.write(str.encode(
            f'neighbor {neighbor_IP_address} route-map map_in_{neighbor_count} in\r\n'))
        tn.write(str.encode(
            f'neighbor {neighbor_IP_address} route-map map_out_{neighbor_count} out\r\n'))

        tn.write(b'end\r\n')
        tn.read_until(b'Configured from console by console')

        # AS-Path prepending configuration
        tn.write(b'conf t\r\n')
        if "AS_path_prepend" in eBGP_neighbor:
            tn.write(str.encode(
                f'route-map map_out_{neighbor_count} permit 5\r\n'))
            as_path_prepend = f'set as-path prepend '
            x = eBGP_neighbor["AS_path_prepend"]
            for _ in range(x):
                as_path_prepend += f'{AS_NUMBER} '
            tn.write(str.encode(as_path_prepend))

        tn.write(b'end\r\n')
        tn.read_very_eager()
        neighbor_count += 1


def generate_iBGP_configuration_telnet(router_number, tn):
    '''
    Configures the internal BGP part of a given router over a telnet connection.
        Parameters:
            router_number (int): the router's id.  
            tn (Telnet): the telnet connection used for the router. 
    '''
    global AS_NUMBER

    tn.write(b'end\r\n')
    tn.write(b'end\r\n')
    tn.write(b'conf t\r\n')
    tn.write(str.encode(f'router bgp {AS_NUMBER}\r\n'))
    tn.write(str.encode(
        f' bgp router-id {router_number}.{router_number}.{router_number}.{router_number}\r\n'))
    if IP_VERSION == 6:
        tn.write(b'no bgp default ipv4-unicast\r\n')
    for routers in NETWORK_ARCHITECTURE['architecture']:
        neighbor_number = routers['abstract_router_number']
        neighbor_loopback = routers['loopback_IP']
        if router_number != neighbor_number:
            tn.write(str.encode(
                f'neighbor {neighbor_loopback} remote-as {AS_NUMBER}\r\n'))
            tn.write(str.encode(
                f'neighbor {neighbor_loopback} update-source Loopback0\r\n'))

    tn.write(b'address-family ipv4\r\n')

    if IP_VERSION == 6:
        tn.write(b'address-family ipv6\r\n')

    for routers in NETWORK_ARCHITECTURE['architecture']:
        neighbor_number = routers['abstract_router_number']
        neighbor_loopback = routers['loopback_IP']
        if router_number != neighbor_number:
            tn.write(str.encode(f'neighbor {neighbor_loopback} activate\r\n'))
            tn.write(str.encode(
                f'neighbor {neighbor_loopback} send-community\r\n'))

    tn.write(b'exit\r\n')
    tn.write(b'address-family vpnv6\r\n')
    for routers in NETWORK_ARCHITECTURE['architecture']:
        neighbor_number = routers['abstract_router_number']
        neighbor_loopback = routers['loopback_IP']
        if router_number != neighbor_number:
            tn.write(str.encode(f'neighbor {neighbor_loopback} activate\r\n'))
            tn.write(str.encode(
                f'neighbor {neighbor_loopback} send-community extended\r\n'))

    tn.write(b'exit\r\n')
    tn.write(b'address-family vpnv4\r\n')
    for routers in NETWORK_ARCHITECTURE['architecture']:
        neighbor_number = routers['abstract_router_number']
        neighbor_loopback = routers['loopback_IP']
        if router_number != neighbor_number:
            tn.write(str.encode(f'neighbor {neighbor_loopback} activate\r\n'))
            tn.write(str.encode(
                f'neighbor {neighbor_loopback} send-community extended\r\n'))

    tn.write(b'end\r\n')
    tn.write(b'exit-address-family\r\n')
    tn.read_very_eager()


## MAIN STARTS HERE ##

if len(sys.argv) < 2:
    print('Provide the path of the intent file as an argument')
    sys.exit(1)

intent_path = sys.argv[1]

target_router = None
if len(sys.argv) == 3:
    try:
        int(sys.argv[2])
    except:
        print('Provide the desired router name as the id of this router (a number)')
        sys.exit(1)
    target_router = int(sys.argv[2])

link_ip_list = []
vrfs_list = []
vrf_counter = 1

AS_NUMBER, AS_INTENTS, ARCHITECTURE_PATH, IGP, IP_RANGE, IP_MASK, IP_VERSION = io_h.get_intents(
    intent_path)
v6 = "v6" if IP_VERSION == 6 else ""
v4 = "v4" if IP_VERSION == 4 else ""

router_intent_list = AS_INTENTS["routers"]
if target_router == None:
    print("Starting the configuration of the routers in AS", AS_NUMBER, "...")
else:
    print("Starting the configuration of router", target_router, "...")

NETWORK_ARCHITECTURE = io_h.generate_ip_address(
    ARCHITECTURE_PATH, IP_RANGE, IP_VERSION, IP_MASK)

for routers in NETWORK_ARCHITECTURE['architecture']:
    vrf_counter = 1
    vrfs_list = []
    # declaration of constants relative to the router
    router_number = routers['abstract_router_number']
    if target_router != None and target_router != router_number:
        continue
    router_name = f'i{router_number}'
    config_file_name = f'{router_name}_startup-config.cfg'
    router_intents = next(
        item for item in router_intent_list if item['router_number'] == router_number)

    router_port = router_intents["telnet_port"]
    with telnetlib.Telnet(HOST, router_port) as tn:
        # clean up the terminal
        tn.write(b'\r\n')
        tn.write(b'\r\n')
        tn.read_very_eager()

        tn.write(b'conf t\r\n')
        tn.write(b'mpls label protocol ldp\r\n')
        tn.write(b'ipv6 unicast-routing\r\n')
        tn.write(b'end\r\n')
        tn.write(b'end\r\n')

        loopback_address = routers["loopback_IP"]
        generate_loopback_configuration_telnet(loopback_address, tn)
        # waits until the command was effectively interpreted
        tn.read_until(b'Configured from console by console')

        for neighbors in routers['neighbors']:
            interface_name = neighbors['interface']
            link_ip = neighbors['link_IP']
            if IP_VERSION == 6:
                ip_address = f'{link_ip}::{router_number}/{IP_MASK+16}'
            elif IP_VERSION == 4:
                address_suffix = 1
                if link_ip in link_ip_list:
                    address_suffix = 2
                else:
                    link_ip_list.append(link_ip)

                # link ips are hardwritten in 32 mask for now
                ip_address = f'{link_ip}.{address_suffix} 255.255.255.252'

            generate_interface_configuration_telnet(interface_name, ip_address, tn)
            tn.read_until(b'Configured from console by console')

        generate_cost_configuration_telnet(router_intents, tn)
        if "eBGP" in router_intents:
            generate_iBGP_configuration_telnet(router_number, tn)
            tn.read_until(b'Configured from console by console')

            generate_eBGP_interface_telnet(router_intents, tn)
            tn.read_until(b'Configured from console by console')

            generate_eBGP_configuration_telnet(router_intents, tn)
            tn.read_until(b'Configured from console by console')

            generate_BGP_policies_telnet(router_intents, tn)
            tn.read_until(b'Configured from console by console')

        if IGP == "OSPF":
            generate_OSPF_configuration_telnet(router_number, tn)

        if IGP == 'RIP':
            generate_RIP_configuration_telnet(tn)

    print("Router", router_name, "done!")

print("All routers have been configured!")
