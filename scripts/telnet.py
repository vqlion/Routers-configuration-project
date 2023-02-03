import telnetlib
import io_handler as io_h
import sys

HOST = "localhost"

def generate_interface_configuration(interface_name, ip_address, tn, asbr=False):
    # returns the configuration of the interface
    # parameters:
    # interface_name: the name of the interface
    # ip_address: the ip address of the interface
    # asbr: a boolean set to True if the router is an asbr
    '''
    Returns the configuration of each interface 
        Parameters:
                interface_name(str): a string
                ip_address(str)    : a string
                absr(boolean)      : a boolean value if the router is an autonomous system border router (only for OSPF and RIP)
        Returns:
                generate_interface_configuration(str): A String on multiple lines which is the configuration of each interface
    '''
    global AS_NUMBER
    global IGP

    tn.write(b'end\r\n')
    tn.write(b'end\r\n')
    tn.write(b'conf t\r\n')
    tn.write(str.encode(f'int {interface_name}\r\n'))
    tn.write(b'no ip address\r\n')
    tn.write(b'no ipv6 address\r\n')
    tn.write(str.encode(f'ipv6 address {ip_address}\r\n'))
    tn.write(b'ipv6 enable\r\n')
    if not asbr:
        if IGP == 'RIP':
            tn.write(str.encode(f'no ipv6 ospf {AS_NUMBER} area 0\r\n'))
            tn.write(b'ipv6 rip ripng enable\r\n')
        if IGP == 'OSPF':
            tn.write(str.encode(f'ipv6 ospf {AS_NUMBER} area 0\r\n'))
            tn.write(b'no ipv6 rip ripng enable\r\n')
    tn.write(b'no shutdown\r\n')
    tn.write(b'end\r\n')

def generate_eBGP_interface(router_intents, tn):
    # returns the configuration of an eBGP interface
    # parameters:
    # router_intents: a dictionnary containing the eBGP intents of the interface
    '''
      Returns the external BGP configuration of the interface 
        Parameters:
            router_intents(): a dictionary which contains the actual commands for eBGP configuration for an interface
        Returns:
            generate_eBGP_interface(str): A String on multiple lines which is the configuration of the external BGP for each interface 
    '''
    global AS_NUMBER
    global IGP

    ASBR = True
    interface_config = ''
    for ebgp_interfaces in router_intents["eBGP_config"]:
        interface = ebgp_interfaces["interface"]
        ip_address = ebgp_interfaces["IP_address"]
        ip_mask = ebgp_interfaces["link_mask"]
        ip_address += f'/{ip_mask}'
        generate_interface_configuration(interface, ip_address, tn, ASBR)

def generate_loopback_configuration(loopback_address, tn):
    # returns the configuration of a loopback interface
    # parameters:
    # loopback_address: the loopback_address
    '''
    Returns the loopback configuration for each AS 
        Parameters:
                loopback_address(str): an unique string 
         Returns:
                generate_loopback_configuration(str): A String on multiple lines which configures the loopback address for each AS
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
    tn.write(str.encode(f'ipv6 address {loopback_address}/{IP_MASK+16}\r\n'))
    tn.write(b'ipv6 enable\r\n')
    if IGP == 'RIP':
        tn.write(str.encode(f'no ipv6 ospf {AS_NUMBER} area 0\r\n'))
        tn.write(b'ipv6 rip ripng enable\r\n')
    if IGP == 'OSPF':
        tn.write(b'no ipv6 rip ripng enable\r\n')
        tn.write(str.encode(f'ipv6 ospf {AS_NUMBER} area 0\r\n'))
    tn.write(b'no shutdown\r\n')
    tn.write(b'end\r\n')
    tn.read_very_eager()

def generate_cost_configuration(router_intents, tn):
    '''
      Returns the cost of the network configuration
        Parameters:
                router_intents(): a dictionary 
        Method: 

        Returns:
            generate_cost_configuration(str): A String which is the cost for each interface in the OSPF
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

def generate_OSPF_configuration(router_number, tn):
    tn.write(b'end\r\n')
    tn.write(b'end\r\n')
    tn.write(b'conf t\r\n')
    tn.write(str.encode(f'ipv6 router ospf {AS_NUMBER}\r\n'))
    tn.read_very_eager()
    tn.write(str.encode(f'router-id {router_number}.{router_number}.{router_number}.{router_number}\r\n'))
    tn.write(b'end\r\n')
    tn.read_very_eager()

def generate_RIP_configuration(tn):
    tn.write(b'end\r\n')
    tn.write(b'end\r\n')
    tn.write(b'conf t\r\n')
    tn.write(b'ipv6 router rip ripng\r\n')
    tn.write(b'redistribute connected\r\n')
    tn.write(b'end\r\n')

def generate_eBGP_configuration(router_intents, tn):
    '''
      Returns the external BGP configuration 
        Parameters:
            router_intents(): a dictionary which contains the actual commands for eBGP configuration for a router 
        Returns:
            generate_eBGP_configuration(str): A String on multiple lines which is the configuration of the external BGP for each router
    '''
    # returns the eBGP configuration of a router's interface
    # parameters:
    # router_intents: a dictionnary containing the eBGP intents of the interface
    global AS_NUMBER

    tn.write(b'end\r\n')
    tn.write(b'end\r\n')
    tn.write(b'conf t\r\n')
    tn.write(str.encode(f'router bgp {AS_NUMBER}\r\n'))

    for ebgp_neighbors in router_intents["eBGP_config"]:
        remote_address = ebgp_neighbors["remote_IP_address"]
        remote_as = ebgp_neighbors["remote_AS"]
        tn.write(str.encode(f'neighbor {remote_address} remote-as {remote_as}\r\n'))
    
    tn.write(b'address-family ipv6\r\n')

    for ebgp_neighbors in router_intents["eBGP_config"]:
        remote_address = ebgp_neighbors["remote_IP_address"]
        link_IP = ebgp_neighbors["link_IP"]
        tn.write(str.encode(f'neighbor {remote_address} activate\r\n'))
        tn.write(str.encode(f'network {link_IP}\r\n'))

    tn.write(str.encode(f'network {IP_RANGE}/{IP_MASK}\r\n'))
    tn.write(b'end\r\n')
    tn.read_until(b'Configured from console by console')

    tn.write(b'conf t\r\n')
    tn.write(str.encode(f'ipv6 route {IP_RANGE}/{IP_MASK} Null0\r\n'))

    tn.write(b'end\r\n')
    tn.read_very_eager()

def generate_BGP_policies(router_intents, tn):
    '''
      Returns the configuration of the 4 BGP policies:
        -  Local preference configuration
        -  Making the Communities
        -  Filtering the private IP addresses
        -  AS prepanding
                                   
        Parameters:
            router_intents(): a dictionary  
        Returns:
            generate_BGP_policies(str): A String on multiple lines which configures each BGP policy  
    '''
    count = 0
    for eBGP_neighbor in router_intents["eBGP_config"]: 
        local_preference = eBGP_neighbor["local_preference"]
        community_in = eBGP_neighbor["community_in"]
        neighbor_IP_address = eBGP_neighbor["remote_IP_address"]
        communities_out = []
        tn.write(b'end\r\n')
        tn.write(b'end\r\n')
        tn.write(b'conf t\r\n')
        for community in eBGP_neighbor["community_out"]:
            communities_out.append(community)
            tn.write(str.encode(f'ip community-list standard {community}_out permit {community}\r\n'))

        tn.write(b'ipv6 access-list private_ipv6_list\r\n')
        tn.write(b'permit ipv6 FD00::/8 any\r\n')

        tn.write(str.encode(f'no route-map map_in_{count} permit 10\r\n'))
        tn.write(str.encode(f'route-map map_in_{count} permit 10\r\n'))
        tn.write(str.encode(f'set community {community_in}\r\n'))
        tn.write(str.encode(f'set local-preference {local_preference}\r\n'))
        tn.write(b'exit\r\n')

        tn.write(str.encode(f'no route-map map_in_{count} deny 1\r\n'))
        tn.write(str.encode(f'route-map map_in_{count} deny 1\r\n'))
        tn.write(b'match ipv6 address private_ipv6_list\r\n')
        tn.write(b'exit\r\n')

        tn.write(str.encode(f'no route-map map_out_{count} deny 10\r\n'))
        if len(communities_out) > 0:
            tn.write(str.encode(f'route-map map_out_{count} deny 10\r\n'))
            for community in communities_out:
                tn.write(b'no match community\r\n')
                tn.write(str.encode(f'match community {community}_out\r\n'))
            tn.write(b'exit\r\n')

        tn.write(str.encode(f'route-map map_out_{count} permit 100\r\n'))
        tn.write(b'exit\r\n')

        tn.write(str.encode(f'router bgp {AS_NUMBER}\r\n'))
        tn.write(b'address-family ipv6\r\n')
        tn.write(str.encode(f'neighbor {neighbor_IP_address} route-map map_in_{count} in\r\n'))
        tn.write(str.encode(f'neighbor {neighbor_IP_address} route-map map_out_{count} out\r\n'))

        tn.write(b'end\r\n')
        tn.read_until(b'Configured from console by console')

        #AS-Path prepending configuration 
        tn.write(b'conf t\r\n')
        if "AS_path_prepend" in eBGP_neighbor:
            tn.write(str.encode(f'route-map map_out_{count} permit 5\r\n'))
            as_path_prepend = f'set as-path prepend '
            x = eBGP_neighbor["AS_path_prepend"]
            for _ in range(x):
                as_path_prepend += f'{AS_NUMBER} '
            tn.write(str.encode(as_path_prepend))

        tn.write(b'end\r\n')
        tn.read_very_eager()
        count += 1


def generate_iBGP_configuration(router_number, eBGP_asbr, tn):
    # returns the iBGP configuration of the router
    # parameters:
    # router_number: the id of the router
    # eBGP: a boolean set to true if the router is an ASBR
    '''
    Returns the internal BGP configuration for each AS 
        Parameters:
               router_number(str): an unique string 
               eBGP(boolean): a boolean value if the router is an autonomous system border router (R6, R7, R8, R9)
         Returns:
                generate_loopback_configuration(str): A String on multiple lines which configures the loopback address for each AS
    '''
    global AS_NUMBER

    tn.write(b'end\r\n')
    tn.write(b'end\r\n')
    tn.write(b'conf t\r\n')
    tn.write(str.encode(f'router bgp {AS_NUMBER}\r\n'))
    tn.write(str.encode(f' bgp router-id {router_number}.{router_number}.{router_number}.{router_number}\r\n'))
    tn.write(b'no bgp default ipv4-unicast\r\n')
    for routers in archi['architecture']:
        neighbor_number = routers['abstract_router_number']
        neighbor_loopback = routers['loopback_IP']
        if router_number != neighbor_number:
            tn.write(str.encode(f'neighbor {neighbor_loopback} remote-as {AS_NUMBER}\r\n'))
            tn.write(str.encode(f'neighbor {neighbor_loopback} update-source Loopback0\r\n'))

    tn.write(b'address-family ipv6\r\n')

    for routers in archi['architecture']:
        neighbor_number = routers['abstract_router_number']
        neighbor_loopback = routers['loopback_IP']
        if router_number != neighbor_number:
            tn.write(str.encode(f'neighbor {neighbor_loopback} activate\r\n'))
            tn.write(str.encode(f'neighbor {neighbor_loopback} send-community\r\n'))

    announced_networks = []
    for routers in archi['architecture']:
        if eBGP_asbr == False:
            for neighbors in routers["neighbors"]:
                neighbor_network = neighbors['link_IP']
                if not neighbor_network in announced_networks:
                    tn.write(str.encode(f'network {neighbor_network}::/{IP_MASK + 16}\r\n'))
                    announced_networks.append(neighbor_network)

    tn.write(b'end\r\n')
    tn.read_very_eager()
    

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

AS_NUMBER, AS_INTENTS, ARCHITECTURE_PATH, IGP, IP_RANGE, IP_MASK = io_h.get_intents(
    intent_path)
router_intent_list = AS_INTENTS["routers"]
if target_router == None: print("Starting the configuration of the routers in AS", AS_NUMBER, "...")
else: print("Starting the configuration of router", target_router, "...")

archi = io_h.generate_ip_address(ARCHITECTURE_PATH, IP_RANGE)

for routers in archi['architecture']:
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

        loopback_address = routers["loopback_IP"]
        generate_loopback_configuration(loopback_address, tn)
        tn.read_until(b'Configured from console by console') #waits until the command was effectively interpreted

        for neighbors in routers['neighbors']:
            interface_name = neighbors['interface']
            link_ip = neighbors['link_IP']
            ip_address = f'{link_ip}::{router_number}/{IP_MASK+16}'
            neighbors.update({"ip_address": ip_address})
            generate_interface_configuration(interface_name, ip_address, tn)
            tn.read_until(b'Configured from console by console')

        generate_cost_configuration(router_intents, tn)
        if "eBGP" in router_intents:
            generate_iBGP_configuration(router_number, True, tn)
            tn.read_until(b'Configured from console by console')

            generate_eBGP_interface(router_intents, tn)
            tn.read_until(b'Configured from console by console')

            generate_eBGP_configuration(router_intents, tn)
            tn.read_until(b'Configured from console by console')
            
            generate_BGP_policies(router_intents, tn)
            tn.read_until(b'Configured from console by console')

        else:
            generate_iBGP_configuration(router_number, False, tn)
            tn.read_until(b'Configured from console by console')

        if IGP == "OSPF":
            generate_OSPF_configuration(router_number, tn)
        
        if IGP == 'RIP':
            generate_RIP_configuration(tn)

    print("Router", router_name, "done!")

print("All routers have been configured!")