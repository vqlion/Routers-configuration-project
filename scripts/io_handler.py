import json
import sys
import os

#loads a json file with the architecture of the network
#returns the total number of links between routers and the adjacency matrix of the network

def get_minimun_router_number(arc):
    min = 99999999999
    for routers in arc['architecture']:
        min = routers['router_number'] if routers['router_number'] < min else min
    return min

def load(file_path):

    f = open(file_path)
    arc = json.load(f)

    router_count = len(arc['architecture'])
    adjacency_matrix = [[0 for _ in range(router_count)] for _ in range(router_count)]
    link_count = 0

    min_router_number = get_minimun_router_number(arc)

    for routers in arc['architecture']:
        router_number = routers['router_number']
        routers.update({'abstract_router_number': router_number})
        routers.update({'router_number': router_number - min_router_number + 1})
        for neighbors in routers['neighbors']:
            neighbor_number = neighbors["neighbor_number"]
            neighbors.update({'abstract_neighbor_number': neighbor_number})
            neighbors.update({'neighbor_number': neighbor_number - min_router_number + 1})
            adjacency_matrix[routers['router_number'] - 1][neighbors["neighbor_number"] - 1] = link_count + 1
            link_count += 1

    link_count /= 2

    return int(link_count) , adjacency_matrix, arc


def generate_ip_address(json_file, ip_range, ip_mask):

    count, matrix, arc = load(json_file)

    ip_list = []

    ip_range_input = ip_range
    ip_mask_input = ip_mask

    ip_range_input = ip_range_input[:-1]

    #loops over the links and creates a new ip for each link, stores in a list
    for i in range(1, count + 1):
        r=f'{i}'
        ip_list.append(f'{ip_range_input}{r}')

    #affects an ip to each link and stores it in the dict from the architecture json file
    for routers in arc['architecture']:
        router_number = routers['router_number']
        abstract_route_number = routers['abstract_router_number']
        routers.update({"loopback_IP": f"{abstract_route_number}::{abstract_route_number}"}) #generate loopback IP of the router
        for neighbors in routers['neighbors']:
            neighbor_number = neighbors['neighbor_number']

            if not "link_IP" in neighbors: #if the link's ip is not set yet
                if matrix[routers['router_number'] - 1][neighbors['neighbor_number'] - 1]: #check if it has been set before on another router
                    neighbors.update({"link_IP": ip_list.pop()}) #set it from the list if it hasn't
                    matrix[routers['router_number'] - 1][neighbors['neighbor_number'] - 1] = 0
                    matrix[neighbors['neighbor_number'] - 1][routers['router_number'] - 1] = 0 #update the matrix to indicate this link has an ip
                else: #if it has been set on another router
                    symetric_router = next(item for item in arc['architecture'] if item['router_number'] == neighbor_number) #get the corresponding router
                    symetric_link = next(item for item in symetric_router['neighbors'] if item['neighbor_number'] == router_number) #get the actual link
                    ip = symetric_link['link_IP'] #get the IP of the link
                    neighbors.update({"link_IP": ip}) #set the IP on this router

    return arc #returns the modified dict with the subnetworks' ip range information

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


def handle_output(AS_NUMBER):
    json_output_name = f'complete_architecture_as_{AS_NUMBER}.json'
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
    return json_output_path, configs_parent_directory
    # creates the required directories to store the output if they are yet to be created
    