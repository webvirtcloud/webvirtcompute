desc = "Debian based eth0 interfaces file template for public cloud"
data = """# This file describes the network interfaces available on your
# system and how to activate them. For more information, see
# interfaces(5).

# The loopback network interface
auto lo
iface lo inet loopback
    dns-nameservers {ipv4_dns1} {ipv4_dns2}
    #dns-nameservers {ipv6_dns1} {ipv6_dns2}
    
# The primary network interface
auto eth0
iface eth0 inet static
    address {ipv4_addr}
    netmask {ipv4_mask}
    gateway {ipv4_gw}

iface eth0 inet6 static
    address {ipv6_addr}
    netmask {ipv6_mask}
    gateway {ipv6_gw}

iface eth0 inet static
    address {ipv4anch_addr}
    netmask {ipv4anch_mask}
"""
