desc = "RedHat based NetworkManager eth0 interface file template for public cloud"
data = """[connection]
id=eth0
type=ethernet
interface-name=eth0
autoconnect-priority=-999

[ethernet]

[ipv4]
address1={{ ipv4public.address }}/{{ ipv4public.prefix }}
address2={{ ipv4compute.address }}/{{ ipv4compute.prefix }}
gateway={{ ipv4public.gateway }}
dns={{ ipv4public.dns1 }};{{ ipv4public.dns2 }};
method=manual

[ipv6]
{% if ipv6public %}
address1={{ ipv6public.address }}/{{ ipv6public.prefix }}
gateway={{ ipv6public.gateway }}
dns={{ ipv6public.dns1 }};{{ ipv6public.dns2 }};
method=manual
{% else}
addr-gen-mode=default
method=auto
{% endif %}

[proxy]
"""
