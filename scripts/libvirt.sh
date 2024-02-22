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

# Check if br-ext is configured
if ! ip link show br-ext > /dev/null 2>&1; then
  echo -e "\nBridge br-ext is not found. Please configure it first!\n"
  exit 1
fi

# Check if br-int is configured
if ! ip link show br-int > /dev/null 2>&1; then
  echo -e "\nBridge br-int is not found. Please configure it first!\n"
  exit 1
fi

# Install libvirt and libguestfish
echo -e "\nInstalling libvirt and libguestfish..."
dnf install -y epel-release
dnf install -y tuned libvirt qemu-kvm xmlstarlet cyrus-sasl-md5 qemu-guest-agent libguestfs-tools libguestfs-rescue libguestfs-winsupport libguestfs-bash-completion
echo -e "Installing libvirt and libguestfish... - Done!\n"

echo -e "\nConfiguring libvirt..."

# Enable SASL for qemu
sed -i 's/#vnc_sasl/vnc_sasl/g' /etc/libvirt/qemu.conf

# Allow VNC connections to qemu
sed -i 's/#vnc_listen/vnc_listen/g' /etc/libvirt/qemu.conf

# Enable virt-host profile
tuned-adm profile virtual-host

# Add sysctl parameters
cat << EOF >> /etc/sysctl.d/99-bridge.conf
net.ipv4.ip_forward=1
net.ipv4.conf.all.rp_filter=0
net.ipv4.conf.default.rp_filter=0
net.bridge.bridge-nf-call-arptables=1
net.bridge.bridge-nf-call-iptables=1
net.bridge.bridge-nf-call-ip6tables=1
EOF

# Apply sysctl parameters
sysctl --system

# Enable and start libvirtd
systemctl enable --now libvirtd-tcp.socket
systemctl enable --now libvirt-guests
systemctl stop libvirtd-ro.socket
systemctl stop libvirtd.socket
systemctl stop libvirtd.service

# Create storage pool for images
virsh pool-define-as images dir - - - - "/var/lib/libvirt/images"
virsh pool-build images && virsh pool-start images && virsh pool-autostart images

# Create storage pool for ISOs
mkdir /var/lib/libvirt/isos
virsh pool-define-as isos dir - - - - "/var/lib/libvirt/isos"
virsh pool-build isos && virsh pool-start isos && virsh pool-autostart isos

# Create storage pool for backups
mkdir /var/lib/libvirt/backups
virsh pool-define-as backups dir - - - - "/var/lib/libvirt/backups"
virsh pool-build backups && virsh pool-start backups && virsh pool-autostart backups

# Remove network pool default
virsh net-destroy default
virsh net-undefine default

# Create network pool public
cat <<EOF | virsh net-define /dev/stdin
<network>
    <name>public</name>
    <forward mode='bridge'/>
    <bridge name='br-ext'/>
</network>
EOF
virsh net-start public && virsh net-autostart public

# Create network pool private
cat <<EOF | virsh net-define /dev/stdin
<network>
    <name>private</name>
    <forward mode='bridge'/>
    <bridge name='br-int'/>
</network>
EOF
virsh net-start private && virsh net-autostart private

# Create nwfiler rule for IPv6
cat <<EOF | virsh nwfilter-define /dev/stdin
<filter name='clean-traffic-ipv6' chain='root'>
    <filterref filter='no-mac-spoofing'/>
    <filterref filter='no-ip-spoofing'/>
    <rule action='accept' direction='out' priority='-650'>
        <mac protocolid='ipv4'/>
    </rule>
    <filterref filter='no-ipv6-spoofing'/>
    <rule action='accept' direction='out' priority='-650'>
        <mac protocolid='ipv6'/>
    </rule>
    <filterref filter='allow-incoming-ipv4'/>
    <filterref filter='allow-incoming-ipv6'/>
    <filterref filter='no-arp-spoofing'/>
    <rule action='accept' direction='inout' priority='-500'>
        <mac protocolid='arp'/>
    </rule>
    <filterref filter='no-other-l2-traffic'/>
    <filterref filter='qemu-announce-self'/>
</filter>
EOF
echo -e "Configuring libvirt... - Done!\n"


# Dowload recovery image
echo -e "\nDownloading recovery image..."
wget -O /var/lib/libvirt/isos/finnix-125.iso https://www.finnix.org/releases/125/finnix-125.iso
echo -e "Downloading recovery image... - Done!\n"

# Enable firewall
systemctl enable --now firewalld

exit 0