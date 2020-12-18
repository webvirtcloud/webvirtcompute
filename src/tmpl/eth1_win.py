desc = "Windows based eth1 interface file template"
data = """REM IPv4 Private
netsh interface ipv4 add address "Ethernet 2" {ipv4_addr} {ipv4_mask}"""
