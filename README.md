# WebVirtCompute #

WebVirtCompute is a daemon for deploying and managing virtual machines based on FastAPI and libvirt. It is designed to be used for compute nodes and backend. This project provides a REST API to manage virtual machines and their resources, making it easy to automate virtual machine management.

## Distribution ##

* AlmaLinux 8
* AlmaLinux 9
* Rocky Linux 8
* Rocky Linux 9

## Requirements ##

* qemu
* libvirt
* firewalld
* prometheus
* libguestfs-tools
* NetworkManager

## For what is it? ##

* It is a daemon for managing virtual machines based on FastAPI and libvirt.
* It is designed to be used for compute nodes and backend.
* It is a lightweight and fast daemon.
* It is easy to install and configure.
* It is only one binary file.
* It is use TLS to secure the communication between the client and the daemon.

## Hypervisor ## 

### Network Setup ###

#### Ubuntu 22.04 (Beta) ####

Install NetworkManager and firewalld:

```bash
sudo apt install -y network-manager firewalld
```

and update `/etc/netplan/00-installer-config.yaml`:

```yaml
network:
  version: 2
  renderer: NetworkManager
```

#### Debian 12 (Beta) ####

Install NetworkManager and firewalld:

```bash
sudo apt install -y network-manager firewalld
```

and change `managed` to `true` in the file `/etc/NeworkManager/NetworkManager.conf`:

```conf
[main]
plugins=ifupdown,keyfile

[ifupdown]
managed=true
```

Before installation, you have to prepare `br-ext` and `br-int` bridges for public and private networks accordingly. 

please note you will also need two networking interfaces; for example `eno1` & `eno2`

Example how to create and setup ```br-ext``` bridge on ```eno1``` interface:

```bash
nmcli conn add type bridge ifname br-ext con-name br-ext
nmcli conn add type bridge-slave ifname eno1 con-name eno1 master br-ext # NEED TO CHANGE eno1 ON YOUR INTERFACE NAME
nmcli conn modify br-ext ipv4.method manual ipv4.addresses 10.255.0.1/16 # for floating IP feature - DO NOT CHANGE
nmcli conn modify br-ext ipv4.method manual +ipv4.addresses 169.254.169.254/16 # for metadata service - DO NOT CHANGE
nmcli conn modify br-ext ipv4.method manual +ipv4.addresses 192.168.50.10/24 # NEED TO CHANGE 192.168.50.10/24 ON YOUR CIDR
nmcli conn modify br-ext ipv4.method manual ipv4.gateway 192.168.50.1 # NEED TO CHANGE 192.168.50.1 ON YOUR GATEWAY IP
nmcli conn modify br-ext ipv4.method manual ipv4.dns 8.8.8.8,1.1.1.1
nmcli conn modify br-ext bridge.stp no
nmcli conn modify br-ext 802-3-ethernet.mtu 1500
nmcli conn up eno1 # NEED TO CHANGE eno1 ON YOUR INTERFACE NAME
nmcli conn up br-ext
```

Exampale how to create and setup ```br-int``` bridge on ```eno2``` interface:

```bash
nmcli conn add type bridge ifname br-int con-name br-int ipv4.method disabled ipv6.method ignore
nmcli conn add type bridge-slave ifname eno2 con-name eno2 master br-int # NEED TO CHANGE eno2 ON YOUR INTERFACE NAME
nmcli conn modify br-int bridge.stp no
nmcli conn modify br-int 802-3-ethernet.mtu 1500
nmcli conn up eno2 # NEED TO CHANGE eno2 ON YOUR INTERFACE NAME
nmcli conn up br-int
```

For bridge interface `br-int` we don't need to set IP addresses.


### Libvirt setup ###

This script will install and configure `libvirt` with `qemu:///system` URI. You can always change settings `libvirt` and `libguestfish` if that is needed. Only create and set up `br-ext` and `br-int` bridges before running this script.

```bash
curl -fsSL https://raw.githubusercontent.com/webvirtcloud/webvirtcompute/master/scripts/libvirt.sh | sudo bash
```

### Prometheus setup ###

This script will install and configure `prometheus` with `node_exporter` and `libvirt_exporter`. You can always change settings for `prometheus` if that is needed. 

```bash
curl -fsSL https://raw.githubusercontent.com/webvirtcloud/webvirtcompute/master/scripts/prometheus.sh | sudo bash
```

### Firewall setup ###

Enable firewalld service:

```bash
systemctl enable --now firewalld
```

Base firewall rules:


```bash
WEBVIRTBACKED_IP=<you backend IP> # need put your backend IP
firewall-cmd --permanent --direct --add-rule ipv4 filter FORWARD 1 -m physdev --physdev-is-bridged -j ACCEPT # Bridge traffic rule
firewall-cmd --permanent --direct --add-rule ipv4 nat POSTROUTING 0 -d 10.255.0.0/16 -j MASQUERADE # Floating IP feature rule
firewall-cmd --permanent --direct --add-rule ipv4 nat PREROUTING 0 -i br-ext '!' -s 169.254.0.0/16 -d 169.254.169.254 -p tcp -m tcp --dport 80 -j DNAT --to-destination $WEBVIRTBACKED_IP:80 # CLoud-init metadata service rule
firewall-cmd --permanent --zone=trusted --add-source=169.254.0.0/16 # Move cloud-init metadata service to trusted zone
firewall-cmd --permanent --zone=trusted --add-interface=br-ext # Move br-ext to trusted zone
firewall-cmd --permanent --zone=trusted --add-interface=br-int # Move br-int to trusted zone
firewall-cmd --reload
```

### Install WebVirtCompute daemon ###

```bash
curl -fsSL https://raw.githubusercontent.com/webvirtcloud/webvirtcompute/master/scripts/install.sh | sudo bash
```

### Update WebVirtCompute daemon ###

```bash
curl -fsSL https://raw.githubusercontent.com/webvirtcloud/webvirtcompute/master/scripts/update.sh | sudo bash
```

### Configuring daemon (optional) ###

WebVirtCompute uses a configuration file to set up the daemon. The default configuration file is located at `/etc/webvirtcompute/webvirtcompute.ini`. You have to copy `token` and add it to WebVirtCloud admin panel when you add a new compute node.

## WebVirtCompute ##

### Build from source ###

```bash
make -f Makefile.rockylinux8 compile
make -f Makefile.rockylinux8 package
```
You can find the archive with binary in `release` directory.

### Download binary ###

You can download already built binary for:

* [almalinux8](https://cloud-apps.webvirt.cloud/webvirtcompute-almalinux8-amd64.tar.gz) 
* [rockylinux8](https://cloud-apps.webvirt.cloud/webvirtcompute-rockylinux8-amd64.tar.gz)
* [almalinux9](https://cloud-apps.webvirt.cloud/webvirtcompute-almalinux9-amd64.tar.gz) 
* [rockylinux9](https://cloud-apps.webvirt.cloud/webvirtcompute-rockylinux9-amd64.tar.gz)

## License ##

WebVirtCompute is released under the Apache 2.0 Licence. See the bundled `LICENSE` file for details.
