#!/usr/bin/env bash
set -e

DISTRO_NAME=""
DISTRO_VERSION=""
OS_RELEASE="/etc/os-release"

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
  echo -e "\nDistro is not recognized. Supported releases: Rocky Linux 8-9, CentOS 8-9, AlmaLinux 8-9.\n"
  exit 1
fi

# Update webvirtcompute
echo -e "\nUpdating webvirtcompute..."
wget -O /tmp/webvirtcompute-$DISTRO_NAME$DISTRO_VERSION-amd64.tar.gz https://cloud-apps.webvirt.cloud/webvirtcompute-$DISTRO_NAME$DISTRO_VERSION-amd64.tar.gz
tar -xvf /tmp/webvirtcompute-$DISTRO_NAME$DISTRO_VERSION-amd64.tar.gz -C /tmp
systemctl stop webvirtcompute
cp /tmp/webvirtcompute/webvirtcompute /usr/local/bin/webvirtcompute
chmod +x /usr/local/bin/webvirtcompute
restorecon -v /usr/local/bin/webvirtcompute
systemctl start webvirtcompute
echo -e "Updating webvirtcompute... - Done!\n"

# Cleanup
rm -rf /tmp/webvirtcompute*

exit 0
