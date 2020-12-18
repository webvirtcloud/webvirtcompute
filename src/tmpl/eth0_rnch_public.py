desc = "RancherOS based eth0 interface file template for public cloud"
data = """#cloud-config

rancher:
  network:
    interfaces:
      eth0:
        addresses:
        - {ipv4_addr}/{ipv4_mask}
        - {ipv4anch_addr}/{ipv4anch_mask}
        - {ipv6_addr}/{ipv6_mask}
        gateway: {ipv4_gw}
        gateway_ipv6: {ipv6_gw}
        dns:
          nameservers:
          - {ipv4_dns1}
          - {ipv4_dns2}
          - {ipv6_dns1}
          - {ipv6_dns2}"""
