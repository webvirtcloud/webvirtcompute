#
# util - HubGridCloud utils for managing VM's filesystem
# UUID regexp - '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
#

import re
import guestfs
from jinja2 import Template
from ipaddress import IPv4Interface

from templates import eth1_rnch
from templates import eth0_rnch_public
from templates import eth0_rnch_private

from templates import eth1_win
from templates import eth0_win_public
from templates import eth0_win_private

from templates import eth1_rhl
from templates import eth0_rhl_public
from templates import eth0_rhl_private

from templates import eth1_deb
from templates import eth2_deb
from templates import eth0_deb_public
from templates import eth0_deb_private


class GuestFSUtil(object):
    def __init__(self, drive, distro):
        self.drive = drive
        self.distro = distro
        self.gfs = guestfs.GuestFS(python_return_dict=True)
        self.gfs.add_drive(drive)
        self.gfs.launch()

    def inspect_distro(self):
        distro = None
        roots = self.gfs.inspect_os()
        for root in roots:
            distro = self.gfs.inspect_get_distro(root)
        if distro == "unknown":
            distro = None
        return distro

    def get_distro(self):
        if "fedora" in self.distro:
            return "rhl"
        if "centos" in self.distro:
            return "rhl"
        if "ubuntu" in self.distro:
            return "deb"
        if "debian" in self.distro:
            return "deb"
        if "windows" in self.distro:
            return "win"
        if "rancheros" in self.distro:
            return "rnch"
        if "alpine" in self.distro:
            return "alpn"

    def root_device(self):
        device = "/dev/sda1"
        if self.get_distro() == "alpn":
            device = "/dev/sda3"
        return device

    def rancheros_config_path(self):
        return "/var/lib/rancher/conf/cloud-config.yml"

    def cloud_init_path(self):
        return "/var/lib/cloud"

    def shadow_file_path(self):
        return "/etc/shadow"

    def hostname_file_path(self):
        return "/etc/hostname"

    def root_ssh_dir_path(self):
        return "/root/.ssh"

    def root_auth_keys_path(self):
        return "/root/.ssh/authorized_keys"

    def _win_str_disk_extend(self):
        return "diskpart /s %~dp0\\diskpart.txt\r\n"

    def _win_str_shutdown(self):
        return "shutdown /r /t 1\r\n"

    def _win_clean_cloudinit(self):
        return "type NUL > %~dp0\\cloudinit.cmd\r\n"

    def nic_file_path(self, nic_type="public"):
        f_path = ""
        if self.get_distro() == "deb" or self.get_distro() == "alpn":
            f_path = "/etc/network/interfaces"
        if self.get_distro() == "rhl":
            if nic_type == "public":
                f_path = "/etc/sysconfig/network-scripts/ifcfg-eth0"
            if nic_type == "private":
                f_path = "/etc/sysconfig/network-scripts/ifcfg-eth1"
        if self.get_distro() == "win":
            f_path = "/Windows/System32/GroupPolicy/Machine/Scripts/Startup/cloudinit.cmd"
        if self.get_distro() == "rnch":
            f_path = self.rancheros_config_path()
        return f_path

    def deb_eth0_data(self, ipv4public, ipv4compute, ipv6public=None, cloud="public"):
        data = ""
        if cloud == "public":
            template = Template(eth0_deb_public.data)
            data = template.render(
                ipv4public=ipv4public,
                ipv4compute=ipv4compute,
                ipv6public=ipv6public
            )
        if cloud == "private":
            template = Template(eth0_deb_private.data)
            data = template.render(
                ipv4public=ipv4public
            )
        return data

    def deb_eth1_data(self, ipv4private):
        template = Template(eth1_deb.data)
        data = template.render(
            ipv4private=ipv4private
        )
        return data

    def deb_eth2_data(self, ipv4private):
        template = Template(eth2_deb.data)
        data = template.render(
            ipv4private=ipv4private
        )
        return data

    def rhl_eth0_data(self, ipv4public, ipv4compute, ipv6public=None, cloud="public"):
        ipv4_public_iface = IPv4Interface(f"{ipv4compute.get('address')}/{ipv4compute.get('netmaks')}")
        ipv4_compute_iface = IPv4Interface(f"{ipv4compute.get('address')}/{ipv4compute.get('netmaks')}")
        ipv4public.update({"prefix": ipv4_public_iface.network.prefixlen})
        ipv4compute.update({"prefix": ipv4_compute_iface.network.prefixlen})
        if cloud == "public":
            template = Template(eth0_rhl_public.data)
            data = template.render(
                ipv4public=ipv4public,
                ipv4compute=ipv4compute,
                ipv6public=ipv6public
            )
        if cloud == "private":
            template = Template(eth0_rhl_private.data)
            data = template.render(
                ipv4public=ipv4public
            )
        return date

    def rhl_eth1_data(self, ipv4private):
        template = Template(eth1_rhl.data)
        data = template.render(
            ipv4private=ipv4private
        )
        return data

    def win_eth0_data(self, ipv4public, ipv4compute, ipv6public=None, cloud="public"):
        ipv4_public_iface = IPv4Interface(f"{ipv4compute.get('address')}/{ipv4compute.get('netmaks')}")
        ipv4_compute_iface = IPv4Interface(f"{ipv4compute.get('address')}/{ipv4compute.get('netmaks')}")
        ipv4public.update({"prefix": ipv4_public_iface.network.prefixlen})
        ipv4compute.update({"prefix": ipv4_compute_iface.network.prefixlen})
        if cloud == "public":
            template = Template(eth0_win_public.data)
            data = template.render(
                ipv4public=ipv4public,
                ipv4compute=ipv4compute,
                ipv6public=ipv6public
            )
        if cloud == "private":
            template = Template(eth0_win_private.data)
            data = template.render(
                ipv4public=ipv4public
            )
        return data

    def win_eth1_data(self, ipv4private):
        template = Template(eth1_win.data)
        data = template.render(
            ipv4private=ipv4private
        )
        return data

    def rnch_eth0_data(self, ipv4public, ipv4compute, ipv6public=None, cloud="public"):
        ipv4_public_iface = IPv4Interface(f"{ipv4compute.get('address')}/{ipv4compute.get('netmaks')}")
        ipv4_compute_iface = IPv4Interface(f"{ipv4compute.get('address')}/{ipv4compute.get('netmaks')}")
        ipv4public.update({"prefix": ipv4_public_iface.network.prefixlen})
        ipv4compute.update({"prefix": ipv4_compute_iface.network.prefixlen})        
        if cloud == "public":
            template = Template(eth0_rnch_public.data)
            data = template.render(
                ipv4public=ipv4public,
                ipv4compute=ipv4compute,
                ipv6public=ipv6public
            )
        if cloud == "private":
            template = Template(eth0_rnch_private.data)
            data = template.render(
                ipv4public=ipv4public
            )
        return data

    def rnch_eth1_data(self, ipv4private):
        ipv4_private_iface = IPv4Interface(f"{ipv4private.get('address')}/{ipv4private.get('netmaks')}")
        ipv4private.update({"prefix": ipv4_private_iface.network.prefixlen})
        template = Template(eth1_rnch.data)
        data = template.render(
            ipv4private=ipv4private
        )
        return data

    def public_nic_setup(self, ipv4public, ipv4compute, ipv6public):
        if self.get_distro() == "deb" or self.get_distro() == "alpn":
            nic_f_path = self.nic_file_path()
            network_file_data = self.deb_eth0_data(ipv4public, ipv4compute, ipv6public=ipv6public)
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(int('0644', 8), nic_f_path)
        if self.get_distro() == "rhl":
            nic_f_path = self.nic_file_path()
            network_file_data = self.rhl_eth0_data(ipv4public, ipv4compute, ipv6public=ipv6public)
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(int('0644', 8), nic_f_path)
        if self.get_distro() == "win":
            nic_f_path = self.nic_file_path()
            network_file_data = self.win_eth0_data(ipv4public, ipv4compute, ipv6public=ipv6public)
            self.gfs.write(nic_f_path, network_file_data)
        if self.get_distro() == "rnch":
            nic_f_path = self.nic_file_path()
            network_file_data = self.rnch_eth0_data(ipv4public, ipv4compute, ipv6public=ipv6public)
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(int('0644', 8), nic_f_path)

    def private_nic_setup(self, ipv4private):
        if self.get_distro() == "deb" or self.get_distro() == "alpn":
            nic_f_path = self.nic_file_path()
            pub_nic_data = self.gfs.cat(nic_f_path)
            priv_nic_data = self.deb_eth1_data(ipv4private)
            network_file_data = pub_nic_data + priv_nic_data
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(int('0644', 8), nic_f_path)
        if self.get_distro() == "rhl":
            nic_f_path = self.nic_file_path(nic_type="private")
            network_file_data = self.rhl_eth1_data(ipv4private)
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(int('0644', 8), nic_f_path)
        if self.get_distro() == "win":
            nic_f_path = self.nic_file_path()
            pub_nic_data = self.gfs.cat(nic_f_path)
            priv_nic_data = self.win_eth1_data(ipv4private)
            network_file_data = pub_nic_data + priv_nic_data
            self.gfs.write(nic_f_path, network_file_data)
        if self.get_distro() == "rnch":
            nic_f_path = self.nic_file_path()
            pub_nic_data = self.gfs.cat(nic_f_path)
            priv_nic_data = self.rnch_eth1_data(ipv4private)
            network_file_data = pub_nic_data + priv_nic_data
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(int('0644', 8), nic_f_path)

    def vpc_gw_nic_setup(self, ipv4vpc):
        if self.get_distro() == "deb" or self.get_distro() == "alpn":
            nic_f_path = self.nic_file_path()
            pub_nic_data = self.gfs.cat(nic_f_path)
            vpc_nic_data = self.deb_eth2_data(ipv4vpc)
            network_file_data = pub_nic_data + vpc_nic_data
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(int('0644', 8), nic_f_path)

    def vpc_nic_setup(self, ipv4vpc):
        if self.get_distro() == "deb":
            nic_f_path = self.nic_file_path()
            network_file_data = self.deb_eth0_data(ipv4vpc, cloud="private")
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(int('0644', 8), nic_f_path)
        if self.get_distro() == "rhl":
            nic_f_path = self.nic_file_path()
            network_file_data = self.rhl_eth0_data(ipv4vpc, cloud="private")
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(int('0644', 8), nic_f_path)
        if self.get_distro() == "win":
            nic_f_path = self.nic_file_path()
            network_file_data = self.win_eth0_data(ipv4vpc, cloud="private")
            self.gfs.write(nic_f_path, network_file_data)
        if self.get_distro() == "rnch":
            nic_f_path = self.nic_file_path()
            network_file_data = self.rnch_eth0_data(ipv4vpc, cloud="private")
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(int('0644', 8), nic_f_path)

    def private_cloud_nic_setup(self, ipv4public):
        if self.get_distro() == "deb":
            nic_f_path = self.nic_file_path()
            network_file_data = self.deb_eth0_data(ipv4public, cloud="private")
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(int('0644', 8), nic_f_path)
        if self.get_distro() == "rhl":
            nic_f_path = self.nic_file_path()
            network_file_data = self.rhl_eth0_data(ipv4public, cloud="private")
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(int('0644', 8), nic_f_path)
        if self.get_distro() == "win":
            nic_f_path = self.nic_file_path()
            network_file_data = self.win_eth0_data(ipv4public, cloud="private")
            self.gfs.write(nic_f_path, network_file_data)
        if self.get_distro() == "rnch":
            nic_f_path = self.nic_file_path()
            network_file_data = self.rnch_eth0_data(ipv4public, cloud="private")
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(int('0644', 8), nic_f_path)

    def setup_networking(self, networks, cloud="public"):
        ipv4vpc = networks.get("v4", {}).get("vpc", {}).get("primary")
        ipv4public = networks.get("v4", {}).get("public", {}).get("primary")
        ipv4compute = networks.get("v4", {}).get("public", {}).get("secondary")
        ipv4private = networks.get("v4", {}).get("private", {}).get("primary")
        ipv6public = networks.get("v6", {}).get("public", {}).get("primary")

        if cloud == "public":
            self.public_nic_setup(ipv4public, ipv4compute, ipv6public=ipv6public)
            if ipv4private:
                self.private_nic_setup(ipv4private)
            # Only for VPC gateway
            if ipv4vpc:
                self.vpc_gw_nic_setup(ipv4vpc)

        if cloud == "private":
            self.ipv4_vpc(ipv4vpc)

    def change_ipv4fixed(self, ipv4compute):
        if self.get_distro() == "deb" or self.get_distro() == "alpn":
            nic_f_path = self.nic_file_path()
            nic_file = self.gfs.cat(nic_f_path)
            new_line_nic_file = f"address {ipv4compute.get('address')}"
            network_file_data = re.sub("^address 10\.255\..*?", new_line_nic_file, nic_file)
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(int('0644', 8), nic_f_path)
        if self.get_distro() == "rhl":
            nic_f_path = self.nic_file_path()
            nic_file = self.gfs.cat(nic_f_path)
            new_line_nic_file = f"^IPADDR2={ipv4compute.get('address')}"
            network_file_data = re.sub("^IPADDR2=.*?", new_line_nic_file, nic_file)
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(int('0644', 8), nic_f_path)
        if self.get_distro() == "rnch":
            nic_f_path = self.rancheros_config_path()
            nic_file = self.gfs.cat(nic_f_path)
            new_line_nic_file = f"address: {ipv4compute.get('address')}/{ipv4compute.get('prefix')}"
            network_file_data = re.sub("^address: 10\.255\..*?", new_line_nic_file, nic_file)
            self.gfs.write(nic_f_path, network_file_data)
            self.gfs.chmod(int('0644', 8), nic_f_path)

    def change_root_passwd(self, password_hash, shadow_file):
        shadow_file_updated = ""
        if self.get_distro() == "win":
            pass
        elif self.get_distro() == "rnch":
            new_pass_line = f'- sed -i "s/^rancher:\*:/rancher:{password_hash}:/g" /etc/shadow'
            shadow_file_updated = re.sub('^- sed -i "s/^rancher:.*?', new_pass_line, shadow_file)
        else:
            root_shadow_line = f"root:{password_hash}:"
            shadow_file_updated = re.sub("^root:.*?:", root_shadow_line, shadow_file)
        return shadow_file_updated

    def reset_root_passwd(self, pass_hash):
        if self.get_distro() == "win":
            nic_f_path = self.nic_file_path()
            f_data = self.gfs.cat(nic_f_path)
            str_pswd = f"net user Administrator {pass_hash}\r\n"
            f_data += str_pswd
            self.gfs.write(nic_f_path, f_data)
        elif self.get_distro() == "rnch":
            config_fl_path = self.rancheros_config_path()
            config_data = self.gfs.cat(config_fl_path)
            if "rancher:\*:" in config_data:
                config_data_updated = self.change_root_passwd(pass_hash, config_data)
            else:
                account_data = f'\nruncmd:\n- sed -i "s/^rancher:\*:/rancher:{pass_hash}:/g" /etc/shadow\n'
                config_data_updated = config_data + account_data
            self.gfs.write(config_fl_path, config_data_updated)
            self.gfs.chmod(int('0644', 8), config_fl_path)
        else:
            shadow_fl_path = self.shadow_file_path()
            file_shadow = self.gfs.cat(shadow_fl_path)
            shadow_file_updated = self.change_root_passwd(pass_hash, file_shadow)
            self.gfs.write(shadow_fl_path, shadow_file_updated)
            self.gfs.chmod(int('0640', 8), shadow_fl_path)

    def set_pubic_keys(self, keys_string):
        if public_key:
            if self.get_distro() == "win":
                pass
            elif self.get_distro() == "rnch":
                f_path = self.rancheros_config_path()
                f_data = self.gfs.cat(f_path)
                key_data = f'\nssh_authorized_keys:\n- "{keys_string}"\n'
                config_data = f_data + key_data
                self.gfs.write(f_path, config_data)
                self.gfs.chmod(int('0640', 8), f_path)
            else:
                root_ssh_folder_path = self.root_ssh_dir_path()
                root_fl_auth_key_path = self.root_auth_keys_path()
                if not self.gfs.is_dir(root_ssh_folder_path):
                    self.gfs.mkdir(root_ssh_folder_path)
                    self.gfs.chmod(int('0700', 8), root_ssh_folder_path)
                self.gfs.write(root_fl_auth_key_path, keys_string)
                self.gfs.chmod(int('0600', 8), root_fl_auth_key_path)

    def set_hostname(self, hostname):
        if self.get_distro() == "alpn":
            f_path = self.hostname_file_path()
            self.gfs.write(f_path, hostname)
        elif self.get_distro() == "rnch":
            f_path = self.rancheros_config_path()
            f_data = self.gfs.cat(f_path)
            key_data = f'\nhostname: "{hostname}"\n'
            config_data = f_data + key_data
            self.gfs.write(f_path, config_data)
            self.gfs.chmod(int('0640', 8), f_path)
        elif self.get_distro() == "win":
            nic_f_path = self.nic_file_path()
            f_data = self.gfs.cat(nic_f_path)
            h_data = 'wmic computersystem where name="{' % COMPUTERNAME % '}" call rename name="%s"\r\n' % hostname
            f_data += h_data
            self.gfs.write(nic_f_path, f_data)

    def clean_cloud_init(self):
        if self.get_distro() == "win":
            pass
        elif self.get_distro() == "rnch":
            pass
        else:
            path = self.cloud_init_path()
            self.gfs.rm_rf(path)

    def resize_win_fs(self):
        nic_f_path = self.nic_file_path()
        f_data = self.gfs.cat(nic_f_path)
        d_data = self._win_str_disk_extend()
        f_data += d_data
        self.gfs.write(nic_f_path, f_data)

    def resize_linux_fs(self, device=None):
        if not device:
            device = self.root_device()
        self.gfs.resize2fs(device)

    def resize_fs(self):
        if self.get_distro() == "win":
            if not self.gfs.mounts():
                self.mount_root()
            self.resize_win_fs()

    def mount_root(self):
        device = self.root_device()
        if self.get_distro() == "win":
            try:
                self.gfs.mount(device, "/")
            except RuntimeError:
                self.gfs.ntfsfix(device)
                self.gfs.mount(device, "/")
        else:
            self.gfs.mount(device, "/")

    def umount_root(self):
        device = self.root_device()
        self.gfs.umount(device)

    def clearfix(self, firstboot=True):
        if self.get_distro() == "rhl":
            if firstboot:
                if not self.gfs.mounts():
                    self.mount_root()
                self.gfs.touch("/.autorelabel")
        if self.get_distro() == "win":
            if not self.gfs.mounts():
                self.mount_root()
            nic_f_path = self.nic_file_path()
            f_data = self.gfs.cat(nic_f_path)
            if firstboot:
                f_data += self._win_str_shutdown()
            f_data += self._win_clean_cloudinit()
            self.gfs.write(nic_f_path, f_data)

    def close(self):
        self.gfs.shutdown()
        self.gfs.close()
