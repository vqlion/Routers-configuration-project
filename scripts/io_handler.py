import json
import sys
import os

def get_minimun_router_number(arc):
    '''
    Returns the minimum router ID in the network  
        Parameters: 
                arc(dict): a dictionary which represents the architecture of the network
        Returns:
               get_minimun_router_number(int): An integer  meaning the minimum router ID

    '''

    min = 99999999999
    for routers in arc['architecture']:
        min = routers['router_number'] if routers['router_number'] < min else min
    return min

def load(file_path):
    '''
    Returns a tuple of three values
        Parameters: 
                file_path(str): a string which contains the path of a JSON file
        Method:
                "link_count": the number of links in the network, calculated by counting the number of connections and dividing by 2
                "adjacency_matrix": a two-dimensional matrix representation of the connections between routers in the network
                "arc": a modified version of the original dictionary loaded from the JSON file, 
                       where each router and its neighbors have been assigned new "router_number" and "neighbor_number" values,
                       based on the minimum router number in the network
                       The original "router_number" and "neighbor_number" values are stored as "abstract_router_number" and "abstract_neighbor_number".
                    
        Returns:
               load(tuple): A tuple  meaning the link count, adjacency matrix, and modified dictionary representation of the file

    '''    
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


def generate_ip_address(json_file, ip_range, ip_version, ip_mask):
    '''
    Returns a modified version of the architecture dictionary
        Parameters: 
                json_file(str): a string which contains the path of a JSON file
                ip_range(str): a string representing the range of IP addresses used to generate IP addresses for the network interfaces
                ip_mask(str): a string representing the IP mask used to generate IP addresses for the network interfaces
        Returns:
               generate_ip_address(dict): A dictionary updated with with the subnetworks' IP range information 
    ''' 
    link_count, matrix, arc = load(json_file)

    ip_list = []
    ip_range_input = ip_range
    ip_range_input = ip_range_input[:-1]

    #loops over the links and creates a new ip for each link, stores in a list
    subnet = 1
    current_subnet = 1
    for i in range(1, link_count + 1):
        r = ''
        if ip_version == 6:
            r += f'{i:X}'
        elif ip_version == 4:
            if (current_subnet == 255):
                subnet += 1
                current_subnet = 1
            iteration = (int) ((32 - ip_mask) / 8) - 1
            for _ in range(0,iteration-1):
                r += f'.{subnet}'
            r += f'.{current_subnet}'
        ip_list.append(f'{ip_range_input}{r}')
        current_subnet += 1

    #affects an ip to each link and stores it in the dict from the architecture json file
    for routers in arc['architecture']:
        router_number = routers['router_number']
        abstract_router_number = routers['abstract_router_number']

        loopback_address = ""
        if ip_version == 6:
            loopback_address = f"{abstract_router_number}::{abstract_router_number}"
        elif ip_version == 4:
            loopback_address = f"192.168.{abstract_router_number}.{abstract_router_number}"
        routers.update({"loopback_IP": f"{loopback_address}"}) #generate loopback IP of the router

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

    return arc 

def get_intents(file):
    '''
    Returns a tuple of six values
        Parameters: 
                file(str): represents the path to a file which contains information in a JSON format
        Method: 
                as_number(int): an integer that represents the AS number of the network
                intents(dict): a dictionary that represents the intent file
                               architecture_path: a string that contains the path of the JSON file containing the architecture of the network
                igp(str): a string that represents the IGP used
                ip_range(str): a string that represents the IP prefix used to generate the IP addresses of the routers
                ip_mask(str): a string that represents the IP mask used to generate the IP addresses of the routers
        Returns:
               get_intents(tuple): A tuple of six values 
    ''' 
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
    ip_version = intents['IP_version']
    # gets the ip range and mask to create the network ips of the links' subnetworks
    ip_mask = intents['IP_mask']

    return as_number, intents, architecture_path, igp, ip_range, ip_mask, ip_version


def handle_output(AS_NUMBER):
    '''
    Returns a tuple of two values
        Parameters: 
                AS_NUMBER(int): an integer representing the number of an autonomous system
        Returns:
               handle_output(tuple): A tuple of strings which are the output path to directory and its subdirectory for the respective configurations
    ''' 
    json_output_name = f'complete_architecture_as_{AS_NUMBER}.json'
    parent_directory = '../output/'
    configs_parent_directory = '../output/configs/'
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
    return json_output_path, configs_parent_directory 
    