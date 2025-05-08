desc = "RedHat based NetworkManager eth1 interface file template"
data = """[connection]
id=eth1
type=ethernet
interface-name=eth1

[ethernet]

[ipv4]
address1={{ ipv4private.address }}/{{ ipv4private.prefix }}
method=manual
"""
