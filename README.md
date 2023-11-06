# WebVirtCompute #

WebVirtCompute is a daemon for deploying and managing virtual machines based on FastAPI and libvirt. This project provides a REST API to manage virtual machines and their resources, making it easy to automate virtual machine management. 

## Distribution ##

* AlmaLinux 8
* AlmaLinux 9
* Rocky Linux 8
* Rocky Linux 9

## Configuring KVM host ##

### Network ###

Before install you have to prepare `br-ext` and `br-int` bridges for public and private network accordingly.
Like example below:

```bash
nmcli connection add type bridge ifname br-ext con-name br-ext ipv4.method disabled ipv6.method ignore
nmcli connection add type bridge-slave ifname eno1 con-name eno1 master br-ext
nmcli connection modify br-ext bridge.stp no
nmcli connection modify br-ext 802-3-ethernet.mtu 1500
nmcli connection up eno1
nmcli connection up br-ext
```

### Libvirt ###

```bash
curl https://raw.githubusercontent.com/webvirtcloud/webvirtcompute/master/scripts/libvirt.sh | sudo bash
```
#### Firewall ####

```bash
WEBVIRTBACKED_IP=<you backend IP>
firewall-cmd --permanent --direct --add-rule ipv4 filter FORWARD 1 -m physdev --physdev-is-bridged -j ACCEPT
firewall-cmd --permanent --direct --add-rule ipv4 nat POSTROUTING 0 -d 10.255.0.0/16 -j MASQUERADE
firewall-cmd --permanent --direct --add-rule ipv4 nat PREROUTING 0 -i br-ext '!' -s 169.254.0.0/16 -d 169.254.169.254 -p tcp -m tcp --dport 80 -j DNAT --to-destination $WEBVIRTBACKED_IP:8080
firewall-cmd --permanent --zone=trusted --add-source=169.254.0.0/16
firewall-cmd --permanent --zone=trusted --add-interface=br-ext
firewall-cmd --permanent --zone=trusted --add-interface=br-int
firewall-cmd --reload
```

## WebVirtCompute ##

### Install binary ###

```bash
curl https://raw.githubusercontent.com/webvirtcloud/webvirtcompute/master/scripts/install.sh | sudo bash
```

#### Configuration ####

WebVirtCompute uses a configuration file to set up the daemon. The default configuration file is located at `/etc/webvirtcompute/webvirtcompute.ini`. You have to copy `token` and add to WebVirtCloud admin panel when you add new compute node.

### Build from source ###
```bash
make -f Makefile.rockylinux8 compile
make -f Makefile.rockylinux8 package
```
You can find archive with binary in `release` directory.

## Binary ##

You can download already built binary for:

* [almalinux8](https://cloud-apps.webvirt.cloud/webvirtcompute-almalinux8-amd64.tar.gz) 
* [rockylinux8](https://cloud-apps.webvirt.cloud/webvirtcompute-rockylinux8-amd64.tar.gz)
* [almalinux9](https://cloud-apps.webvirt.cloud/webvirtcompute-almalinux9-amd64.tar.gz) 
* [rockylinux9](https://cloud-apps.webvirt.cloud/webvirtcompute-rockylinux9-amd64.tar.gz)

## License ##

WebVirtCompute is released under the Apache 2.0 Licence. See the bundled `LICENSE` file for details.