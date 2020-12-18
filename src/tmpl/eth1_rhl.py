desc = "RedHat based eth1 interface file template"
data = """DEVICE=eth1
TYPE=Ethernet
BOOTPROTO=none
ONBOOT=yes
IPADDR={ipv4_addr}
NETMASK={ipv4_mask}
DEFROUTE=no
NM_CONTROLLED=yes"""
