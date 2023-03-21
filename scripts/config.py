import io_handler as io_h
import json
import os
import sys


def generate_header(hostname):
    '''
    Returns the header by concatenating 2 string constants 
        Parameters: 
                hostname(str): an unique string 
        Returns:
               generate_header(str): A string which is the header of the network configuration

    '''
    CONSTANT_VERBOSE_1 = f'version 15.2\nservice timestamps debug datetime msec\nservice timestamps log datetime msec\n!\nhostname {hostname}'
    CONSTANT_VERBOSE_2 = '\n!\nboot-start-marker\nboot-end-marker\nno aaa new-model\nno ip icmp rate-limit unreachable\nip cef\nno ip domain lookup\nipv6 unicast-routing\nipv6 cef\nmultilink bundle-name authenticated\nip tcp synwait-time 5\n!\n!\n!\n!\n!\n'

    return CONSTANT_VERBOSE_1 + CONSTANT_VERBOSE_2 + (('mpls label protocol ldp\n!\n') if IP_VERSION == 4 else "")


def generate_footer():
    '''
    Returns the footer by concatenating multiple strings in one local variable
        Parameters(): 
                -
        Returns:
               generate_footer([literal]): returns a string which is the footer of the network configuration
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


def generate_interface_configuration(interface_name, ip_address, ip_v=0):
    '''
    Returns the configuration of each interface 
        Parameters:
                interface_name(str): a string
                ip_address(str)    : a string
                absr(boolean)      : a boolean flag if the router is an autonomous system border router (only for OSPF and RIP)
        Returns:
                generate_interface_configuration(str): A String on which is the configuration of each interface
    '''
    global AS_NUMBER
    global IGP

    asbr = True
    version = f'v{ip_v}' if ip_v == 6 else ""

    if ip_v == 0: 
        ip_v = IP_VERSION
        version = v6
        asbr = False

    interface_config = f'interface {interface_name}\n'
    interface_config += ' no ip address\n'
    # verbose constants depending on the interface type
    interface_config += ' duplex full\n' if interface_name == 'fe0/0' else ' negotiation auto\n'

    interface_config += f' ip{version} address {ip_address}\n'
    if ip_v == 6:
        interface_config += ' ipv6 enable\n'

    if not asbr:
        if ip_v == 4:
            interface_config += ' mpls ip\n'
        interface_config += f' ip{version} rip ripng enable\n' if not asbr and IGP == 'RIP' else ''
        if IGP == 'OSPF':
            interface_config += f' ip{version} ospf {AS_NUMBER} area 0\n' 
        else : ''
    interface_config += '!\n'

    return interface_config

def generate_cost_configuration(router_intents):
    '''
      Returns the cost of the network configuration
        Parameters:
                router_intents(): a dictionary 
        Method: 

        Returns:
            generate_cost_configuration(str): A String which is the cost for each interface in the OSPF
    '''
    cost_config=''
    if "cost_parameters" in router_intents:
        cost_parameters = router_intents["cost_parameters"]
        for cost_configuration in cost_parameters:
            cost=cost_configuration["cost"]
            interface=cost_configuration["interface"]
            cost_config += f'interface {interface}\n'
            cost_config += f'ip{v6} ospf cost {cost}\n!\n'
    return cost_config

def generate_loopback_configuration(loopback_address):
    '''
    Returns the loopback configuration 
        Parameters:
                loopback_address(str): an unique string 
         Returns:
                generate_loopback_configuration(str): A String on which configures the loopback address 
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


def generate_iBGP_configuration(router_number, eBGP_asbr):
    '''
    Returns the internal BGP configuration for each AS 
        Parameters:
               router_number(str): an unique string 
               eBGP(boolean): a boolean value if the router is an autonomous system border router
         Returns:
                generate_iBGP_configuration(str): A String which configures the iBGP configuration of the router
    '''
    global AS_NUMBER
    iBGP_config = ''
    if eBGP_asbr:
        iBGP_config = f'router bgp {AS_NUMBER}\n'
        iBGP_config += f' bgp router-id {router_number}.{router_number}.{router_number}.{router_number}\n'
        iBGP_config += ' bgp log-neighbor-changes\n'
        iBGP_config += ' no bgp default ipv4-unicast\n' if IP_VERSION == 6 else ""
        for routers in archi['architecture']:
            neighbor_number = routers['abstract_router_number']
            neighbor_loopback = routers['loopback_IP']
            if router_number != neighbor_number:
                iBGP_config += f' neighbor {neighbor_loopback} remote-as {AS_NUMBER}\n'
                iBGP_config += f' neighbor {neighbor_loopback} update-source Loopback0\n'

        iBGP_config += '!\n'
        iBGP_config += f'address-family ipv4\n'

        if v6:
            iBGP_config += '!\n'
            iBGP_config += f'address-family ipv6\n'

        for routers in archi['architecture']:
            neighbor_number = routers['abstract_router_number']
            neighbor_loopback = routers['loopback_IP']
            if router_number != neighbor_number:
                iBGP_config += f' neighbor {neighbor_loopback} activate\n'
                iBGP_config += f' neighbor {neighbor_loopback} send-community\n'

        announced_networks = []
        for routers in archi['architecture']:
            if eBGP_asbr == False:
                for neighbors in routers["neighbors"]:
                    neighbor_network = neighbors['link_IP']
                    if not neighbor_network in announced_networks:
                        iBGP_config += f' network {neighbor_network}::/{IP_MASK + 16}\n'
                        announced_networks.append(neighbor_network)

        iBGP_config += 'exit-address-family\n'
        iBGP_config += '!\n'

    return iBGP_config


def generate_eBGP_configuration(router_intents):
    '''
      Returns the external BGP configuration 
        Parameters:
            router_intents(): a dictionary which contains the actual commands for eBGP configuration for a router 
        Returns:
            generate_eBGP_configuration(str): A String which is the configuration of the external BGP for each router
    '''
    global AS_NUMBER

    eBGP_config = f'router bgp {AS_NUMBER}\n'
    for ebgp_neighbors in router_intents["eBGP_config"]:
        remote_address = ebgp_neighbors["remote_IP_address"]
        remote_as = ebgp_neighbors["remote_AS"]
        ip_v = "v6" if ebgp_neighbors["IP_version"] == 6 else "v4"
        eBGP_config += f' neighbor {remote_address} remote-as {remote_as}\n'
        eBGP_config += '!\n'
        eBGP_config += f'address-family ip{ip_v}\n'
        remote_address = ebgp_neighbors["remote_IP_address"]
        link_IP = ebgp_neighbors["link_IP"]
        eBGP_config += f' neighbor {remote_address} activate\n'
        eBGP_config += f' network {link_IP}\n'

    eBGP_config += f' network {IP_RANGE}/{IP_MASK}\n'
    eBGP_config += 'exit-address-family\n!\n'
    eBGP_config += f'ip{v6} route {IP_RANGE}/{IP_MASK} Null0\n!\n'

    return eBGP_config


def generate_eBGP_interface(router_intents):
    '''
      Returns the eBGP interface's configuration
        Parameters:
            router_intents(): a dictionary which contains the actual commands for eBGP configuration for an interface
        Returns:
            generate_eBGP_interface(str): A String which is the configuration of the interface
    '''
    global AS_NUMBER
    global IGP

    interface_config = ''
    for ebgp_interfaces in router_intents["eBGP_config"]:
        interface = ebgp_interfaces["interface"]
        ip_address = ebgp_interfaces["IP_address"]
        ip_mask = ebgp_interfaces["link_mask"]
        ip_v = ebgp_interfaces["IP_version"]
        ip_address += f'/{ip_mask}'
        interface_config += generate_interface_configuration(
            interface, ip_address, ip_v)

    return interface_config


def generate_BGP_policies(router_intents):
    '''
      Returns the configuration of the 4 BGP policies:
        -  Local preference configuration
        -  Making the Communities
        -  Filtering the private IP addresses
        -  AS prepending
                                   
        Parameters:
            router_intents(): a dictionary  
        Returns:
            generate_BGP_policies(str): A String which configures each BGP policy  
    '''
    BGP_configuration = ''
    count = 0
    for eBGP_neighbor in router_intents["eBGP_config"]: 
        local_preference = eBGP_neighbor["local_preference"]
        community_in = eBGP_neighbor["community_in"]
        neighbor_IP_address = eBGP_neighbor["remote_IP_address"]
        neighbor_IP_version = eBGP_neighbor["IP_version"]
        version = "v6" if neighbor_IP_address == 6 else "v4"
        communities_out = []
        for community in eBGP_neighbor["community_out"]:
            communities_out.append(community)
            BGP_configuration += f'ip community-list standard {community}_out permit {community}\n'

        BGP_configuration += '!\n'
        BGP_configuration += f'ipv6 access-list private_ipv6_list\n'
        BGP_configuration += f' permit ipv6 FD00::/8 any \n'
        BGP_configuration += '!\n'
        BGP_configuration += f'route-map map_in_{count} permit 10\n'
        BGP_configuration += f' set community {community_in}\n'
        BGP_configuration += f' set local-preference {local_preference}\n'
        BGP_configuration += '!\n'
        BGP_configuration += f'route-map map_in_{count} deny 1\n'
        BGP_configuration += f' match ipv6 address private_ipv6_list\n'
        BGP_configuration += '!\n'
        if len(communities_out) > 0:
            BGP_configuration += f'route-map map_out_{count} deny 10\n'
            for community in communities_out:
                BGP_configuration += f' match community {community}_out\n'

        BGP_configuration += '!\n'
        BGP_configuration += f'route-map map_out_{count} permit 100\n!\n'

        BGP_configuration += f'router bgp {AS_NUMBER}\n'
        BGP_configuration += f'address-family ip{version}\n'
        BGP_configuration += f' neighbor {neighbor_IP_address} route-map map_in_{count} in\n'
        BGP_configuration += f' neighbor {neighbor_IP_address} route-map map_out_{count} out\n' 
        BGP_configuration += 'exit-address-family\n!\n'

        #AS-Path prepending configuration 
        if "AS_path_prepend" in eBGP_neighbor:
            BGP_configuration += f"route-map map_out_{count} permit 5\n"
            BGP_configuration += f' set as-path prepend '
            x = eBGP_neighbor["AS_path_prepend"]
            for _ in range(x):
                BGP_configuration+= f'{AS_NUMBER} '
            BGP_configuration += '\n!\n'

        count +=1

    return BGP_configuration


if len(sys.argv) != 2:
    print('Provide the path of the intent file as an argument')
    sys.exit(1)

intent_path = sys.argv[1]


AS_NUMBER, AS_INTENTS, ARCHITECTURE_PATH, IGP, IP_RANGE, IP_MASK, IP_VERSION = io_h.get_intents(
    intent_path)
router_intent_list = AS_INTENTS["routers"]
print("Generating the configuration of AS", AS_NUMBER, "...")

v6 = "v6" if IP_VERSION == 6 else ""
v4 = "v4" if IP_VERSION == 4 else ""

archi = io_h.generate_ip_address(ARCHITECTURE_PATH, IP_RANGE, IP_VERSION, IP_MASK)

json_output_path, configs_parent_directory = io_h.handle_output(AS_NUMBER)

link_ip_list = []

# construction of the configuration files
for routers in archi['architecture']:
    # declaration of constants relative to the router
    router_number = routers['abstract_router_number']
    router_name = f'i{router_number}'
    config_file_name = f'{router_name}_startup-config.cfg'
    router_intents = next(
        item for item in router_intent_list if item['router_number'] == router_number)
    output_path = os.path.join(configs_parent_directory, config_file_name)

    # opening the file the script is going to write the configuration into
    with open(output_path, 'w') as config_file:


        # Writing header
        config_file.write(generate_header(router_name))

        # Writing configuration of the loopback addresses
        loopback_address = routers["loopback_IP"]
        config_file.write(generate_loopback_configuration(
            loopback_address))

        for neighbors in routers['neighbors']:
            # Writing the configuration of the non-ebgp interfaces
            interface_name = neighbors['interface']
            link_ip = neighbors['link_IP']
            ip_address = ''
            if IP_VERSION == 6:
                ip_address = f'{link_ip}::{router_number}/{IP_MASK+16}'
            elif IP_VERSION == 4:
                add = 1
                if link_ip in link_ip_list:
                    add = 2
                else:
                    link_ip_list.append(link_ip)

                ip_address = f'{link_ip}.{add} 255.255.255.252'
                
            neighbors.update({"ip_address": ip_address})
            config_file.write(generate_interface_configuration(
                interface_name, ip_address))
        config_file.write(generate_cost_configuration(router_intents))


        if "eBGP" in router_intents:
            # specific iBGP configuration for eBGP routers
            config_file.write(generate_iBGP_configuration(
                router_number, True))

            # specific interface configuration on eBGP interfaces
            config_file.write(generate_eBGP_interface(
                router_intents))

            # configuration of the eBGP neighbors
            config_file.write(generate_eBGP_configuration(
                router_intents))

            config_file.write(generate_BGP_policies(router_intents))
        else:
            # basic iBGP configuration if the router isn't ASBR
            config_file.write(generate_iBGP_configuration(
                router_number, False))

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


# save the config in a json file
with open(json_output_path, 'w') as json_file:
    json.dump(archi, json_file,
              indent=4,
              separators=(',', ': '))

print("Done! The configuration of each router is located at",
      configs_parent_directory)
