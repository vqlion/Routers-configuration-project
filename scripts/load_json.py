import json

#loads a json file with the architecture of the network
#returns the total number of links between routers and the adjacency matrix of the network

def load(file_path):

    f = open(file_path)
    arc = json.load(f)

    router_count = len(arc['architecture'])
    adjacency_matrix = [[0 for _ in range(router_count)] for _ in range(router_count)]
    link_count = 0

    for routers in arc['architecture']:
        for neighbors in routers['neighbors']:
            adjacency_matrix[routers['router_number'] - 1][neighbors["neighbor_number"] - 1] = link_count + 1
            link_count += 1

    link_count /= 2

    return int(link_count) , adjacency_matrix, arc

