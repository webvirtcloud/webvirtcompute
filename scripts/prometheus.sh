#!/usr/bin/env bash
set -e

DISTRO_NAME=""
DISTRO_VERSION=""
OS_RELEASE="/etc/os-release"
TOKEN=$(echo -n $(date) | sha256sum | cut -d ' ' -f1)

if [[ -f $OS_RELEASE ]]; then
  source $OS_RELEASE
  if [[ $ID == "rocky" ]]; then
    DISTRO_NAME="rockylinux"
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

# Check if libvirt is installed
if ! dnf list installed libvirt > /dev/null 2>&1; then
  echo -e "\nPackage libvirt is not installed. Please install and configure libvirt first!\n"
  exit 1
fi

# Install prometheus
echo -e "\nInstalling and configuring prometheus..."
dnf install -y epel-release
dnf install -y golang-github-prometheus golang-github-prometheus-node-exporter
wget -O /tmp/prometheus-libvirt-exporter-0.0.1.linux-amd64.tar.gz https://github.com/retspen/libvirt-exporter/releases/download/0.1.0/prometheus-libvirt-exporter-0.0.1.linux-amd64.tar.gz
tar -xvf /tmp/prometheus-libvirt-exporter-0.0.1.linux-amd64.tar.gz -C /tmp
cp /tmp/prometheus-libvirt-exporter-0.0.1.linux-amd64/prometheus-libvirt-exporter /usr/local/bin/
restorecon -v /usr/local/bin/prometheus-libvirt-exporter
cp /tmp/prometheus-libvirt-exporter/prometheus-libvirt-exporter.service /etc/systemd/system/prometheus-libvirt-exporter.service
cat << EOF >> /etc/prometheus/prometheus.yml

  - job_name: libvirt
    # Libvirt exporter
    static_configs:
      - targets: ['localhost:9177']
EOF
systemctl daemon-reload
systemctl enable --now prometheus-libvirt-exporter
systemctl enable --now prometheus-node-exporter
systemctl enbale --now prometheus
echo -e "Installing and configuring prometheus... - Done!\n"

# Clean up
rm -rf /tmp/prometheus-libvirt-exporter*

exit 0
