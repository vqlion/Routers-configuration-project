import ip_generation as gen
import json
import os
import sys

def get_intents(file, as_number):
    f = open(file)
    intents = json.load(f)
    as_intents = next(item for item in intents['intent'] if item['AS_number'] == as_number)
    architecture_path = as_intents['architecture_path']
    igp = as_intents['IGP']
    ip_range = as_intents['IP_prefix']
    ip_mask = as_intents['IP_mask']

    return as_intents, architecture_path, igp, ip_range, ip_mask

if len(sys.argv) != 2:
    print('Provide the AS number as an argument')
print("Generating the configuration of AS", sys.argv[1], "...")
as_number = int(sys.argv[1])
as_intents, architecture_path, igp, ip_range, ip_mask = get_intents('../intent_files/intent.json', as_number)

file_path = gen.generate_ip_address(architecture_path, ip_range, ip_mask, as_number)

f = open(file_path)
archi = json.load(f)
constants1 = 'version 15.2\nservice timestamps debug datetime msec\nservice timestamps log datetime msec\n!\nhostname '
constans2 = '\n!\nboot-start-marker\nboot-end-marker\nno aaa new-model\nno ip icmp rate-limit unreachable\nip cef\nno ip domain lookup\nipv6 unicast-routing\nipv6 cef\nmultilink bundle-name authenticated\nip tcp synwait-time 5\n!\n!\n!\n!\n!\n'


for routers in archi['architecture']:
    router_number = routers['abstract_router_number']
    router_name = f'R{routers["abstract_router_number"]}'
    output_path = f'../output_files/configs/{router_name}_startup-config.cfg'
    with open(output_path, 'a') as config_file:
        config_file.write(constants1 + router_name + constans2)
        loopback_address = routers["loopback_IP"]
        loopback_config = 'interface Loopback0\n no ip address\n'
        loopback_config += f' ipv6 address {loopback_address}/{ip_mask+16}\n'
        loopback_config += ' ipv6 enable\n'
        loopback_config += ' ipv6 rip ripng enable\n' if igp == 'RIP' else ''
        loopback_config += f' ipv6 ospf {as_number} area 0\n' if igp == 'OSPF' else ''
        loopback_config += '!\n'
        config_file.write(loopback_config)
        for neighbors in routers['neighbors']:
            interface_name = neighbors['interface']
            link_ip = neighbors['link_IP']
            interface_config = f'interface {interface_name}\n'
            interface_config += ' no ip address\n'
            interface_config += ' duplex full\n' if interface_name == 'fe0/0' else ' negotiation auto\n'
            ip_address = f'{link_ip}::{router_number}/{ip_mask+16}'
            neighbors.update({"ip_address": ip_address})
            interface_config += f' ipv6 address {ip_address}\n'
            interface_config += ' ipv6 enable\n'
            interface_config += ' ipv6 rip ripng enable\n' if igp == 'RIP' else ''
            interface_config += f' ipv6 ospf {as_number} area 0\n' if igp == 'OSPF' else ''
            interface_config += '!\n'
            config_file.write(interface_config)
        if igp == "OSPF":
            ospf_config = f'ipv6 router ospf {as_number}\n'
            ospf_config += f' router_id {router_number}.{router_number}.{router_number}.{router_number}\n default-information originate always\n!\n'
            config_file.write(ospf_config)

os.remove(file_path)
with open(file_path, 'x') as json_file:
        json.dump(archi, json_file, 
                            indent=4,  
                            separators=(',',': ')) #save in a new json file

print("Done! Configuration of each router is at", file_path, "in the configs folder.")


