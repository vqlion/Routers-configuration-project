# Intent files syntax

In order for the script to properly work, we need to provide it basic informations regarding the behavior and the architecture of the network.

## Intents file

The intents regarding the configuration of the network must be described in a json file.

Here is an example of what that file must look like:

```json
{
    "AS_number": 2004,
    "architecture_path": "../intent_files/network_arc_2004.json",
    "IGP": "OSPF",
    "IP_prefix": "2004:100:1::",
    "IP_mask": 48,
    "routers": []
}
```

 - ```AS_number``` is the AS number of the network
 - ```architecture_path``` is the path of the architecture json file, which describes the physical links between the routers in the network. See [architecture](#architecture) for this file's syntax
 - ```IGP``` is the IGP desired for the network (RIP or OSPF)
 - ```IP_prefix``` is the IP prefix desired to address the physical interfaces of the routers
 - ```IP_mask``` is the mask associated to the latter
 - ```routers``` is a list of all the routers in the network, with information about their eBGP sessions and OSPF metric optimization

Here is an example of what a router in the ```routers``` list must look like. Note that this list must be complete, even if a router does not have a custom cost parameter or an eBGP session.

```json
{
    "router_number": 9,
    "cost_parameters": [
        {
            "cost":100,
            "interface": "g1/0"
        }
    ], 
    "eBGP": true,
    "eBGP_config": [
        {
            "interface": "g2/0",
            "remote_AS": 2002,
            "link_IP":"2000:100:1:2::/64",
            "link_mask":64,
            "IP_address": "2000:100:1:2::9",
            "remote_IP_address": "2000:100:1:2::7",
            "local_preference": 200,
            "community_in": "2003:20",
            "community_out": ["2003:30", "2003:20"],
            "AS_path_prepend": 4
        }
    ]
}
```

 - ```router_number``` is the id of the router. It is arbitrary, but all routers must have different positive ids, and the id of a router must be consistent between the intent file and the architecture file
 - ```cost_parameters``` is a list of the costs intents for OSPF optimization. It is optional
    - ```cost``` is the desired cost
    - ```interface``` is the name of the interface that will see its cost modified
 - ```eBGP``` is a boolean flag to specify whether the router will have an eBGP session on one of its interface. It is optional, and is considered as false if not given
 - ```eBGP_config``` is a list of the intents regarding the eBGP sessions. It is optional
    - ```interface``` is the interface on which the session will be held
    - ```remote_AS``` is the AS number of the neighbor
    - ```link_IP``` is the IP range of the link used for the session
    - ```link_mask``` is the mask associated to the latter
    - ```IP_address``` is the desired IP address on the ```interface```
    - ```remote_IP_address``` is the IP address of the neighboring router
    - ```local_preference``` is the local preference the router should apply to the routes advertised by the neighbor
    - ```community_in``` is the community the router should apply to the routes advertised by the neighbor
    - ```community_out``` is a list of all the communities the router should ignore when advertising routes to its neighbor. If a route has previously been tagged with a community in this list by any router in the AS, it won't be advertised
    - ```AS_path_prepend``` is the desired amount of prepending on the routes advertised by the neighbor. It is optional

## Architecture file

The architecture of the network must be described in a json file.
The architecture file must describe every connection in the network.

Here is an example of what that file must look like:

```json
{
    "architecture": [
        {
            "router_number": 18,
            "neighbors": [
                {
                    "interface": "f0/0",
                    "neighbor_number": 20
                },
                {
                    "interface": "gi2/0",
                    "neighbor_number": 19
                }
            ]
        },
        {
            "router_number": 19,
            "neighbors": [
                {
                    "interface": "f0/0",
                    "neighbor_number": 18
                }
            ]
        }
    ]
}
```

The json file contains a simple list: ```architecture```, containing the architecture of the network. Each element of the list represents router.

 - ```router_number``` is the id of the router. Again, arbitrary number, following the same rules as the ones in the intent file
 - ```neighbors``` is a list of all the interfaces of the routers that are connected to a neighbor in the same AS. eBGP neighbors aren't described in this list thought, as they are already described in the intent file
    - ```interface``` is the name of the interface on which the neighbor is connected
    - ```neighbor_number``` is the id of the neighbor
