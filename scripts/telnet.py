import telnetlib

HOST = "localhost"

with telnetlib.Telnet(HOST, 5000) as tn:
    tn.write(b'end\r\n')
    tn.write(b'end\r\n')
    tn.write(b'conf t\r\n')
    tn.write(b'int g2/0\r\n')
    tn.write(b'no ip address\r\n')
    tn.write(b'no ipv6 address\r\n')
    tn.write(b'ipv6 address 2002:100:1:8::FFE/64\r\n')
    tn.write(b'ipv6 enable\r\n')
    tn.write(b'ipv6 rip ripng enable\r\n')
    tn.write(b'no shutdown\r\n')
    tn.write(b'end\r\n')