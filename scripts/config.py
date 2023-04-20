import io_handler as io_h
import json
import os
import sys


def generate_header(hostname):
    '''
    Returns the header of the router's configuration file. This header is pretty much always the same, and only the hostname changes.
        Parameters: 
                hostname (str): the name of the router
        Returns:
               generate_header (str): the header of the router's configuration file

    '''
    CONSTANT_VERBOSE_1 = f'version 15.2\nservice timestamps debug datetime msec\nservice timestamps log datetime msec\n!\nhostname {hostname}'
    CONSTANT_VERBOSE_2 = '\n!\nboot-start-marker\nboot-end-marker\nno aaa new-model\nno ip icmp rate-limit unreachable\nip cef\nno ip domain lookup\nipv6 unicast-routing\nipv6 cef\nmultilink bundle-name authenticated\nip tcp synwait-time 5\n!\n!\n!\n!\n!\n'

    return CONSTANT_VERBOSE_1 + CONSTANT_VERBOSE_2 + (('mpls label protocol ldp\n!\n') if IP_VERSION == 4 else "")


def generate_footer():
    '''
    Returns the footer of the router's configuration file. The footer is always the same.
        Parameters: 
                -
        Returns:
               generate_footer(str): a string representing the footer of the router's configuration file
    '''
    footer = '!\n'
    footer += 'control plane\n'
    footer += '!\n'
    footer += 'ip forward-protocol nd\n'
    footer += '!\n'
    footer += '!\n'
    footer += 'no ip http server\n'
    footer += 'no ip http secure-server\n'
    footer += '!\n'
    footer += '!\n'
    footer += 'line con 0\n'
    footer += ' exec-timeout 0 0\n'
    footer += ' privilege level 15\n'
    footer += ' logging synchronous\n'
    footer += ' stopbits 1\n'
    footer += 'line aux 0\n'
    footer += ' exec-timeout 0 0\n'
    footer += ' privilege level 15\n'
    footer += ' logging synchronous\n'
    footer += ' stopbits 1\n'
    footer += 'line vty 0 4\n'
    footer += ' login\n'
    footer += '!\n'
    footer += '!\n'
    footer += 'end'

    return footer


def generate_interface_configuration(interface_name, ip_address, ip_version=0, interface_intents={"vpn":False}):
    '''
    Returns the configuration of a given interface as a string. 

    Generates configurations of ipv4 and ipv6 interfaces. It also generates the configuration of the associated VRF if needed. 
    More details on the interface_intents can be found in the documentation. 
        Parameters:
                interface_name (str): the name of the interface (e.g. g1/0).
                ip_address (str): the ip address associated to the interface. It can be ipv4 or ipv6, and the mask has to be specified.
                ip_version (int): (optional) the version of the ip address. If not specified, the configuration will be written for an interior interface (one that is not linked to a router outside of the AS), and the version will be the global version of the network. If specified, the configuration will be writtent for a border interface (one that communicates with the outside of the AS). 
                interface_intents (dict): (optional) a dictionnary that contains the intents of the specified interface. Required if the interface is outside of the AS.
        Returns:
                interface_config (str): the configuration of the interface as a string
    '''
    global AS_NUMBER
    global IGP
    global vrf_counter
    
    asbr = True
    literate_version = f'v{ip_version}' if ip_version == 6 else ""
    interface_config = ''
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
        interface_config += f'vrf definition {vrf_counter}\n' 
        interface_config += f' rd {remote_as}:{vpn_client_id}\n'
        interface_config += f' address-family ipv{ip_version}\n'
        interface_config += f' route-target export {AS_NUMBER}:{vpn_client_id}\n'
        interface_config += f' route-target import {AS_NUMBER}:{vpn_client_id}\n'
        if "vpn_list" in interface_intents:
            for client_id in interface_intents["vpn_list"]:
                interface_config += f' route-target import {AS_NUMBER}:{client_id}\n' 
        interface_config += f' exit-address-family\n'
        interface_config += '!\n'
        vrfs_list.append(vpn_client_id)
        vrf_counter += 1

    interface_config += f'interface {interface_name}\n'
    if vpn_client_id:
        interface_config +=f" vrf forwarding {vrf_counter-1}\n" 
    interface_config += ' no ip address\n'
    # verbose constants depending on the interface type
    interface_config += ' duplex full\n' if interface_name == 'fe0/0' else ' negotiation auto\n'

    interface_config += f' ip{literate_version} address {ip_address}\n'
    
    if ip_version == 6:
        interface_config += ' ipv6 enable\n'

    if not asbr:
        if ip_version == 4:
            interface_config += ' mpls ip\n'
        interface_config += f' ip{literate_version} rip ripng enable\n' if not asbr and IGP == 'RIP' else ''
        if IGP == 'OSPF':
            interface_config += f' ip{literate_version} ospf {AS_NUMBER} area 0\n' 
        else : ''
    interface_config += '!\n'
    
    return interface_config

def generate_cost_configuration(router_intents):
    '''
      Returns the OSPF cost configuration for a router's interfaces. The router is specified via the router_intents parameter.
        Parameters:
                router_intents (dict): a dictionary describing the intents of the router. More details in the documentation.
        Method: 

        Returns:
            cost_config (str): the OSPF cost of each interface for the given router.
    '''
    cost_config=''
    if "cost_parameters" in router_intents:
        cost_parameters = router_intents["cost_parameters"]
        for cost_configuration in cost_parameters:
            cost = cost_configuration["cost"]
            interface = cost_configuration["interface"]
            cost_config += f'interface {interface}\n'
            cost_config += f'ip{v6} ospf cost {cost}\n!\n'
    return cost_config

def generate_loopback_configuration(loopback_address):
    '''
    Returns configuration of a given loopback interface as a string.
    One router can have only one loopback address.

        Parameters:
                loopback_address (str): the ip address of the loopback interface. It can be ipv4 or ipv6.
         Returns:
                loopback_config (str): the configuration of the loopback interface. 
    '''
    global AS_NUMBER
    global IGP
    global IP_MASK

    loopback_config = 'interface Loopback0\n no ip address\n'

    if IP_VERSION == 6:
        loopback_config += f' ipv6 address {loopback_address}/{IP_MASK+16}\n'
        loopback_config += ' ipv6 enable\n'
    elif IP_VERSION == 4:
        loopback_config += f' ip address {loopback_address} 255.255.255.255\n'
    # extra config if RIP router
    loopback_config += f' ip{v6} rip ripng enable\n' if IGP == 'RIP' else ''
    # extra config if OSPF router
    loopback_config += f' ip{v6} ospf {AS_NUMBER} area 0\n' if IGP == 'OSPF' else ''
    loopback_config += '!\n'

    return loopback_config


def generate_iBGP_configuration(router_number):
    '''
    Returns the internal BGP configuration of a given router.
        Parameters:
               router_number (int): the router's id.  
         Returns:
                iBGP_config (str): the iBGP configuration of the router
    '''
    global AS_NUMBER
    iBGP_config = ''
    iBGP_config = f'router bgp {AS_NUMBER}\n'
    iBGP_config += f' bgp router-id {router_number}.{router_number}.{router_number}.{router_number}\n'
    iBGP_config += ' bgp log-neighbor-changes\n'
    iBGP_config += ' no bgp default ipv4-unicast\n' if IP_VERSION == 6 else ""
    for routers in NETWORK_ARCHITECTURE['architecture']:
        neighbor_number = routers['abstract_router_number']
        neighbor_loopback_address = routers['loopback_IP']
        if router_number != neighbor_number:
            iBGP_config += f' neighbor {neighbor_loopback_address} remote-as {AS_NUMBER}\n'
            iBGP_config += f' neighbor {neighbor_loopback_address} update-source Loopback0\n'

    iBGP_config += '!\n'
    iBGP_config += f'address-family ipv4\n'

    if v6:
        iBGP_config += '!\n'
        iBGP_config += f'address-family ipv6\n'

    for routers in NETWORK_ARCHITECTURE['architecture']:
        neighbor_number = routers['abstract_router_number']
        neighbor_loopback_address = routers['loopback_IP']
        if router_number != neighbor_number:
            iBGP_config += f' neighbor {neighbor_loopback_address} activate\n'
            iBGP_config += f' neighbor {neighbor_loopback_address} send-community\n'

    iBGP_config += '!\naddress-family vpnv6\n'

    for routers in NETWORK_ARCHITECTURE['architecture']:
            neighbor_number = routers['abstract_router_number']
            neighbor_loopback_address = routers['loopback_IP']
            if router_number != neighbor_number:
                iBGP_config += f' neighbor {neighbor_loopback_address} activate\n'
                iBGP_config += f' neighbor {neighbor_loopback_address} send-community extended\n'

    iBGP_config += '!\naddress-family vpnv4\n'

    for routers in NETWORK_ARCHITECTURE['architecture']:
            neighbor_number = routers['abstract_router_number']
            neighbor_loopback_address = routers['loopback_IP']
            if router_number != neighbor_number:
                iBGP_config += f' neighbor {neighbor_loopback_address} activate\n'
                iBGP_config += f' neighbor {neighbor_loopback_address} send-community extended\n'

    iBGP_config += 'exit-address-family\n'
    iBGP_config += '!\n'

    return iBGP_config


def generate_eBGP_configuration(router_intents):
    '''
      Returns the external BGP configuration of a given router.
        Parameters:
            router_intents (dict): a dictionary with the routers intents. More details in the documentation.
        Returns:
            eBGP_config (str): the configuration of the external BGP for the router.
    '''
    global AS_NUMBER

    eBGP_config = f'router bgp {AS_NUMBER}\n'
    for ebgp_neighbors in router_intents["eBGP_config"]:
        remote_address = ebgp_neighbors["remote_IP_address"]
        is_vpn_client = ebgp_neighbors["vpn"]
        remote_as = ebgp_neighbors["remote_AS"]
        eBGP_config += f' neighbor {remote_address} remote-as {remote_as}\n' if not is_vpn_client else ''

    for ebgp_neighbors in router_intents["eBGP_config"]:
        remote_address = ebgp_neighbors["remote_IP_address"]
        remote_as = ebgp_neighbors["remote_AS"]
        ip_v = "v6" if ebgp_neighbors["IP_version"] == 6 else "v4"
        is_vpn_client = ebgp_neighbors["vpn"]
        if not is_vpn_client:
            eBGP_config += '!\n'
            eBGP_config += f'address-family ip{ip_v}\n'
            remote_address = ebgp_neighbors["remote_IP_address"]
            link_IP = ebgp_neighbors["link_IP"]
            link_mask = ebgp_neighbors["link_mask"]
            eBGP_config += f' neighbor {remote_address} activate\n'
            eBGP_config += f' network {link_IP}\n' if ip_v == "v6" else f' network {link_IP} mask {link_mask}\n!\n'
        if is_vpn_client:
            vpn_client_id = ebgp_neighbors["client_id"]
            print(vrfs_list, vrfs_list.index(vpn_client_id), vpn_client_id)
            eBGP_config += f"!\naddress-family ip{ip_v} vrf {vrfs_list.index(vpn_client_id)+1}\n" 
            eBGP_config += f' redistribute connected\n'
            eBGP_config += f' neighbor {remote_address} remote-as {remote_as}\n'
            eBGP_config += f' neighbor {remote_address} activate\n!\n'

    eBGP_config += 'exit-address-family\n!\n'

    return eBGP_config


def generate_eBGP_interface(router_intents):
    '''
      Returns the configuration of an eBGP interface (that is, an interface outside of the AS).
        Parameters:
            router_intents (dict): a dictionary with the routers intents. More details in the documentation.
        Returns:
            interface_config (str): the configuration of the interface.
    '''
    global AS_NUMBER
    global IGP
    global vrf_counter
    
    interface_config = ''
    for ebgp_interface in router_intents["eBGP_config"]:
        interface = ebgp_interface["interface"]
        ip_address = ebgp_interface["IP_address"]
        ip_mask = ebgp_interface["link_mask"]
        ip_version = ebgp_interface["IP_version"]
        ip_address += f'/{ip_mask}' if ip_version == 6 else f' {ip_mask}'
        interface_config += generate_interface_configuration(interface, ip_address, ip_version, ebgp_interface)

    return interface_config


def generate_BGP_policies(router_intents):
    '''
      Returns the BGP policies' configuration. The BGP policied are the following:
        -  Local preference configuration
        -  BGP communities to choose to which neighbors a given route has to be advertised
        -  Filtering the private IP addresses
        -  AS prepending
                                   
        Parameters:
            router_intents (dict): a dictionary with the routers intents. More details in the documentation.  
        Returns:
            BGP_configuration (str): the configuration for the BGP policies.  
    '''
    BGP_configuration = ''
    neighbor_count = 0 # for different route map names
    for eBGP_neighbor in router_intents["eBGP_config"]: 
        local_preference = eBGP_neighbor["local_preference"]
        community_in = eBGP_neighbor["community_in"]
        neighbor_IP_address = eBGP_neighbor["remote_IP_address"]
        neighbor_IP_version = eBGP_neighbor["IP_version"]
        version = "v6" if neighbor_IP_version == 6 else "v4"
        communities_out = []
        for community in eBGP_neighbor["community_out"]:
            communities_out.append(community)
            BGP_configuration += f'ip community-list standard {community}_out permit {community}\n'

        BGP_configuration += '!\n'
        BGP_configuration += f'ipv6 access-list private_ipv6_list\n'
        BGP_configuration += f' permit ipv6 FD00::/8 any \n'
        BGP_configuration += '!\n'
        BGP_configuration += f'route-map map_in_{neighbor_count} permit 10\n'
        BGP_configuration += f' set community {community_in}\n'
        BGP_configuration += f' set local-preference {local_preference}\n'
        BGP_configuration += '!\n'
        BGP_configuration += f'route-map map_in_{neighbor_count} deny 1\n'
        BGP_configuration += f' match ipv6 address private_ipv6_list\n'
        BGP_configuration += '!\n'
        if len(communities_out) > 0:
            BGP_configuration += f'route-map map_out_{neighbor_count} deny 10\n'
            for community in communities_out:
                BGP_configuration += f' match community {community}_out\n'

        BGP_configuration += '!\n'
        BGP_configuration += f'route-map map_out_{neighbor_count} permit 100\n!\n'

        BGP_configuration += f'router bgp {AS_NUMBER}\n'
        BGP_configuration += f'address-family ip{version}\n'
        BGP_configuration += f' neighbor {neighbor_IP_address} route-map map_in_{neighbor_count} in\n'
        BGP_configuration += f' neighbor {neighbor_IP_address} route-map map_out_{neighbor_count} out\n' 
        BGP_configuration += 'exit-address-family\n!\n'

        #AS-Path prepending configuration 
        if "AS_path_prepend" in eBGP_neighbor:
            BGP_configuration += f"route-map map_out_{neighbor_count} permit 5\n"
            BGP_configuration += f' set as-path prepend '
            x = eBGP_neighbor["AS_path_prepend"] # bad variable name but it is only used in one line and i am lazy
            for _ in range(x):
                BGP_configuration+= f'{AS_NUMBER} '
            BGP_configuration += '\n!\n'

        neighbor_count +=1

    return BGP_configuration

## MAIN STARTS HERE ##

if len(sys.argv) != 2:
    print('Provide the path of the intent file as an argument')
    sys.exit(1)

intent_path = sys.argv[1]

AS_NUMBER, AS_INTENTS, ARCHITECTURE_PATH, IGP, IP_RANGE, IP_MASK, IP_VERSION = io_h.get_intents(
    intent_path)
router_intent_list = AS_INTENTS["routers"]
print("Generating the configuration of AS", AS_NUMBER, "...") # good customer experience ^^

v6 = "v6" if IP_VERSION == 6 else ""
v4 = "v4" if IP_VERSION == 4 else ""
vrf_counter = 1

NETWORK_ARCHITECTURE = io_h.generate_ip_address(ARCHITECTURE_PATH, IP_RANGE, IP_VERSION, IP_MASK)

json_output_path, configs_parent_directory = io_h.handle_output(AS_NUMBER)

link_ip_list = []
vrfs_list = []

# construction of the configuration files
for router in NETWORK_ARCHITECTURE['architecture']:
    vrf_counter = 1 # resetting the vrf counter for each router
    vrfs_list = [] # resetting the vrfs list for each router 
    # declaration of constants relative to the router
    router_number = router['abstract_router_number']
    router_name = f'i{router_number}'
    config_file_name = f'{router_name}_startup-config.cfg'
    router_intents = next(
        item for item in router_intent_list if item['router_number'] == router_number) # parsing in python is... interesting
    output_path = os.path.join(configs_parent_directory, config_file_name)

    # opening the file the script is going to write the configuration into
    with open(output_path, 'w') as config_file:
        # Writing header
        config_file.write(generate_header(router_name))

        # Writing configuration of the loopback interface
        loopback_address = router["loopback_IP"]
        config_file.write(generate_loopback_configuration(
            loopback_address))

        for neighbor in router['neighbors']:
            # Writing the configuration of the non-ebgp interfaces
            interface_name = neighbor['interface']
            link_ip = neighbor['link_IP']
            ip_address = ''
            if IP_VERSION == 6:
                ip_address = f'{link_ip}::{router_number}/{IP_MASK+16}'
            elif IP_VERSION == 4:
                address_suffix = 1
                if link_ip in link_ip_list:
                    address_suffix = 2
                else:
                    link_ip_list.append(link_ip)

                ip_address = f'{link_ip}.{address_suffix} 255.255.255.252' # link ips are hardwritten is 32 mask for now
                
            neighbor.update({"ip_address": ip_address})
            config_file.write(generate_interface_configuration(
                interface_name, ip_address))
        config_file.write(generate_cost_configuration(router_intents))


        if "eBGP" in router_intents:
            # specific iBGP configuration for eBGP routers
            config_file.write(generate_iBGP_configuration(
                router_number))

            # specific interface configuration on eBGP interfaces
            config_file.write(generate_eBGP_interface(
                router_intents))

            # configuration of the eBGP neighbors
            config_file.write(generate_eBGP_configuration(
                router_intents))

            config_file.write(generate_BGP_policies(router_intents))


        # extra config if OSPF router
        if IGP == "OSPF":
            ospf_config = f'ipv6 ' if IP_VERSION == 6 else ''
            ospf_config += f'router ospf {AS_NUMBER}\n'
            if IP_VERSION == 6:
                ospf_config += f' router-id {router_number}.{router_number}.{router_number}.{router_number}\n'
            elif IP_VERSION == 4:
                ospf_config += f' router-id {loopback_address}\n'
            ospf_config += ' default-information originate always\n!\n'
            config_file.write(ospf_config)

        if IGP == 'RIP':
            rip_config = 'ipv6 router rip ripng\n'
            rip_config += ' redistribute connected\n!\n'
            config_file.write(rip_config)

        # writing footer
        config_file.write(generate_footer())


# save the config in a json file (primarly for debugging, but also for good customer experience ^^ lol)
with open(json_output_path, 'w') as json_file:
    json.dump(NETWORK_ARCHITECTURE, json_file,
              indent=4,
              separators=(',', ': '))

print("Done! The configuration of each router is located at",
      configs_parent_directory) # yet another 'good customer experience' feature. god I love these.
