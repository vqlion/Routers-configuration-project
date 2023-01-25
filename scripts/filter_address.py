import ipaddress

def filter_private_addr(ipv6_list):
    private_range = ipaddress.IPv6Network("fc00::/7")
    non_private_ips = []
    for ip in ipv6_list:
        try:
            addr = ipaddress.IPv6Address(ip)
            if addr not in private_range:
                non_private_ips.append(ip)
        except ValueError:
            pass
    return non_private_ips
def client_request(client_ip):
    filtered_ips = filter_private_addr([client_ip])
    if not filtered_ips:
        print("This address IP is private: ",client_ip)
    else:
        print("This address IP is public: ",client_ip)