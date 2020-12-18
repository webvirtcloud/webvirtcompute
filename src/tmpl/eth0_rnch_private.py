desc = "RancherOS based eth0 interface file template for private cloud"
data = """#cloud-config

rancher:
  network:
    interfaces:
      eth0:
        addresses:
        - {ipv4_addr}/{ipv4_mask}
        gateway: {ipv4_gw}
        dns:
          nameservers:
          - {ipv4_dns1}
          - {ipv4_dns2}"""
