import re
import load_json
import json
import os

def generate_ip_address(json_file, ip_range, ip_mask):

    count, matrix, arc = load_json.load(json_file)

    ip_list = []

    ip_range_input = ip_range
    ip_mask_input = ip_mask

    ip_range_regex = '([0-9]+:?)+'

    # print("mask", int(ip_mask_input))

    # if(re.match(ip_range_regex, ip_range_input)):
    #     print(ip_range_input)

    ip_range_input = ip_range_input[:-1]

    #loops over the links and creates a new ip for each link, stores in a list
    for i in range(1, count + 1):
        r=f'{i}'
        ip_list.append(f'{ip_range_input}{r}')

    #affects an ip to each link and stores it in the dict from the architecture json file
    for routers in arc['architecture']:
        router_number = routers['router_number']
        routers.update({"loopback_IP": f"{router_number}::{router_number}"}) #generate loopback IP of the router
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