#
# util - HubGridCloud utils for managing VM's filesystem
# UUID regexp - '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
#

import re
import guestfs
from .logger import method_logger

from tmpl import eth1_rnch
from tmpl import eth0_rnch_public
from tmpl import eth0_rnch_private

from tmpl import eth1_core
from tmpl import eth0_core_public
from tmpl import eth0_core_private

from tmpl import eth1_win
from tmpl import eth0_win_public
from tmpl import eth0_win_private

from tmpl import eth1_rhl
from tmpl import eth0_rhl_public
from tmpl import eth0_rhl_private

from tmpl import eth1_deb
from tmpl import eth2_deb
from tmpl import eth0_deb_public
from tmpl import eth0_deb_private


class GuestFSUtil(object):
    @method_logger()
    def __init__(self, drive, distro):
        self.drive = drive
        self.distro = distro
        self.gfs = guestfs.GuestFS(python_return_dict=True)
        self.gfs.add_drive(drive)
        self.gfs.launch()

    @method_logger()
    def get_distro(self):
        if 'fedora' in self.distro:
            return 'rhl'
        if 'centos' in self.distro:
            return 'rhl'
        if 'ubuntu' in self.distro:
            return 'deb'
        if 'debian' in self.distro:
            return 'deb'
        if 'windows' in self.distro:
            return 'win'
        if 'coreos' in self.distro:
            return 'core'
        if 'atomic' in self.distro:
            return 'atom'
        if 'rancheros' in self.distro:
            return 'rnch'
        if 'alpine' in self.distro:
            return 'alpn'

    @method_logger()
    def root_device(self):
        device = '/dev/sda1'
        if self.get_distro() == 'core':
            device = '/dev/sda6'
        if self.get_distro() == 'atom':
            device = '/dev/atomicos/root'
        if self.get_distro() == 'alpn':
            device = '/dev/sda3'
        return device

    @method_logger()
    def ostree_path(self):
        ostree_path = '/ostree/boot.0/centos-atomic-host'
        root_uuid = self.gfs.ls(ostree_path)
        return ostree_path + '/' + root_uuid[0] + '/0'

    @method_logger()
    def coreos_config_path(self):
        return '/cloud-config.yml'

    @method_logger()
    def rancheros_config_path(self):
        return '/var/lib/rancher/conf/cloud-config.yml'

    @method_logger()
    def cloud_init_path(self):
        path = '/var/lib/cloud'
        if self.get_distro() == 'atom':
            path = self.ostree_path() + path
        return path

    @method_logger()
    def shadow_file_path(self):
        path = '/etc/shadow'
        if self.get_distro() == 'atom':
            path = self.ostree_path() + path
        return path

    @method_logger()
    def hostname_file_path(self):
        path = '/etc/hostname'
        if self.get_distro() == 'atom':
            path = self.ostree_path() + path
        return path

    @method_logger()
    def root_ssh_dir_path(self):
        path = '/root/.ssh'
        if self.get_distro() == 'atom':
            path = '/ostree/deploy/centos-atomic-host/var/roothome/.ssh'
        return path

    @method_logger()
    def root_auth_keys_path(self):
        path = '/root/.ssh/authorized_keys'
        if self.get_distro() == 'atom':
            path = '/ostree/deploy/centos-atomic-host/var/roothome/.ssh/authorized_keys'
        return path

    @method_logger()
    def _win_str_disk_extend(self):
        return 'diskpart /s %~dp0\\diskpart.txt\r\n'

    @method_logger()
    def _win_str_shutdown(self):
        return 'shutdown /r /t 1\r\n'

    @method_logger()
    def _win_clean_cloudinit(self):
        return 'type NUL > %~dp0\\cloudinit.cmd\r\n'

    @method_logger()
    def nic_file_path(self, nic_type='public'):
        f_path = ''
        if self.get_distro() == 'deb' or self.get_distro() == 'alpn':
            f_path = '/etc/network/interfaces'
        if self.get_distro() == 'rhl':
            if nic_type == 'public':
                f_path = '/etc/sysconfig/network-scripts/ifcfg-eth0'
            if nic_type == 'private':
                f_path = '/etc/sysconfig/network-scripts/ifcfg-eth1'
        if self.get_distro() == 'atom':
            if nic_type == 'public':
                f_path = self.ostree_path() + '/etc/sysconfig/network-scripts/ifcfg-eth0'
            if nic_type == 'private':
                f_path = self.ostree_path() + '/etc/sysconfig/network-scripts/ifcfg-eth1'
        if self.get_distro() == 'win':
            f_path = '/Windows/System32/GroupPolicy/Machine/Scripts/Startup/cloudinit.cmd'
        if self.get_distro() == 'core':
            f_path = self.coreos_config_path()
        if self.get_distro() == 'rnch':
            f_path = self.rancheros_config_path()
        return f_path

    @method_logger()
    def deb_eth0_data(self, ipv4public, ipv4anchor={}, ipv6public={}, cloud='public'):
        f_eth0 = ''
        if cloud == 'public':
            f_eth0 = eth0_deb_public.data.format(
                ipv4_addr=ipv4public.get('address'),
                ipv4_mask=ipv4public.get('mask'),
                ipv4_gw=ipv4public.get('gateway'),
                ipv4_dns1=ipv4public.get('dns1'),
                ipv4_dns2=ipv4public.get('dns2'),
                ipv4anch_addr=ipv4anchor.get('address'),
                ipv4anch_mask=ipv4anchor.get('mask'),
                ipv6_addr=ipv6public.get('address'),
                ipv6_mask=ipv6public.get('prefix'),
                ipv6_gw=ipv6public.get('gateway'),
                ipv6_dns1=ipv6public.get('dns1'),
                ipv6_dns2=ipv6public.get('dns2')
            )
        if cloud == 'private':
            f_eth0 = eth0_deb_private.data.format(
                ipv4_addr=ipv4public.get('address'),
                ipv4_mask=ipv4public.get('mask'),
                ipv4_gw=ipv4public.get('gateway'),
                ipv4_dns1=ipv4public.get('dns1'),
                ipv4_dns2=ipv4public.get('dns2')
            )
        return f_eth0

    @method_logger()
    def deb_eth1_data(self, ipv4private):
        f_eth1 = eth1_deb.data.format(
            ipv4_addr=ipv4private.get('address'),
            ipv4_mask=ipv4private.get('mask')
        )
        return f_eth1

    @method_logger()
    def deb_eth2_data(self, ipv4private):
        f_eth2 = eth2_deb.data.format(
            ipv4_addr=ipv4private.get('address'),
            ipv4_mask=ipv4private.get('mask')
        )
        return f_eth2

    @method_logger()
    def rhl_eth0_data(self, ipv4public, ipv4anchor={}, ipv6public={}, cloud='public'):
        f_eth0 = ''
        if cloud == 'public':
            f_eth0 = eth0_rhl_public.data.format(
                ipv4_addr=ipv4public.get('address'),
                ipv4_mask=ipv4public.get('mask'),
                ipv4_gw=ipv4public.get('gateway'),
                ipv4_dns1=ipv4public.get('dns1'),
                ipv4_dns2=ipv4public.get('dns2'),
                ipv4anch_addr=ipv4anchor.get('address'),
                ipv4anch_mask=ipv4anchor.get('prefix'),
                ipv6_addr=ipv6public.get('address'),
                ipv6_mask=ipv6public.get('prefix'),
                ipv6_gw=ipv6public.get('gateway'),
                ipv6_dns1=ipv6public.get('dns1'),
                ipv6_dns2=ipv6public.get('dns2')
            )
        if cloud == 'private':
            f_eth0 = eth0_rhl_private.data.format(
                ipv4_addr=ipv4public.get('address'),
                ipv4_mask=ipv4public.get('mask'),
                ipv4_gw=ipv4public.get('gateway'),
                ipv4_dns1=ipv4public.get('dns1'),
                ipv4_dns2=ipv4public.get('dns2')
            )
        return f_eth0

    @method_logger()
    def rhl_eth1_data(self, ipv4private):
        f_eth1 = eth1_rhl.data.format(
            ipv4_addr=ipv4private.get('address'),
            ipv4_mask=ipv4private.get('mask')
        )
        return f_eth1

    @method_logger()
    def win_eth0_data(self, ipv4public, ipv4anchor={}, ipv6public={}, cloud='public'):
        f_eth0 = ''
        if cloud == 'public':
            f_eth0 = eth0_win_public.data.format(
                ipv4_addr=ipv4public.get('address'),
                ipv4_mask=ipv4public.get('mask'),
                ipv4_gw=ipv4public.get('gateway'),
                ipv4_dns1=ipv4public.get('dns1'),
                ipv4_dns2=ipv4public.get('dns2'),
                ipv4anch_addr=ipv4anchor.get('address'),
                ipv4anch_mask=ipv4anchor.get('prefix'),
                ipv6_addr=ipv6public.get('address'),
                ipv6_mask=ipv6public.get('prefix'),
                ipv6_gw=ipv6public.get('gateway'),
                ipv6_dns1=ipv6public.get('dns1'),
                ipv6_dns2=ipv6public.get('dns2')
            )
        if cloud == 'private':
            f_eth0 = eth0_win_private.data.format(
                ipv4_addr=ipv4public.get('address'),
                ipv4_mask=ipv4public.get('mask'),
                ipv4_gw=ipv4public.get('gateway'),
                ipv4_dns1=ipv4public.get('dns1'),
                ipv4_dns2=ipv4public.get('dns2')
            )
        return f_eth0

    @method_logger()
    def win_eth1_data(self, ipv4private):
        f_eth1 = eth1_win.data.format(
            ipv4_addr=ipv4private.get('address'),
            ipv4_mask=ipv4private.get('mask')
        )
        return f_eth1

    @method_logger()
    def core_eth0_data(self, ipv4public, ipv4anchor={}, ipv6public={}, cloud='public'):
        f_eth0 = ''
        if cloud == 'public':
            f_eth0 = eth0_core_public.data.format(
                ipv4_addr=ipv4public.get('address'),
                ipv4_mask=ipv4public.get('prefix'),
                ipv4_gw=ipv4public.get('gateway'),
                ipv4_dns1=ipv4public.get('dns1'),
                ipv4anch_addr=ipv4anchor.get('address'),
                ipv4anch_mask=ipv4anchor.get('prefix'),
                ipv6_addr=ipv6public.get('address'),
                ipv6_mask=ipv6public.get('prefix'),
                ipv6_gw=ipv6public.get('gateway'),
                ipv6_dns1=ipv6public.get('dns1'),
            )
        if cloud == 'private':
            f_eth0 = eth0_core_private.data.format(
                ipv4_addr=ipv4public.get('address'),
                ipv4_mask=ipv4public.get('prefix'),
                ipv4_gw=ipv4public.get('gateway'),
                ipv4_dns1=ipv4public.get('dns1'),
                ipv4_dns2=ipv4public.get('dns2')
            )
        return f_eth0

    @method_logger()
    def core_eth1_data(self, ipv4private):
        f_eth1 = eth1_core.data.format(
            ipv4_addr=ipv4private.get('address'),
            ipv4_mask=ipv4private.get('prefix')
        )
        return f_eth1

    @method_logger()
    def rnch_eth0_data(self, ipv4public, ipv4anchor={}, ipv6public={}, cloud='public'):
        f_eth0 = ''
        if cloud == 'public':
            f_eth0 = eth0_rnch_public.data.format(
                ipv4_addr=ipv4public.get('address'),
                ipv4_mask=ipv4public.get('prefix'),
                ipv4_gw=ipv4public.get('gateway'),
                ipv4_dns1=ipv4public.get('dns1'),
                ipv4_dns2=ipv4public.get('dns2'),
                ipv4anch_addr=ipv4anchor.get('address'),
                ipv4anch_mask=ipv4anchor.get('prefix'),
                ipv6_addr=ipv6public.get('address'),
                ipv6_mask=ipv6public.get('prefix'),
                ipv6_gw=ipv6public.get('gateway'),
                ipv6_dns1=ipv6public.get('dns1'),
                ipv6_dns2=ipv6public.get('dns2'),
            )
        if cloud == 'private':
            f_eth0 = eth0_rnch_private.data.format(
                ipv4_addr=ipv4public.get('address'),
                ipv4_mask=ipv4public.get('prefix'),
                ipv4_gw=ipv4public.get('gateway'),
                ipv4_dns1=ipv4public.get('dns1'),
                ipv4_dns2=ipv4public.get('dns2')
            )
        return f_eth0

    @method_logger()
    def rnch_eth1_data(self, ipv4private):
        f_eth1 = eth1_rnch.data.format(
            ipv4_addr=ipv4private.get('address'),
            ipv4_mask=ipv4private.get('prefix')
        )
        return f_eth1

    @method_logger()
    def public_nic_setup(self, ipv4public, ipv4anchor, ipv6public):
        if self.get_distro() == 'deb' or self.get_distro() == 'alpn':
            nic_f_path = self.nic_file_path()
            network_file_data = self.deb_eth0_data(ipv4public, ipv4anchor, ipv6public=ipv6public)
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(644, nic_f_path)
        if self.get_distro() == 'rhl' or self.get_distro() == 'atom':
            nic_f_path = self.nic_file_path()
            network_file_data = self.rhl_eth0_data(ipv4public, ipv4anchor, ipv6public=ipv6public)
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(644, nic_f_path)
        if self.get_distro() == 'win':
            nic_f_path = self.nic_file_path()
            network_file_data = self.win_eth0_data(ipv4public, ipv4anchor, ipv6public=ipv6public)
            self.gfs.write(nic_f_path, network_file_data)
        if self.get_distro() == 'core':
            nic_f_path = self.nic_file_path()
            network_file_data = self.core_eth0_data(ipv4public, ipv4anchor, ipv6public=ipv6public)
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(644, nic_f_path)
        if self.get_distro() == 'rnch':
            nic_f_path = self.nic_file_path()
            network_file_data = self.rnch_eth0_data(ipv4public, ipv4anchor, ipv6public=ipv6public)
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(644, nic_f_path)

    @method_logger()
    def private_nic_setup(self, ipv4private):
        if self.get_distro() == 'deb' or self.get_distro() == 'alpn':
            nic_f_path = self.nic_file_path()
            pub_nic_data = self.gfs.cat(nic_f_path)
            priv_nic_data = self.deb_eth1_data(ipv4private)
            network_file_data = pub_nic_data + priv_nic_data
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(644, nic_f_path)
        if self.get_distro() == 'rhl' or self.get_distro() == 'atom':
            nic_f_path = self.nic_file_path(nic_type='private')
            network_file_data = self.rhl_eth1_data(ipv4private)
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(644, nic_f_path)
        if self.get_distro() == 'win':
            nic_f_path = self.nic_file_path()
            pub_nic_data = self.gfs.cat(nic_f_path)
            priv_nic_data = self.win_eth1_data(ipv4private)
            network_file_data = pub_nic_data + priv_nic_data
            self.gfs.write(nic_f_path, network_file_data)
        if self.get_distro() == 'core':
            nic_f_path = self.nic_file_path()
            pub_nic_data = self.gfs.cat(nic_f_path)
            priv_nic_data = self.core_eth1_data(ipv4private)
            network_file_data = pub_nic_data + priv_nic_data
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(644, nic_f_path)
        if self.get_distro() == 'rnch':
            nic_f_path = self.nic_file_path()
            pub_nic_data = self.gfs.cat(nic_f_path)
            priv_nic_data = self.rnch_eth1_data(ipv4private)
            network_file_data = pub_nic_data + priv_nic_data
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(644, nic_f_path)

    @method_logger()
    def vpc_gw_nic_setup(self, ipv4vpc):
        if self.get_distro() == 'deb' or self.get_distro() == 'alpn':
            nic_f_path = self.nic_file_path()
            pub_nic_data = self.gfs.cat(nic_f_path)
            vpc_nic_data = self.deb_eth2_data(ipv4vpc)
            network_file_data = pub_nic_data + vpc_nic_data
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(644, nic_f_path)

    @method_logger()
    def vpc_nic_setup(self, ipv4vpc):
        if self.get_distro() == 'deb':
            nic_f_path = self.nic_file_path()
            network_file_data = self.deb_eth0_data(ipv4vpc, cloud='private')
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(644, nic_f_path)
        if self.get_distro() == 'rhl' or self.get_distro() == 'atom':
            nic_f_path = self.nic_file_path()
            network_file_data = self.rhl_eth0_data(ipv4vpc, cloud='private')
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(644, nic_f_path)
        if self.get_distro() == 'win':
            nic_f_path = self.nic_file_path()
            network_file_data = self.win_eth0_data(ipv4vpc, cloud='private')
            self.gfs.write(nic_f_path, network_file_data)
        if self.get_distro() == 'core':
            nic_f_path = self.nic_file_path()
            network_file_data = self.core_eth0_data(ipv4vpc, cloud='private')
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(644, nic_f_path)
        if self.get_distro() == 'rnch':
            nic_f_path = self.nic_file_path()
            network_file_data = self.rnch_eth0_data(ipv4vpc, cloud='private')
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(644, nic_f_path)

    @method_logger()
    def private_cloud_nic_setup(self, ipv4public):
        if self.get_distro() == 'deb':
            nic_f_path = self.nic_file_path()
            network_file_data = self.deb_eth0_data(ipv4public, cloud='private')
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(644, nic_f_path)
        if self.get_distro() == 'rhl' or self.get_distro() == 'atom':
            nic_f_path = self.nic_file_path()
            network_file_data = self.rhl_eth0_data(ipv4public, cloud='private')
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(644, nic_f_path)
        if self.get_distro() == 'win':
            nic_f_path = self.nic_file_path()
            network_file_data = self.win_eth0_data(ipv4public, cloud='private')
            self.gfs.write(nic_f_path, network_file_data)
        if self.get_distro() == 'core':
            nic_f_path = self.nic_file_path()
            network_file_data = self.core_eth0_data(ipv4public, cloud='private')
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(644, nic_f_path)
        if self.get_distro() == 'rnch':
            nic_f_path = self.nic_file_path()
            network_file_data = self.rnch_eth0_data(ipv4public, cloud='private')
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(644, nic_f_path)

    @method_logger()
    def setup_networking(self, networks, cloud='public'):
        ipv4vpc = networks.get('ipv4_vpc')
        ipv4public = networks.get('ipv4_public')
        ipv6public = networks.get('ipv6_public')
        ipv4anchor = networks.get('ipv4_anchor')
        ipv4private = networks.get('ipv4_private')

        if cloud == 'public':
            self.public_nic_setup(ipv4public, ipv4anchor=ipv4anchor, ipv6public=ipv6public)
            if ipv4private:
                self.private_nic_setup(ipv4private)
            # Only for VPC gateway
            if ipv4vpc:
                self.vpc_gw_nic_setup(ipv4vpc)

        if cloud == 'private':
            self.vpc_nic_setup(ipv4vpc)

    @method_logger()
    def change_ipv4anch(self, ipv4anchor):
        if self.get_distro() == 'deb' or self.get_distro() == 'alpn':
            nic_f_path = self.nic_file_path()
            nic_file = self.gfs.cat(nic_f_path)
            new_line_nic_file = 'address ' % ipv4anchor.get('address')
            network_file_data = re.sub('^address 10\.255\..*?', new_line_nic_file, nic_file)
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(644, nic_f_path)
        if self.get_distro() == 'rhl':
            nic_f_path = self.nic_file_path()
            nic_file = self.gfs.cat(nic_f_path)
            new_line_nic_file = '^IPADDR2=%s' % ipv4anchor.get('address')
            network_file_data = re.sub('^IPADDR2=.*?', new_line_nic_file, nic_file)
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(644, nic_f_path)
        if self.get_distro() == 'core':
            nic_f_path = self.coreos_config_path()
            nic_file = self.gfs.cat(nic_f_path)
            new_line_nic_file = 'Address=%s/%s' % (ipv4anchor.get('address'), ipv4anchor.get('prefix'))
            network_file_data = re.sub('^Address=10\.255\..*?', new_line_nic_file, nic_file)
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(644, nic_f_path)
        if self.get_distro() == 'rnch':
            nic_f_path = self.rancheros_config_path()
            nic_file = self.gfs.cat(nic_f_path)
            new_line_nic_file = 'address: %s/%s' % (ipv4anchor.get('address'), ipv4anchor.get('prefix'))
            network_file_data = re.sub('^address: 10\.255\..*?', new_line_nic_file, nic_file)
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(644, nic_f_path)

    @method_logger()
    def change_root_passwd(self, password_hash, shadow_file):
        shadow_file_updated = ''
        if self.get_distro() == 'win':
            pass
        elif self.get_distro() == 'core':
            new_pass_line = '- passwd: "%s"' % password_hash
            shadow_file_updated = re.sub('^- passwd:.*?', new_pass_line, shadow_file)
        elif self.get_distro() == 'rnch':
            new_pass_line = '- sed -i "s/^rancher:\*:/rancher:%s:/g" /etc/shadow' % password_hash
            shadow_file_updated = re.sub('^- sed -i "s/^rancher:.*?', new_pass_line, shadow_file)
        else:
            root_shadow_line = 'root:%s:' % password_hash
            shadow_file_updated = re.sub('^root:.*?:', root_shadow_line, shadow_file)
        return shadow_file_updated

    @method_logger()
    def reset_root_passwd(self, pass_hash):
        if self.get_distro() == 'win':
            nic_f_path = self.nic_file_path()
            f_data = self.gfs.cat(nic_f_path)
            str_pswd = 'net user Administrator %s\r\n' % pass_hash
            f_data += str_pswd
            self.gfs.write(nic_f_path, f_data)
        elif self.get_distro() == 'core':
            config_fl_path = self.coreos_config_path()
            config_data = self.gfs.cat(config_fl_path)
            if 'passwd' in config_data:
                config_data_updated = self.change_root_passwd(pass_hash, config_data)
            else:
                account_data = '\nusers:\n  - name: "core"\n  - passwd: "%s"\n' % pass_hash
                config_data_updated = config_data + account_data
            self.gfs.write(config_fl_path, config_data_updated)
            self.gfs.chmod(644, config_fl_path)
        elif self.get_distro() == 'rnch':
            config_fl_path = self.rancheros_config_path()
            config_data = self.gfs.cat(config_fl_path)
            if 'rancher:\*:' in config_data:
                config_data_updated = self.change_root_passwd(pass_hash, config_data)
            else:
                account_data = '\nruncmd:\n- sed -i "s/^rancher:\*:/rancher:%s:/g" /etc/shadow\n' % pass_hash
                config_data_updated = config_data + account_data
            self.gfs.write(config_fl_path, config_data_updated)
            self.gfs.chmod(644, config_fl_path)
        else:
            shadow_fl_path = self.shadow_file_path()
            file_shadow = self.gfs.cat(shadow_fl_path)
            shadow_file_updated = self.change_root_passwd(pass_hash, file_shadow)
            self.gfs.write(shadow_fl_path, shadow_file_updated)
            self.gfs.chmod(640, shadow_fl_path)

    @method_logger()
    def set_pubic_keys(self, public_key):
        if public_key:
            if self.get_distro() == 'win':
                pass
            elif self.get_distro() == 'core':
                f_path = self.coreos_config_path()
                f_data = self.gfs.cat(f_path)
                key_data = '\n\nssh_authorized_keys:\n  - "%s"\n' % public_key
                config_data = f_data + key_data
                self.gfs.write(f_path, config_data)
                self.gfs.chmod(640, f_path)
            elif self.get_distro() == 'rnch':
                f_path = self.rancheros_config_path()
                f_data = self.gfs.cat(f_path)
                key_data = '\nssh_authorized_keys:\n- "%s"\n' % public_key
                config_data = f_data + key_data
                self.gfs.write(f_path, config_data)
                self.gfs.chmod(640, f_path)
            else:
                root_ssh_folder_path = self.root_ssh_dir_path()
                root_fl_auth_key_path = self.root_auth_keys_path()
                if not self.gfs.is_dir(root_ssh_folder_path):
                    self.gfs.mkdir(root_ssh_folder_path)
                    self.gfs.chmod(700, root_ssh_folder_path)
                self.gfs.write(root_fl_auth_key_path, public_key)
                self.gfs.chmod(600, root_fl_auth_key_path)

    @method_logger()
    def set_hostname(self, hostname):
        if self.get_distro() == 'alpn':
            f_path = self.hostname_file_path()
            self.gfs.write(f_path, hostname)
        elif self.get_distro() == 'core':
            f_path = self.coreos_config_path()
            f_data = self.gfs.cat(f_path)
            key_data = '\nhostname: "%s"\n' % hostname
            config_data = f_data + key_data
            self.gfs.write(f_path, config_data)
            self.gfs.chmod(640, f_path)
        elif self.get_distro() == 'rnch':
            f_path = self.rancheros_config_path()
            f_data = self.gfs.cat(f_path)
            key_data = '\nhostname: "%s"\n' % hostname
            config_data = f_data + key_data
            self.gfs.write(f_path, config_data)
            self.gfs.chmod(640, f_path)
        elif self.get_distro() == 'win':
            nic_f_path = self.nic_file_path()
            f_data = self.gfs.cat(nic_f_path)
            h_data = 'wmic computersystem where name="%s" call rename name="%s"\r\n' % ('%COMPUTERNAME%', hostname)
            f_data += h_data
            self.gfs.write(nic_f_path, f_data)

    @method_logger()
    def clean_cloud_init(self):
        if self.get_distro() == 'win':
            pass
        elif self.get_distro() == 'core':
            pass
        elif self.get_distro() == 'rnch':
            pass
        else:
            path = self.cloud_init_path()
            self.gfs.rm_rf(path)

    @method_logger()
    def resize_win_fs(self):
        nic_f_path = self.nic_file_path()
        f_data = self.gfs.cat(nic_f_path)
        d_data = self._win_str_disk_extend()
        f_data += d_data
        self.gfs.write(nic_f_path, f_data)

    @method_logger()
    def resize_linux_fs(self, device=None):
        if not device:
            device = self.root_device()
        self.gfs.resize2fs(device)

    @method_logger()
    def resize_fs(self):
        if self.get_distro() == 'win':
            if not self.gfs.mounts():
                self.mount_root()
            self.resize_win_fs()

    @method_logger()
    def mount_root(self):
        device = self.root_device()
        if self.get_distro() == 'win':
            try:
                self.gfs.mount(device, '/')
            except RuntimeError:
                self.gfs.ntfsfix(device)
                self.gfs.mount(device, '/')
        else:
            self.gfs.mount(device, '/')

    @method_logger()
    def umount_root(self):
        device = self.root_device()
        if self.get_distro() == 'core':
            device = '/dev/sda6'
        self.gfs.umount(device)

    @method_logger()
    def clearfix(self, firstboot=True):
        if self.get_distro() == 'rhl':
            if firstboot:
                if not self.gfs.mounts():
                    self.mount_root()
                self.gfs.touch('/.autorelabel')
        if self.get_distro() == 'win':
            if not self.gfs.mounts():
                self.mount_root()
            nic_f_path = self.nic_file_path()
            f_data = self.gfs.cat(nic_f_path)
            if firstboot:
                f_data += self._win_str_shutdown()
            f_data += self._win_clean_cloudinit()
            self.gfs.write(nic_f_path, f_data)

    @method_logger()
    def close(self):
        self.gfs.shutdown()
        self.gfs.close()
