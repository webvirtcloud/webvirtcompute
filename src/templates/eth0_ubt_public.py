desc = "Ubuntu based Netplan eth0 interfaces file template for public cloud"
data = """network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      addresses:
        - {{ ipv4public.address }}/{{ ipv4public.prefix }}
        - {{ ipv4compute.address }}/{{ ipv4compute.prefix }}{% if ipv6public %}
        - {{ ipv6public.address }}/{{ ipv6public.prefix }}{% endif %}
      nameservers:
        search: []
        addresses: [{{ ipv4public.dns1 }}, {{ ipv4public.dns2 }}]{% if ipv6public %}
        addresses: [{{ ipv6public.dns1 }}, {{ ipv6public.dns2 }}]{% endif %}
      routes:
        - to: default
          via: {{ ipv4public.gateway }}
"""
