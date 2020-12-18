desc = "Debian based eth1 interfaces file template"
data = """
# The secondary network interface
auto eth1
iface eth1 inet static
    address {ipv4_addr}
    netmask {ipv4_mask}
"""
