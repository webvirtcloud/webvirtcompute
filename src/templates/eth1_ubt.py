desc = "Ubuntu based Netplan eth1 interfaces file template"
data = """
    eth1:
      addresses:
        - {{ ipv4private.address }}/{{ ipv4private.prefix }}}"""
