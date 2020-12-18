desc = "CoreOS based eth0 interfaces file template for public cloud"
data = """#cloud-config

coreos:
    oem:
      id: simplystack
      name: SimplyStack
      version-id: 0.0.1
      home-url: https://www.simplystack.com/
      bug-report-url: https://github.com/coreos/bugs/issues
    units:
    - name: 00-eth0.network
      runtime: true
      content: |
        [Match]
        Name=eth0

        [Network]
        Address={ipv4_addr}/{ipv4_mask}
        Gateway={ipv4_gw}
        DNS={ipv4_dns1}

        [Network]
        Address={ipv4anch_addr}/{ipv4anch_mask}

        [Network]
        Address={ipv6_addr}/{ipv6_mask}
        Gateway={ipv6_gw}
        DNS={ipv6_dns1}"""
