#!/usr/bin/env bash
set -e

DISTRO_NAME=""
DISTRO_VERSION=""
OS_RELEASE="/etc/os-release"
TOKEN=$(echo -n $(date) | sha256sum | cut -d ' ' -f1)

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

# Check if libvirt is installed (distribution-specific check)
if [[ $DISTRO_NAME == "rhel" ]]; then
  if ! dnf list installed libvirt > /dev/null 2>&1; then
    echo -e "\nPackage libvirt is not installed. Please install and configure libvirt first!\n"
    exit 1
  fi
elif [[ $DISTRO_NAME == "debian" ]] || [[ $DISTRO_NAME == "ubuntu" ]]; then
  if ! dpkg -l | grep -q "libvirt-daemon-system"; then
    echo -e "\nPackage libvirt-daemon-system is not installed. Please install and configure libvirt first!\n"
    exit 1
  fi
fi

# Install webvirtcompute
echo -e "\nInstalling webvirtcompute..."
wget -O /tmp/webvirtcompute-$DISTRO_NAME$DISTRO_VERSION-amd64.tar.gz https://cloud-apps.webvirt.cloud/webvirtcompute-$DISTRO_NAME$DISTRO_VERSION-amd64.tar.gz
tar -xvf /tmp/webvirtcompute-$DISTRO_NAME$DISTRO_VERSION-amd64.tar.gz -C /tmp
cp /tmp/webvirtcompute/webvirtcompute /usr/local/bin/webvirtcompute
chmod +x /usr/local/bin/webvirtcompute

# SELinux only exists on RHEL-based systems
if [[ $DISTRO_NAME == "rhel" ]] && command -v restorecon &> /dev/null; then
  restorecon -v /usr/local/bin/webvirtcompute
fi

mkdir -p /etc/webvirtcompute
cp /tmp/webvirtcompute/webvirtcompute.ini /etc/webvirtcompute/webvirtcompute.ini
sed -i "s/token = .*/token = $TOKEN/" /etc/webvirtcompute/webvirtcompute.ini
cp /tmp/webvirtcompute/webvirtcompute.service /etc/systemd/system/webvirtcompute.service
systemctl daemon-reload
systemctl enable --now webvirtcompute
echo -e "Installing webvirtcompute... - Done!\n"

# Show token
echo -e "\nYour webvirtcompue connection token is: \n\t\n$TOKEN\n\nPlease add it to admin panel when you add the compute node.\n"

# Cleanup
rm -rf /tmp/webvirtcompute*

exit 0
