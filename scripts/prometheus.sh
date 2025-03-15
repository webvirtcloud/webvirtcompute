#!/usr/bin/env bash
set -e

DISTRO_NAME=""
DISTRO_VERSION=""
OS_RELEASE="/etc/os-release"
PKG_MANAGER="dnf"

if [[ -f $OS_RELEASE ]]; then
  source $OS_RELEASE
  DISTRO_VERSION=$(echo "$VERSION_ID" | awk -F. '{print $1}')
  if [[ $ID == "rocky" ]] && [[ $VERSION_ID == "8" || $VERSION_ID == "9" ]]; then
    DISTRO_NAME="rhel"
  elif [[ $ID == "centos" ]] && [[ $VERSION_ID == "8" || $VERSION_ID == "9" ]]; then
    DISTRO_NAME="rhel"
  elif [[ $ID == "almalinux" ]] && [[ $VERSION_ID == "8" || $VERSION_ID == "9" ]]; then
    DISTRO_NAME="rhel"
  elif [[ $ID == "debian" ]] && [[ $VERSION_ID == "12" ]]; then
    DISTRO_NAME="debian"
    PKG_MANAGER="apt"
  fi
fi

# Check if release file is recognized
if [[ -z $DISTRO_NAME ]]; then
  echo -e "\nDistro is not recognized. Supported releases: Rocky Linux 8-9, CentOS 8-9, AlmaLinux 8-9, Debian 12.\n"
  exit 1
fi

# Check if libvirt is installed
if [[ $DISTRO_NAME == "rhel" ]]; then
  if ! dnf list installed libvirt > /dev/null 2>&1; then
    echo -e "\nPackage libvirt is not installed. Please install and configure libvirt first!\n"
    exit 1
  fi
elif [[ $DISTRO_NAME == "debian" ]]; then
  if ! dpkg -l | grep -q "libvirt-daemon-system"; then
    echo -e "\nPackage libvirt-daemon-system is not installed. Please install and configure libvirt first!\n"
    exit 1
  fi
fi

# Install prometheus
echo -e "\nInstalling and configuring prometheus..."
if [[ $DISTRO_NAME == "rhel" ]]; then
  dnf install -y epel-release
  dnf install -y golang-github-prometheus golang-github-prometheus-node-exporter
elif [[ $DISTRO_NAME == "debian" ]]; then
  apt update
  apt install -y prometheus prometheus-node-exporter
fi

# Download and install libvirt exporter
wget -O /tmp/prometheus-libvirt-exporter.tar.gz https://cloud-apps.webvirt.cloud/prometheus-libvirt-exporter-$DISTRO_NAME$DISTRO_VERSION-amd64.tar.gz
tar -xvf /tmp/prometheus-libvirt-exporter.tar.gz -C /tmp
cp /tmp/prometheus-libvirt-exporter/prometheus-libvirt-exporter /usr/local/bin/
chmod +x /usr/local/bin/prometheus-libvirt-exporter

# Apply SELinux context if applicable
if [[ $DISTRO_NAME == "rhel" ]] && command -v restorecon &> /dev/null; then
  restorecon -v /usr/local/bin/prometheus-libvirt-exporter
fi

# Configure Prometheus libvirt exporter service
cp /tmp/prometheus-libvirt-exporter/prometheus-libvirt-exporter.service /etc/systemd/system/prometheus-libvirt-exporter.service

# Add libvirt exporter to prometheus config
cat << EOF >> /etc/prometheus/prometheus.yml

  - job_name: libvirt
    # Libvirt exporter
    static_configs:
      - targets: ['localhost:9177']
EOF

# Reload systemd and enable services
systemctl daemon-reload
systemctl enable --now prometheus-libvirt-exporter

# Enable and start services based on distro-specific names
systemctl enable --now prometheus-node-exporter
systemctl enable --now prometheus

echo -e "\nInstalling and configuring prometheus... - Done!\n"

# Clean up
rm -rf /tmp/prometheus-libvirt-exporter*

exit 0
