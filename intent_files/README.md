# Intent files syntax

In order for the script to properly work, we need to provide it basic informations regarding the behavior and the architecture of the network.

## Intents file

The intents regarding the configuration of the network must be described in a json file.

Below is an example of what that file must look like:

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
 - ```architecture_path``` is the path of the architecture json file, which describes the physical links between the routers in the network. See [architecture](#architecture-file) for this file's syntax
 - ```IGP``` is the IGP desired for the network (RIP or OSPF)
 - ```IP_prefix``` is the IP prefix desired to address the physical interfaces of the routers. In IPv4, the prefix has to specified following the following example's format : ```"IP_prefix": "10.1."```.
 - ```IP_mask``` is the mask associated to the latter. It is deprecated for IPv4 addresses and will not be considered.
 - ```routers``` is a list of all the routers in the network, with information about their eBGP sessions and OSPF metric optimization

Here is an example of what a router in the ```routers``` list must look like. Note that this list must be complete, even if a router does not have a custom cost parameter or an eBGP session.

```json
{
    "router_number": 1,
    "telnet_port": 5000,
    "cost_parameters": [
        {
            "cost":100,
            "interface": "g1/0"
        }
    ],
    "eBGP": true,
    "eBGP_config": [
        {
            "interface": "g1/0",
            "remote_AS": 2,
            "link_IP": "2000:100:1:2::/64",
            "link_mask": 64,
            "IP_version": 6,
            "IP_address": "2000:100:1:2::1",
            "remote_IP_address": "2000:100:1:2::5",
            "local_preference": 400,
            "community_in": "2:10",
            "community_out": [],
            "vpn": true,
            "client_id": 1,
            "vpn_list": [2]
        },
        {
            "interface": "g2/0",
            "remote_AS": 3,
            "link_IP": "10.160.0.0",
            "link_mask": "255.255.0.0",
            "IP_version": 4,
            "IP_address": "10.160.0.1",
            "remote_IP_address": "10.160.0.6",
            "local_preference": 400,
            "community_in": "3:10",
            "community_out": [],
            "vpn": true,
            "client_id": 2
        }
    ]
}
```

 - ```router_number``` is the id of the router. It is arbitrary, but all routers must have different positive ids, and the id of a router must be consistent between the intent file and the architecture file
 - ```telnet_port``` is the port on which the telnet connection must occur. It is optional, but the telnet configuration won't work if it's not given. By default, telnet configurations will be done on ```localhost```.
 - ```cost_parameters``` is a list of the costs intents for OSPF optimization. It is optional
    - ```cost``` is the desired OSPF cost
    - ```interface``` is the name of the interface that will see its cost modified
 - ```eBGP``` is a boolean flag to specify whether the router will have an eBGP session on one of its interface. It is optional, and is considered as false if not given
 - ```eBGP_config``` is a list of the intents regarding the eBGP sessions. It is optional but must be set if ```eBGP``` is set to true.
    - ```interface``` is the interface on which the session will be held
    - ```remote_AS``` is the AS number of the neighbor
    - ```link_IP``` is the IP range of the link used for the session. In IPv6, you also have to specify the link here, as shown in the example. In IPv4, you must not specify the mask here.
    - ```link_mask``` is the mask associated to the latter. It has to be specified following the example's formats for IPv4 & IPv6.
    - ```IP_address``` is the desired IP address on the ```interface```
    - ```remote_IP_address``` is the IP address of the neighboring router
    - ```local_preference``` is the local preference the router should apply to the routes advertised by the neighbor
    - ```community_in``` is the BGP community the router should apply to the routes advertised by the neighbor
    - ```community_out``` is a list of all the communities the router should ignore when advertising routes to its neighbor. If a route has previously been tagged with a community in this list by any router in the AS, it won't be advertised.
    - ```AS_path_prepend``` is the desired amount of prepending on the routes advertised by the neighbor. It is optional
    - ```vpn``` is a boolean flag to specifiy whether the neighbouring router is a vpn customer
    - ```client_id``` is the id of the VPN customer. VPN customer ids are global to the AS and must be linked to one and only one customer. VPN routes of customers with the same ids will be shared.
    - ```vpn_list``` is a list of all the VPN customers ids whom routes should be shared with the VPN customer (site sharing among multiple VPN customers) 

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

## Drag and drop file

The drag and drop file is a json file used to move the configuration files automatically in the right directories. It must describe, for each router, the path of the new configuration file and the path it should be copied in.

Here is an example of what this file must look like:

```json
{
    "architecture": [
        {
            "router_number": 1,
            "removed_file": "../../../../GNS3/projects/projet_GNS3/project-files/dynamips/b51ccf5e-4fd6-4412-931b-73faa1445566/configs/i1_startup-config.cfg",               
            "source_file": "../output/configs/i1_startup-config.cfg"
        },
        {
            "router_number": 2,
            "removed_file": "../../../../GNS3/projects/projet_GNS3/project-files/dynamips/e58c5662-6d45-4798-aeb3-011db479c2f0/configs/i2_startup-config.cfg",              
            "source_file": "../output/configs/i2_startup-config.cfg"
        }
    ]
}
```

 - ```router_number``` is the id of the router. It must be consistent with the other intent files.
 - ```removed_file``` is the path of the router's configuration file in the GNS3 files.
 - ```source_file``` is the path of the newly generated router's configuration