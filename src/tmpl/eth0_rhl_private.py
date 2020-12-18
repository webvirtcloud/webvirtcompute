desc = "RedHat based eth0 interface file template for private cloud"
data = """DEVICE=eth0
TYPE=Ethernet
BOOTPROTO=none
ONBOOT=yes
IPADDR={ipv4_addr}
NETMASK={ipv4_mask}
GATEWAY={ipv4_gw}
NM_CONTROLLED=yes
IPV6INIT=no
DNS1={ipv4_dns1}
DNS2={ipv4_dns2}"""
