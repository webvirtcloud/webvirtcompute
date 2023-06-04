# WebVirtCompute #

WebVirtCompute is a daemon for deploying and managing virtual machines based on FastAPI and libvirt. This project provides a REST API to manage virtual machines and their resources, making it easy to automate virtual machine management.

## Distribution ##

* Rocky Linux 8
* Rocky Linux 9

## Installation ##

To install WebVirtCompute, you need to download already built binary.

### Install ###
```bash
cd /tmp/
wget https://cloud-apps.webvirt.cloud/webvirtcompute-rockylinux8-amd64.tar.gz
tar -xvf webvirtcompute-rockylinux8-amd64.tar.gz
cd webvirtcompute
sudo cp webvirtcompute /usr/local/bin/
sudo cp webvirtcompute.service /etc/systemd/system/
sudo mkdir -p /etc/webvirtcompute
sudo cp webvirtcompute.ini /etc/webvirtcompute/
sudo systemctl daemon-reload
sudo systemctl enable --now webvirtcompute
```
### Configuration ###

WebVirtCompute uses a configuration file to set up the daemon. The default configuration file is located at `/etc/webvirtcompute/webvirtcompute.ini`. You need to change default `token` variable. You can generate token with `openssl rand -hex 32` command.

## Build ##
```bash
make -f Makefile.rockylinux8 compile
make -f Makefile.rockylinux8 package
```
You can find archive with binary in `release` directory.

## Binary ##

You can download already built binary for [rockylinux8](https://cloud-apps.webvirt.cloud/webvirtcompute-rockylinux8-amd64.tar.gz) and for [rockylinux9](https://cloud-apps.webvirt.cloud/webvirtcompute-rockylinux9-amd64.tar.gz).

## License ##

WebVirtCompute is released under the Apache 2.0 Licence. See the bundled `LICENSE` file for details.