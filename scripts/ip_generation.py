import re
import load_json

count, matrix = load_json.load('../intent_files/network_arc.json')

list = []

ip_range_input = '2002:100:1::'
ip_mask_input = 48

ip_range_regex = '([0-9]+:?)+'

print("mask", int(ip_mask_input))

if(re.match(ip_range_regex, ip_range_input)):
    print(ip_range_input)

ip_range_input = ip_range_input[:-1]

#loops over the links and creates a new ip for each link, stores in a list
#todo: actual creation of the link, affectation to each address to each link, and better support for more mask lengths
for i in range(1, count):
    r=f'{i}'
    list.append(f'{ip_range_input}{r}')

print(list)