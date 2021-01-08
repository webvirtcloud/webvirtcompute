#!/usr/bin/env bash
set -e

# Install packages
dnf install -y epel-release
dnf install -y bash-completion \
               libgcrypt libvirt libguestfs-tools \
               python36 python36-devel python3-firewall python3-libvirt python3-libguestfs
               

# Enable libvirt
systemctl enable --now libvirtd

echo ""
echo "Done!"

exit 0
