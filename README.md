# WebVirtCompute #

WebVirtCompute is a daemon for deploying and managing virtual machines based on FastAPI and libvirt. This project provides a REST API to manage virtual machines and their resources, making it easy to automate virtual machine management. 

## Distribution ##

* AlmaLinux 8
* AlmaLinux 9
* Rocky Linux 8
* Rocky Linux 9

## Installation ##

Before install you have to install and configue `libvirt` daemon. To install WebVirtCompute, you need to download already built binary.

### Install ###

```bash
curl https://raw.githubusercontent.com/webvirtcloud/webvirtcompute/master/scripts/install.sh | sudo bash
```

### Configuration ###

WebVirtCompute uses a configuration file to set up the daemon. The default configuration file is located at `/etc/webvirtcompute/webvirtcompute.ini`. You have to copy `token` and add to WebVirtCloud admin panel when you add new compute node.

## Build ##
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