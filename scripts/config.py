import ip_generation as gen
import json
import os
import sys

#opens the intent file at the path specified and returns the intents of the given AS, along with information about it
def get_intents(file, as_number):
    f = open(file)
    intents = json.load(f)
    as_intents = next(item for item in intents['intent'] if item['AS_number'] == as_number) #get the right AS intents in the file intent
    #the above line might be irrelevant for future use if we separate as intents in different files
    architecture_path = as_intents['architecture_path']
    igp = as_intents['IGP']
    ip_range = as_intents['IP_prefix']
    ip_mask = as_intents['IP_mask'] #gets the ip range and mask to create the network ips of the links' subnetworks

    return as_intents, architecture_path, igp, ip_range, ip_mask

if len(sys.argv) != 2:
    print('Provide the AS number as an argument')
print("Generating the configuration of AS", sys.argv[1], "...")
as_number = int(sys.argv[1])
as_intents, architecture_path, igp, ip_range, ip_mask = get_intents('../intent_files/intent.json', as_number)

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
#creates the required directories to store the output if they are yet to be created

CONSTANT_VERBOSE_1 = 'version 15.2\nservice timestamps debug datetime msec\nservice timestamps log datetime msec\n!\nhostname '
CONSTANT_VERBOSE_2 = '\n!\nboot-start-marker\nboot-end-marker\nno aaa new-model\nno ip icmp rate-limit unreachable\nip cef\nno ip domain lookup\nipv6 unicast-routing\nipv6 cef\nmultilink bundle-name authenticated\nip tcp synwait-time 5\n!\n!\n!\n!\n!\n'
#constants at the beginning of each file

#actual construction of the config files
for routers in archi['architecture']:
    router_number = routers['abstract_router_number']
    router_name = f'R{routers["abstract_router_number"]}'
    config_file_name = f'{router_name}_startup-config.cfg'
    output_path = os.path.join(configs_parent_directory, config_file_name)
    with open(output_path, 'w') as config_file:
        config_file.write(CONSTANT_VERBOSE_1 + router_name + CONSTANT_VERBOSE_2) #add the constants and the router's id to the config file
        loopback_address = routers["loopback_IP"]
        loopback_config = 'interface Loopback0\n no ip address\n'
        loopback_config += f' ipv6 address {loopback_address}/{ip_mask+16}\n'
        loopback_config += ' ipv6 enable\n'
        loopback_config += ' ipv6 rip ripng enable\n' if igp == 'RIP' else '' #extra config if RIP router
        loopback_config += f' ipv6 ospf {as_number} area 0\n' if igp == 'OSPF' else '' #extra config if OSPF router
        loopback_config += '!\n'
        config_file.write(loopback_config)
        for neighbors in routers['neighbors']:
            interface_name = neighbors['interface']
            link_ip = neighbors['link_IP']
            ip_address = f'{link_ip}::{router_number}/{ip_mask+16}'
            neighbors.update({"ip_address": ip_address})
            interface_config = f'interface {interface_name}\n'
            interface_config += ' no ip address\n'
            interface_config += ' duplex full\n' if interface_name == 'fe0/0' else ' negotiation auto\n' #verbose constants depending on the interface type
            interface_config += f' ipv6 address {ip_address}\n'
            interface_config += ' ipv6 enable\n'
            interface_config += ' ipv6 rip ripng enable\n' if igp == 'RIP' else ''
            interface_config += f' ipv6 ospf {as_number} area 0\n' if igp == 'OSPF' else ''
            interface_config += '!\n'
            config_file.write(interface_config) #generates the configuration needed line by line and writes it to the file
        if igp == "OSPF": #extra config if OSPF router
            ospf_config = f'ipv6 router ospf {as_number}\n'
            ospf_config += f' router_id {router_number}.{router_number}.{router_number}.{router_number}\n default-information originate always\n!\n'
            config_file.write(ospf_config)

with open(json_output_path, 'w') as json_file:
        json.dump(archi, json_file, 
                            indent=4,  
                            separators=(',',': ')) #save the config in a json file

print("Done! The configuration of each router is located at", configs_parent_directory)


