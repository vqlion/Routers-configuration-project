# GNS3 Project

Automation of the generation of router configurations. Feed the program an intent file with the parameters of the AS, as well as the description of the architecture of the network, and the script generates the configuration file for each cisco router automatically.

## Features
 - Automated generation of IP addresses for each link of the network (physical/loopback interfaces) based on IP prefix
 - Enable an IGP on the routers (RIP or OSPF) 
 - OSPF metric optimization: setting custom link costs for OSPF
 - Automated BGP configuration:
    - iBGP and eBGP sessions 
    - Filter out private IP addresses
    - Policies based on the business relationships with neighboring AS
    - Custom local preference
    - AS path prepending
## Intent files
The intent and architecture files must be json files following a particular format. They can be found in the [intent files folder](./intent_files/). 

You can also provide a drag and drop intent file, which helps putting the configuration of each router in the right folder automatically.

The full documentation about the intent files syntax can be found [here](./intent_files/README.md).

## Usage

### Script generation

You can generate the scripts, which will be located in an output directory.

```shell
cd scripts
python3 config.py {intent_file_path}
```

```intent_file_path``` being the path of the intent file. See [intent files syntax](./intent_files/README.md).

Then, you can use the dragndrop script to move the files automatically.

```shell
python3 dragndrop.py {dragndrop_file_path}
```

```dragndrop_file_path``` being the path of the drag and drop json file. See [intent files syntax](./intent_files/README.md).

### Telnet generation

alternatively, you can modify the routers' configuration on the fly, when they are running:

```shell
python3 telnet.py {intent_file_path} {router_number}
```

```intent_file_path``` being the path of the intent file, and ```router_number``` being the id of the router you want to modify. The router number is optional: if not given, all the routers in the AS relative to the intent file will be modified (this can take some time, depending on how many routers are running).

## Team
[Rebecca Djimtoingar](https://github.com/rebeccadjim), [Alexandru Baciu](https://github.com/bachusutopian) and [Valentin Jossic](https://github.com/vqlion)