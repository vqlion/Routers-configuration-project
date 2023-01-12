import re
import load_json
import json

count, matrix, arc = load_json.load('../intent_files/network_arc.json')

ip_list = []

ip_range_input = '2002:100:1::'
ip_mask_input = 48

ip_range_regex = '([0-9]+:?)+'

print("mask", int(ip_mask_input))

if(re.match(ip_range_regex, ip_range_input)):
    print(ip_range_input)

ip_range_input = ip_range_input[:-1]

#loops over the links and creates a new ip for each link, stores in a list
for i in range(1, count + 1):
    r=f'{i}'
    ip_list.append(f'{ip_range_input}{r}')

#affects an ip to each link and stores it in a new json file based on architecture one
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

for i in arc['architecture']:
    print(f'For router {i["router_number"]}')
    for j in i['neighbors']:
        print(f'{j}')

with open('test_out.json', 'x') as json_file:
    json.dump(arc, json_file, 
                        indent=4,  
                        separators=(',',': ')) #save in a new json file

print(ip_list)