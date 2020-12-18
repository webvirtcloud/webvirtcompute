desc = "CoreOS based eth0 interfaces file template for private cloud"
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
        DNS={ipv4_dns2}"""
