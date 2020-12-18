desc = "Windows based eth0 interface file template for private cloud"
data = """@echo off
echo  ##############################################################################
echo  #                                                                            #
echo  #                            FIRST BOOT SETUP                                #
echo  #                                                                            #
echo  #         Please don't close the window it will closed automatically         #
echo  #                                                                            #
echo  ##############################################################################

REM IPv4 Public
netsh interface ipv4 delete dnsservers "Ethernet" all
netsh interface ipv4 reset
netsh interface ipv4 set address "Ethernet" static {ipv4_addr} {ipv4_mask} {ipv4_gw}
netsh interface ipv4 add dnsservers "Ethernet" {ipv4_dns1}
netsh interface ipv4 add dnsservers "Ethernet" {ipv4_dns2} index=2"""
