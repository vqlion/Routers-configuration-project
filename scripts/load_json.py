import json

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
            neightbor_number = neighbors["neighbor_number"]
            neighbors.update({'abstract_neighbor_number': neightbor_number})
            neighbors.update({'neighbor_number': neightbor_number - min_router_number + 1})
            adjacency_matrix[routers['router_number'] - 1][neighbors["neighbor_number"] - 1] = link_count + 1
            link_count += 1

    link_count /= 2

    return int(link_count) , adjacency_matrix, arc

