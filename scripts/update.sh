#!/usr/bin/env bash
set -e

DISTRO_NAME=""
DISTRO_VERSION=""
OS_RELEASE="/etc/os-release"

if [[ -f $OS_RELEASE ]]; then
  source $OS_RELEASE
  DISTRO_VERSION=$(echo "$VERSION_ID" | awk -F. '{print $1}')
  if [[ "$ID" =~ ^(rhel|rocky|centos|almalinux)$ ]] && [[ $VERSION_ID == [89]* ]]; then
    DISTRO_NAME="rhel"
    PKG_MANAGER="dnf"
  elif [[ $ID == "debian" ]] && [[ $VERSION_ID == "12" ]]; then
    DISTRO_NAME="debian"
    PKG_MANAGER="apt"
  elif [[ $ID == "ubuntu" ]] && [[ $VERSION_ID == "22.04" ]] || [[ $VERSION_ID == "24.04" ]]; then
    DISTRO_VERSION=$(echo "$VERSION_ID" | awk -F. '{print $1$2}')
    DISTRO_NAME="ubuntu"
    PKG_MANAGER="apt"
  else
    echo -e "\nUnsupported distribution or version! Supported releases: Rocky Linux 8-9, CentOS 8-9, AlmaLinux 8-9, Debian 12, Ubuntu 22.04 and Ubuntu 24.04.\n"
    exit 1
  fi
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
