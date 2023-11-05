#!/usr/bin/env bash
set -e

DISTRO_NAME=""
DISTRO_VERSION=""
OS_RELEASE="/etc/os-release"
TOKEN=$(echo -n $(date) | sha256sum | cut -d ' ' -f1)

if [[ -f $OS_RELEASE ]]; then
  source $OS_RELEASE
  if [[ $ID == "rocky" ]]; then
    DISTRO_NAME="rockylinux "
  elif [[ $ID == "centos" ]]; then
    DISTRO_NAME="centos"
  elif [[ $ID == "almalinux" ]]; then
    DISTRO_NAME="almalinux"
  fi
    DISTRO_VERSION=$(echo "$VERSION_ID" | awk -F. '{print $1}')
fi

# Check if release file is recognized
if [[ -z $DISTRO_NAME ]]; then
  echo -e "\nRelease file not recognized. Supported releases: Rocky Linux 8-9, CentOS 8-9, AlmaLinux 8-9.\n"
  exit 1
fi

# Check if libvirt is installed
if ! dnf list installed libvirt >/dev/null 2>&1; then
  echo -e "\nPackage libvirt is not installed. Please install and configure libvirt first!\n"
  exit 1
fi

# Install webvirtcompute
echo -e "\nInstalling webvirtcompute..."
wget -O /tmp/webvirtcompute-$DISTRO_NAME$DISTRO_VERSION-amd64.tar.gz https://cloud-apps.webvirt.cloud/webvirtcompute-$DISTRO_NAME$DISTRO_VERSION-amd64.tar.gz
tar -xvf /tmp/webvirtcompute-$DISTRO_NAME$DISTRO_VERSION-amd64.tar.gz -C /tmp
cp /tmp/webvirtcompute-$DISTRO_NAME$DISTRO_VERSION-amd64/webvirtcompute /usr/local/bin/webvirtcompute
chmod +x /usr/local/bin/webvirtcompute
restorecon -v /usr/local/bin/webvirtcompute
mkdir /etc/webvirtcompute
cp /tmp/webvirtcompute/webvirtcompute.ini /etc/webvirtcompute/webvirtcompute.ini
sed -i "s/token = .*/token = $TOKEN/" /etc/webvirtcompute/webvirtcompute.ini
cp /tmp/webvirtcompute/webvirtcompute.service /etc/systemd/system/webvirtcompute.service
systemctl daemon-reload
systemctl enable --now webvirtcompute
echo -e "Installing webvirtcompute... - Done!\n"

# Cleanup
rm -rf /tmp/webvirtcompute-$DISTRO_NAME$DISTRO_VERSION-amd64.tar.gz

exit 0
