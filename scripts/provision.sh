#!/usr/bin/env bash
set -e

# Install packages
dnf install -y epel-release
dnf install -y bash-completion wget \
               libgcrypt libvirt libguestfs-tools \
               python36 python3-libvirt python3-libguestfs
               
# Setup folders
mkdir /var/lib/libvirt/isos
mkdir /var/lib/libvirt/backups

# Enable libvirt
systemctl enable --now libvirtd
systemctl enable --now libvirt-guests

# Setup libvirt storage
virsh pool-define /vagrant/libvirt/isos.xml
virsh pool-define /vagrant/libvirt/images.xml
virsh pool-define /vagrant/libvirt/backups.xml
virsh pool-start isos
virsh pool-start images
virsh pool-start backups
virsh pool-autostart isos
virsh pool-autostart images
virsh pool-autostart backups

# Setup libvirt network
virsh net-destroy default
virsh net-undefine default
virsh net-define /vagrant/libvirt/private.xml
virsh net-define /vagrant/libvirt/public.xml
virsh net-start private
virsh net-start public
virsh net-autostart private
virsh net-autostart public

# Setup libvirt nwfilter
virsh nwfilter-define /vagrant/libvirt/allow-incoming-ipv6.xml
virsh nwfilter-define /vagrant/libvirt/no-ipv6-spoofing.xml
virsh nwfilter-define /vagrant/libvirt/clean-traffic-ipv6.xml

# Tune profile
tuned-adm profile virtual-host

# Download rescue iso
wget https://mirrors.finnix.org/releases/121/finnix-121.iso -O /var/lib/libvirt/isos/rescue.iso > /dev/null 2>&1

# Prometheus Server
cd /tmp
mkdir /var/lib/prometheus
groupadd --system prometheus
useradd -s /sbin/nologin -d /var/lib/prometheus --system -g prometheus prometheus
for i in rules rules.d files_sd; do mkdir -p /etc/prometheus/${i}; done
curl -s https://api.github.com/repos/prometheus/prometheus/releases/latest | grep browser_download_url | grep linux-amd64 | cut -d '"' -f 4 | wget -qi - > /dev/null 2>&1
tar -zxf prometheus*.tar.gz
cd prometheus*/
mv prometheus promtool /usr/local/bin/
mv consoles/ console_libraries/ /etc/prometheus/
for i in rules rules.d files_sd; do chown -R prometheus:prometheus /etc/prometheus/${i}; done
for i in rules rules.d files_sd; do chmod -R 775 /etc/prometheus/${i}; done
chown -R prometheus:prometheus /var/lib/prometheus/
cat << EOF > /etc/prometheus/prometheus.yml
# my global config
global:
  scrape_interval:     15s # Set the scrape interval to every 15 seconds. Default is every 1 minute.
  evaluation_interval: 15s # Evaluate rules every 15 seconds. The default is every 1 minute.
  # scrape_timeout is set to the global default (10s).

# Alertmanager configuration
alerting:
  alertmanagers:
  - static_configs:
    - targets:
      # - alertmanager:9093

# Load rules once and periodically evaluate them according to the global 'evaluation_interval'.
rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

# A scrape configuration containing exactly one endpoint to scrape:
# Here it's Prometheus itself.
scrape_configs:
  # The job name is added as a label \`job=<job_name>\` to any timeseries scraped from this config.
  - job_name: 'prometheus'

    # metrics_path defaults to '/metrics'
    # scheme defaults to 'http'.

    static_configs:
    - targets: ['localhost:9090']

  - job_name: 'libvirt'

    # metrics_path defaults to '/metrics'
    # scheme defaults to 'http'.

    static_configs:
    - targets: ['localhost:9177']

EOF
cat << EOF > /etc/systemd/system/prometheus.service
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/usr/local/bin/prometheus \
    --config.file=/etc/prometheus/prometheus.yml \
    --web.console.templates=/etc/prometheus/consoles \
    --web.console.libraries=/etc/prometheus/console_libraries \
    --storage.tsdb.path=/var/lib/prometheus \
    --storage.tsdb.retention.time=31d
SyslogIdentifier=prometheus
Restart=always

[Install]
WantedBy=multi-user.target
EOF
systemctl enable --now prometheus

# Prometheus Libvirt Exporter
cd /tmp
curl -s https://api.github.com/repos/retspen/libvirt_exporter/releases/latest | grep browser_download_url | grep linux-amd64 | cut -d '"' -f 4 | wget -qi - > /dev/null 2>&1
tar -zxf libvirt_exporter*.tar.gz
mv libvirt_exporter /usr/local/bin/
cat << EOF > /etc/systemd/system/libvirt_exporter.service
[Unit]
Description=LibVirt Exporter
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/usr/local/bin/libvirt_exporter --web.listen-address=localhost:9177
SyslogIdentifier=libvirt_exporter
Restart=always

[Install]
WantedBy=multi-user.target
EOF
systemctl enable --now libvirt_exporter

echo ""
echo "Done!"

exit 0
