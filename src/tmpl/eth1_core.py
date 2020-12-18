desc = "CoreOS based eth1 interfaces file template"
data = """
    - name: 00-eth1.network
      runtime: true
      content: |
        [Match]
        Name=eth1

        [Network]
        Address={ipv4_addr}/{ipv4_mask}"""
