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

The full documentation about the intent files syntax can be found [here](./intent_files/intents_syntax.md).

## Usage

```shell
cd scripts
python3 config.py {intent_file_path}
```

```intent_file_path``` being the path of the intent file. See [intent files syntax](./intent_files/intents_syntax.md).

## Team
[Rebecca Djimtoingar](https://github.com/rebeccadjim), [Alexandru Baciu](https://github.com/bachusutopian) and [Valentin Jossic](https://github.com/vqlion)