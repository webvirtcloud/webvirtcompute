desc = "Ubuntu based Netplan eth0 interfaces file template for private cloud"
data = """network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      addresses:
        - {{ ipv4public.address }}/{{ ipv4public.prefix }}
      nameservers:
        search: []
        addresses: [{{ ipv4public.dns1 }}, {{ ipv4public.dns2 }}]
      routes:
        - to: default
          via: {{ ipv4public.gateway }}
"""
