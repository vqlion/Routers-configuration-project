import json

#loads a json file with the architecture of the network, creates the adjacency matrix
#also counts the number of links
#todo: wrap it up in a function

f = open('../intent_files/network_arc.json')

arc = json.load(f)

for i in arc['architecture']:
    print(f'For router {i["router_number"]}')
    for j in i['neighbors']:
        print(f'{j}')

router_count = len(arc['architecture'])
adjacency_matrix = [[0 for _ in range(router_count)] for _ in range(router_count)]
link_count = 0

for router in arc['architecture']:
    for neighbors in router['neighbors']:
        adjacency_matrix[router['router_number'] - 1][neighbors["neighbor_number"] - 1] = 1
        link_count += 1

link_count /= 2

print("Adj", adjacency_matrix)
print("count", link_count)

