import ip_generation as gen
import json
import os
import sys

# opens the intent file at the path specified and returns the intents of the given AS, along with information about it


def get_intents(file):
    try:
        f = open(file)
    except Exception:
        print("There was an error opening the intent file. Terminating...")
        sys.exit(1)
    intents = json.load(f)
    as_number = intents['AS_number']
    architecture_path = intents['architecture_path']
    igp = intents['IGP']
    ip_range = intents['IP_prefix']
    # gets the ip range and mask to create the network ips of the links' subnetworks
    ip_mask = intents['IP_mask']

    return as_number, intents, architecture_path, igp, ip_range, ip_mask


def generate_footer():
    footer = 'control plane\n'
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


def generate_interface_configuration(interface_name, ip_address, as_number, igp, asbr=False):
    interface_config = f'interface {interface_name}\n'
    interface_config += ' no ip address\n'
    # verbose constants depending on the interface type
    interface_config += ' duplex full\n' if interface_name == 'fe0/0' else ' negotiation auto\n'
    interface_config += f' ipv6 address {ip_address}\n'
    interface_config += ' ipv6 enable\n'
    if not asbr:
        interface_config += ' ipv6 rip ripng enable\n' if not asbr and igp == 'RIP' else ''
        interface_config += f' ipv6 ospf {as_number} area 0\n' if igp == 'OSPF' else ''
    interface_config += '!\n'

    return interface_config


def generate_loopback_configuration(loopback_address, ip_mask, igp, as_number):
    loopback_config = 'interface Loopback0\n no ip address\n'
    loopback_config += f' ipv6 address {loopback_address}/{ip_mask+16}\n'
    loopback_config += ' ipv6 enable\n'
    # extra config if RIP router
    loopback_config += ' ipv6 rip ripng enable\n' if igp == 'RIP' else ''
    # extra config if OSPF router
    loopback_config += f' ipv6 ospf {as_number} area 0\n' if igp == 'OSPF' else ''
    loopback_config += '!\n'

    return loopback_config


def generate_iBGP_configuration(as_number, router_number, eBGP):
    iBGP_config = f'router bgp {as_number}\n'
    iBGP_config += f' bgp router-id {router_number}.{router_number}.{router_number}.{router_number}\n'
    iBGP_config += ' bgp log-neighbor-changes\n'
    iBGP_config += ' no bgp default ipv4-unicast\n'
    for routers in archi['architecture']:
        neighbor_number = routers['abstract_router_number']
        neighbor_loopback = routers['loopback_IP']
        if router_number != neighbor_number:
            iBGP_config += f' neighbor {neighbor_loopback} remote-as {as_number}\n'
            iBGP_config += f' neighbor {neighbor_loopback} update-source Loopback0\n'

    iBGP_config += '!\n'
    iBGP_config += 'address-family ipv4\n'
    iBGP_config += '!\n'
    iBGP_config += 'address-family ipv6\n'

    for routers in archi['architecture']:
        neighbor_number = routers['abstract_router_number']
        neighbor_loopback = routers['loopback_IP']
        if router_number != neighbor_number:
            iBGP_config += f' neighbor {neighbor_loopback} activate\n'
            iBGP_config += f' neighbor {neighbor_loopback} send-community\n'

    announced_networks = []
    for routers in archi['architecture']:
        if eBGP == False:
            for neighbors in routers["neighbors"]:
                neighbor_network = neighbors['link_IP']
                if not neighbor_network in announced_networks:
                    iBGP_config += f' network {neighbor_network}::/{ip_mask + 16}\n'
                    announced_networks.append(neighbor_network)

    iBGP_config += 'exit-address-family\n'
    iBGP_config += '!\n'
    iBGP_config += 'ip forward-protocol nd\n'
    iBGP_config += '!\n'
    iBGP_config += '!\n'
    iBGP_config += 'no ip http server\n'
    iBGP_config += 'no ip http secure-server\n'
    iBGP_config += '!\n'

    if eBGP == True:
        iBGP_config += f'ipv6 route {ip_range}/{ip_mask} Null0\n'
    if igp == 'RIP':
        iBGP_config += 'ipv6 router rip ripng\n'
        iBGP_config += ' redistribute connected\n'

    iBGP_config += '!\n'
    iBGP_config += '!\n'
    iBGP_config += '!\n'

    return iBGP_config


def generate_eBGP_configuration(router_intents, as_number):
    eBGP_config = f'router bgp {as_number}\n'
    for ebgp_neighbors in router_intents["eBGP_config"]:
        remote_address = ebgp_neighbors["remote_IP_address"]
        remote_as = ebgp_neighbors["remote_AS"]
        eBGP_config += f' neighbor {remote_address} remote-as {remote_as}\n'
    eBGP_config += '!\n'
    eBGP_config += 'address-family ipv6\n'

    for ebgp_neighbors in router_intents["eBGP_config"]:
        remote_address = ebgp_neighbors["remote_IP_address"]
        link_IP = ebgp_neighbors["link_IP"]
        eBGP_config += f' neighbor {remote_address} activate\n'
        eBGP_config += f' network {link_IP}\n'

    eBGP_config += f' network {ip_range}/{ip_mask}\n'
    eBGP_config += 'exit-address-family\n!\n'

    return eBGP_config


def generate_EGP_interface(router_intents, as_number, igp):
    asbr = True
    interface_config = ''
    for ebgp_interfaces in router_intents["eBGP_config"]:
        interface = ebgp_interfaces["interface"]
        ip_address = ebgp_interfaces["IP_address"]
        ip_mask = ebgp_interfaces["link_mask"]
        ip_address += f'/{ip_mask}'
        interface_config += generate_interface_configuration(
            interface, ip_address, as_number, igp, asbr)

    return interface_config


if len(sys.argv) != 2:
    print('Provide the path of the intent file as an argument')
    sys.exit(1)

intent_path = sys.argv[1]

as_number, as_intents, architecture_path, igp, ip_range, ip_mask = get_intents(
    intent_path)
router_intent_list = as_intents["routers"]
print("Generating the configuration of AS", as_number, "...")

archi = gen.generate_ip_address(architecture_path, ip_range, ip_mask)

json_output_name = f'complete_architecture_as_{as_number}.json'
parent_directory = '../output_files/'
configs_parent_directory = '../output_files/configs/'
json_output_path = os.path.join(parent_directory, json_output_name)

try:
    os.mkdir(parent_directory)
except FileExistsError:
    pass

try:
    os.mkdir(configs_parent_directory)
except FileExistsError:
    pass
# creates the required directories to store the output if they are yet to be created

CONSTANT_VERBOSE_1 = 'version 15.2\nservice timestamps debug datetime msec\nservice timestamps log datetime msec\n!\nhostname '
CONSTANT_VERBOSE_2 = '\n!\nboot-start-marker\nboot-end-marker\nno aaa new-model\nno ip icmp rate-limit unreachable\nip cef\nno ip domain lookup\nipv6 unicast-routing\nipv6 cef\nmultilink bundle-name authenticated\nip tcp synwait-time 5\n!\n!\n!\n!\n!\n'
# constants at the beginning of each file

# actual construction of the config files
for routers in archi['architecture']:
    router_number = routers['abstract_router_number']
    router_name = f'i{routers["abstract_router_number"]}'
    config_file_name = f'{router_name}_startup-config.cfg'
    output_path = os.path.join(configs_parent_directory, config_file_name)
    router_intents = next(
        item for item in router_intent_list if item['router_number'] == router_number)
    with open(output_path, 'w') as config_file:
        # add the constants and the router's id to the config file
        config_file.write(CONSTANT_VERBOSE_1 +
                          router_name + CONSTANT_VERBOSE_2)
        loopback_address = routers["loopback_IP"]
        config_file.write(generate_loopback_configuration(
            loopback_address, ip_mask, igp, as_number))
        for neighbors in routers['neighbors']:
            interface_name = neighbors['interface']
            link_ip = neighbors['link_IP']
            ip_address = f'{link_ip}::{router_number}/{ip_mask+16}'
            neighbors.update({"ip_address": ip_address})
            # generates the configuration needed line by line and writes it to the file
            config_file.write(generate_interface_configuration(
                interface_name, ip_address, as_number, igp))

        if "eBGP" in router_intents:
            config_file.write(generate_iBGP_configuration(
                as_number, router_number, True))
            config_file.write(generate_EGP_interface(
                router_intents, as_number, igp))
            config_file.write(generate_eBGP_configuration(
                router_intents, as_number))
            pass
        else:
            config_file.write(generate_iBGP_configuration(
                as_number, router_number, False))

        if igp == "OSPF":  # extra config if OSPF router
            ospf_config = f'ipv6 router ospf {as_number}\n'
            ospf_config += f' router-id {router_number}.{router_number}.{router_number}.{router_number}\n default-information originate always\n!\n'
            config_file.write(ospf_config)
        config_file.write(generate_footer())

with open(json_output_path, 'w') as json_file:
    json.dump(archi, json_file,
              indent=4,
              separators=(',', ': '))  # save the config in a json file

print("Done! The configuration of each router is located at",
      configs_parent_directory)
