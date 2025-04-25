desc = "RedHat based NetworkManager eth0 interface file template for private cloud"
data = """[connection]
id=eth0
type=ethernet
interface-name=eth0
autoconnect-priority=-999

[ethernet]

[ipv4]
address1={{ ipv4public.address }}/{{ ipv4public.prefix }}
gateway={{ ipv4public.gateway }}
dns={{ ipv4public.dns1 }};{{ ipv4public.dns2 }};
method=manual

[ipv6]
addr-gen-mode=default
method=auto

[proxy]
"""
