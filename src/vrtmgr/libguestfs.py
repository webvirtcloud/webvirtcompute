import logging
import re
from ipaddress import IPv4Interface

import guestfs
from jinja2 import Template

from templates import (
    eth0_deb_private,
    eth0_deb_public,
    eth0_fed_private,
    eth0_fed_public,
    eth0_rhl_private,
    eth0_rhl_public,
    eth0_win_private,
    eth0_win_public,
    eth0_ubt_private,
    eth0_ubt_public,
    eth1_deb,
    eth1_fed,
    eth1_rhl,
    eth1_win,
    eth1_ubt,
    eth2_deb,
)

from .exceptions import GuestFSError

# Setup logging
logger = logging.getLogger(__name__)


class GuestFSUtil(object):
    """
    A utility class for interacting with virtual machine disk images using libguestfs.
    Provides methods for inspecting and configuring VMs based on their OS family.
    """

    def __init__(self, drive):
        """
        Initialize GuestFSUtil with a drive path.

        Args:
            drive (str): Path to the VM disk image file
        """
        self.drive = drive
        self.os_family = None
        try:
            self.gfs = guestfs.GuestFS(python_return_dict=True)
            self.gfs.add_drive(drive)
            self.gfs.launch()
        except Exception as e:
            logger.error(f"Failed to initialize libguestfs for {drive}: {str(e)}")
            raise

    def _update_ip_prefix(self, ip_dict):
        """
        Helper method to calculate network prefix length from IP and netmask
        and update the dictionary with the prefix value.

        Args:
            ip_dict (dict): Dictionary containing 'address' and 'netmask' keys

        Returns:
            dict: The updated dictionary with 'prefix' key
        """
        if ip_dict and ip_dict.get("address") and ip_dict.get("netmask"):
            ip_iface = IPv4Interface(
                f"{ip_dict.get('address')}/{ip_dict.get('netmask')}"
            )
            ip_dict.update({"prefix": ip_iface.network.prefixlen})
        return ip_dict

    def _update_network_prefixes(
        self, ipv4public=None, ipv4compute=None, ipv4private=None
    ):
        """
        Helper method to calculate and update network prefix lengths for multiple IP dictionaries.

        Args:
            ipv4public (dict): Public IP information
            ipv4compute (dict): Compute IP information
            ipv4private (dict): Private IP information

        Returns:
            tuple: Updated dictionaries
        """
        if ipv4public:
            ipv4public = self._update_ip_prefix(ipv4public)
        if ipv4compute:
            ipv4compute = self._update_ip_prefix(ipv4compute)
        if ipv4private:
            ipv4private = self._update_ip_prefix(ipv4private)
        return ipv4public, ipv4compute, ipv4private

    def inspect_distro(self):
        """
        Inspect the OS distribution on the drive.

        Returns:
            str: Distribution name or None if not determined
        """
        distro = None
        try:
            roots = self.gfs.inspect_os()
            if roots:
                for root in roots:
                    distro = self.gfs.inspect_get_distro(root)
                    if distro and distro != "unknown":
                        break
        except Exception as e:
            logger.warning(f"Error inspecting OS distribution: {str(e)}")

        return None if distro == "unknown" else distro

    def get_distro(self):
        """
        Get the OS family/distribution type.

        Returns:
            str: OS family code (rhl, fed, deb, win, etc.) or "unknown"
        """
        distro = self.inspect_distro()

        if "redhat-based" in distro or "centos" in distro:
            return "rhl"
        if "fedora" in distro:
            return "fed"
        if "debian" in distro or "ubuntu" in distro:
            return "deb"
        if "alpine" in distro:
            return "alp"
        if "windows" in distro:
            return "win"

        return "unknown"

    def root_device(self):
        """
        Determine the root device path based on OS family.
        Also sets the os_family attribute if not already set.

        Returns:
            str: Path to the root device
        """
        if self.os_family is None:
            self.os_family = self.get_distro()

        device = "/dev/sda1"
        if self.os_family == "alp":
            self.os_family = "deb"  # Treat Alpine like Debian for setup networking
            device = "/dev/sda2"
        return device

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
        if self.os_family == "deb":
            f_path = "/etc/network/interfaces"
        if self.os_family == "ubt":
            f_path = "/etc/netplan/01-netcfg.yaml"
        if self.os_family == "rhl":
            if nic_type == "public":
                f_path = "/etc/sysconfig/network-scripts/ifcfg-eth0"
            if nic_type == "private":
                f_path = "/etc/sysconfig/network-scripts/ifcfg-eth1"
        if self.os_family == "fed":
            if nic_type == "public":
                f_path = "/etc/NetworkManager/system-connections/eth0.nmconnection"
            if nic_type == "private":
                f_path = "/etc/NetworkManager/system-connections/eth1.nmconnection"
        if self.os_family == "win":
            f_path = (
                "/Windows/System32/GroupPolicy/Machine/Scripts/Startup/cloudinit.cmd"
            )
        return f_path

    def deb_eth0_data(self, ipv4public, ipv4compute, ipv6public=None, cloud="public"):
        ipv4public, ipv4compute, _ = self._update_network_prefixes(
            ipv4public, ipv4compute
        )
        if cloud == "public":
            template = Template(eth0_deb_public.data)
            data = template.render(
                ipv4public=ipv4public, ipv4compute=ipv4compute, ipv6public=ipv6public
            )
        if cloud == "private":
            template = Template(eth0_deb_private.data)
            data = template.render(ipv4public=ipv4public)
        return data

    def deb_eth1_data(self, ipv4private):
        ipv4private = self._update_ip_prefix(ipv4private)
        template = Template(eth1_deb.data)
        data = template.render(ipv4private=ipv4private)
        return data

    def deb_eth2_data(self, ipv4private):
        template = Template(eth2_deb.data)
        data = template.render(ipv4private=ipv4private)
        return data

    def ubt_eth0_data(self, ipv4public, ipv4compute, ipv6public=None, cloud="public"):
        data = ""
        ipv4public, ipv4compute, _ = self._update_network_prefixes(
            ipv4public, ipv4compute
        )
        if cloud == "public":
            template = Template(eth0_ubt_public.data)
            data = template.render(
                ipv4public=ipv4public, ipv4compute=ipv4compute, ipv6public=ipv6public
            )
        if cloud == "private":
            template = Template(eth0_ubt_private.data)
            data = template.render(ipv4public=ipv4public)
        return data

    def ubt_eth1_data(self, ipv4private):
        ipv4private = self._update_ip_prefix(ipv4private)
        template = Template(eth1_ubt.data)
        data = template.render(ipv4private=ipv4private)
        return data

    def rhl_eth0_data(self, ipv4public, ipv4compute, ipv6public=None, cloud="public"):
        ipv4public, ipv4compute, _ = self._update_network_prefixes(
            ipv4public, ipv4compute
        )
        if cloud == "public":
            template = Template(eth0_rhl_public.data)
            data = template.render(
                ipv4public=ipv4public, ipv4compute=ipv4compute, ipv6public=ipv6public
            )
        if cloud == "private":
            template = Template(eth0_rhl_private.data)
            data = template.render(ipv4public=ipv4public)
        return data

    def rhl_eth1_data(self, ipv4private):
        template = Template(eth1_rhl.data)
        data = template.render(ipv4private=ipv4private)
        return data

    def fed_eth0_data(self, ipv4public, ipv4compute, ipv6public=None, cloud="public"):
        ipv4public, ipv4compute, _ = self._update_network_prefixes(
            ipv4public, ipv4compute
        )
        if cloud == "public":
            template = Template(eth0_fed_public.data)
            data = template.render(
                ipv4public=ipv4public, ipv4compute=ipv4compute, ipv6public=ipv6public
            )
        if cloud == "private":
            template = Template(eth0_fed_private.data)
            data = template.render(ipv4public=ipv4public)
        return data

    def fed_eth1_data(self, ipv4private):
        ipv4private = self._update_ip_prefix(ipv4private)
        template = Template(eth1_fed.data)
        data = template.render(ipv4private=ipv4private)
        return data

    def win_eth0_data(self, ipv4public, ipv4compute, ipv6public=None, cloud="public"):
        ipv4public, ipv4compute, _ = self._update_network_prefixes(
            ipv4public, ipv4compute
        )
        if cloud == "public":
            template = Template(eth0_win_public.data)
            data = template.render(
                ipv4public=ipv4public, ipv4compute=ipv4compute, ipv6public=ipv6public
            )
        if cloud == "private":
            template = Template(eth0_win_private.data)
            data = template.render(ipv4public=ipv4public)
        return data

    def win_eth1_data(self, ipv4private):
        template = Template(eth1_win.data)
        data = template.render(ipv4private=ipv4private)
        return data

    def _get_network_impl(self, method_name):
        """
        Helper method to get the appropriate network implementation method for the current OS family.

        Args:
            method_name (str): Base name of the method to call

        Returns:
            callable: The appropriate method for this OS family
        """
        handlers = {
            "deb": getattr(self, f"deb_{method_name}"),
            "ubt": getattr(self, f"ubt_{method_name}"),
            "rhl": getattr(self, f"rhl_{method_name}"),
            "fed": getattr(self, f"fed_{method_name}"),
            "win": getattr(self, f"win_{method_name}"),
        }
        return handlers.get(self.os_family)

    def _write_network_file(self, file_path, content):
        """
        Helper method to write network configuration to a file and set permissions.

        Args:
            file_path (str): Path to the network configuration file
            content (str): Content to write to the file
        """
        self.gfs.write(file_path, content)
        if self.os_family != "win":
            self.gfs.chmod(int("0644", 8), file_path)

    def public_nic_setup(self, ipv4public, ipv4compute, ipv6public):
        """
        Configure the public network interface.

        Args:
            ipv4public (dict): Public IPv4 configuration
            ipv4compute (dict): Compute IPv4 configuration
            ipv6public (dict): IPv6 configuration
        """
        nic_f_path = self.nic_file_path()
        impl = self._get_network_impl("eth0_data")

        if impl:
            network_file_data = impl(ipv4public, ipv4compute, ipv6public=ipv6public)
            self._write_network_file(nic_f_path, network_file_data)

    def private_nic_setup(self, ipv4private):
        """
        Configure the private network interface.

        Args:
            ipv4private (dict): Private IPv4 configuration
        """
        nic_f_path = self.nic_file_path(
            nic_type="private" if self.os_family in ["rhl", "fed"] else "public"
        )
        impl = self._get_network_impl("eth1_data")

        if impl:
            if self.os_family in ["deb", "ubt", "win"]:
                # For these OS types, we append to the existing config
                pub_nic_data = self.gfs.cat(nic_f_path)
                priv_nic_data = impl(ipv4private)
                network_file_data = pub_nic_data + priv_nic_data
            else:
                # For rhl and fed, we create a new file
                network_file_data = impl(ipv4private)

            self._write_network_file(nic_f_path, network_file_data)

    def vpc_gw_nic_setup(self, ipv4vpc):
        """
        Configure the VPC gateway network interface.

        Args:
            ipv4vpc (dict): VPC IPv4 configuration
        """
        if self.os_family == "deb":
            nic_f_path = self.nic_file_path()
            pub_nic_data = self.gfs.cat(nic_f_path)
            vpc_nic_data = self.deb_eth2_data(ipv4vpc)
            network_file_data = pub_nic_data + vpc_nic_data
            self._write_network_file(nic_f_path, network_file_data)

    def vpc_nic_setup(self, ipv4vpc):
        """
        Configure the VPC network interface.

        Args:
            ipv4vpc (dict): VPC IPv4 configuration
        """
        nic_f_path = self.nic_file_path()
        impl = self._get_network_impl("eth0_data")

        if impl:
            network_file_data = impl(ipv4vpc, None, None, cloud="private")
            self._write_network_file(nic_f_path, network_file_data)

    def private_cloud_nic_setup(self, ipv4public):
        """
        Configure the network interface for a private cloud setup.

        Args:
            ipv4public (dict): Public IPv4 configuration
        """
        nic_f_path = self.nic_file_path()
        impl = self._get_network_impl("eth0_data")

        if impl:
            network_file_data = impl(ipv4public, None, None, cloud="private")
            self._write_network_file(nic_f_path, network_file_data)

    def setup_networking(self, networks, cloud="public"):
        """
        Configure networking for the VM based on provided network configuration.

        Args:
            networks (dict): Network configuration data
            cloud (str): Cloud type, either "public" or "private"
        """
        ipv6public = networks.get("v6")
        ipv4vpc = networks.get("v4", {}).get("vpc")
        ipv4private = networks.get("v4", {}).get("private")
        ipv4public = networks.get("v4", {}).get("public", {}).get("primary")
        ipv4compute = networks.get("v4", {}).get("public", {}).get("secondary")

        if cloud == "public":
            try:
                self.public_nic_setup(ipv4public, ipv4compute, ipv6public=ipv6public)
                if ipv4private:
                    self.private_nic_setup(ipv4private)
                # Only for VPC gateway
                if ipv4vpc:
                    self.vpc_gw_nic_setup(ipv4vpc)
            except Exception as e:
                logger.error(f"Error setting up public network: {str(e)}")
                raise

        elif cloud == "private":
            try:
                if ipv4vpc:
                    self.vpc_nic_setup(ipv4vpc)
                else:
                    logger.warning(
                        "No VPC network configuration provided for private cloud setup"
                    )
            except Exception as e:
                logger.error(f"Error setting up private network: {str(e)}")
                raise

    def change_ipv4fixed(self, ipv4compute):
        """
        Change the fixed IPv4 address in the network configuration.

        Args:
            ipv4compute (dict): Compute IPv4 configuration
        """
        if not ipv4compute or self.os_family == "win":
            return

        nic_f_path = self.nic_file_path()
        nic_file = self.gfs.cat(nic_f_path)

        os_handlers = {
            "deb": {
                "pattern": r"^address 10\.255\..*?",
                "replacement": f"address {ipv4compute.get('address')}",
            },
            "ubt": {
                "pattern": r"^- 10\.255\..*?",
                "replacement": f"- {ipv4compute.get('address')}/{ipv4compute.get('prefix')}",
            },
            "rhl": {
                "pattern": r"^IPADDR2=.*?",
                "replacement": f"IPADDR2={ipv4compute.get('address')}",
            },
            "fed": {
                "pattern": r"^address2=.*?",
                "replacement": f"address2={ipv4compute.get('address')}/{ipv4compute.get('prefix')}",
            },
        }

        if self.os_family in os_handlers:
            handler = os_handlers[self.os_family]
            network_file_data = re.sub(
                handler["pattern"], handler["replacement"], nic_file
            )
            self._write_network_file(nic_f_path, network_file_data)

    def change_root_passwd(self, password_hash, shadow_file):
        shadow_file_updated = ""
        if self.os_family == "win":
            pass
        else:
            root_shadow_line = f"root:{password_hash}:"
            shadow_file_updated = re.sub("^root:.*?:", root_shadow_line, shadow_file)
        return shadow_file_updated

    def reset_root_passwd(self, pass_hash):
        if self.os_family == "win":
            nic_f_path = self.nic_file_path()
            f_data = self.gfs.cat(nic_f_path)
            str_pswd = f"net user Administrator {pass_hash}\r\n"
            f_data += str_pswd
            self.gfs.write(nic_f_path, f_data)
        else:
            shadow_fl_path = self.shadow_file_path()
            file_shadow = self.gfs.cat(shadow_fl_path)
            shadow_file_updated = self.change_root_passwd(pass_hash, file_shadow)
            self.gfs.write(shadow_fl_path, shadow_file_updated)
            self.gfs.chmod(int("0640", 8), shadow_fl_path)

    def set_pubic_keys(self, keys_string):
        if keys_string:
            if self.os_family == "win":
                pass
            else:
                root_ssh_folder_path = self.root_ssh_dir_path()
                root_fl_auth_key_path = self.root_auth_keys_path()
                if not self.gfs.is_dir(root_ssh_folder_path):
                    self.gfs.mkdir(root_ssh_folder_path)
                    self.gfs.chmod(int("0700", 8), root_ssh_folder_path)
                self.gfs.write(root_fl_auth_key_path, keys_string)
                self.gfs.chmod(int("0600", 8), root_fl_auth_key_path)

    def set_hostname(self, hostname):
        if self.os_family == "win":
            nic_f_path = self.nic_file_path()
            f_data = self.gfs.cat(nic_f_path)
            h_data = rf"wmic computersystem where name='%COMPUTERNAME%' call rename name='{hostname}'\r\n"
            f_data += h_data
            self.gfs.write(nic_f_path, f_data)
        else:
            f_path = self.hostname_file_path()
            self.gfs.write(f_path, hostname)

    def clean_cloud_init(self):
        if self.os_family == "win":
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
        if self.os_family == "win":
            if not self.gfs.mounts():
                self.mount_root()
            self.resize_win_fs()

    def mount_root(self):
        """
        Mount the root filesystem of the VM.
        Handles Windows NTFS and Linux filesystems differently.
        """
        device = self.root_device()
        try:
            if self.os_family == "win":
                try:
                    self.gfs.mount(device, "/")
                except RuntimeError:
                    logger.info(f"Running ntfsfix on {device} before mounting")
                    self.gfs.ntfsfix(device)
                    self.gfs.mount(device, "/")
            else:
                self.gfs.mount(device, "/")
            logger.debug(f"Successfully mounted {device}")
        except Exception as e:
            logger.error(f"Failed to mount {device}: {str(e)}")
            raise

    def umount_root(self):
        """
        Unmount the root filesystem of the VM.
        """
        try:
            if self.gfs.mounts():
                device = self.root_device()
                self.gfs.umount(device)
                logger.debug(f"Successfully unmounted {device}")
        except Exception as e:
            logger.error(f"Failed to unmount: {str(e)}")
            raise

    def clearfix(self, firstboot=True):
        """
        Perform cleanup and first-boot operations for the VM.

        Args:
            firstboot (bool): Whether this is the first boot of the VM
        """
        try:
            if self.os_family == "rhl":
                if firstboot:
                    if not self.gfs.mounts():
                        self.mount_root()
                    self.gfs.touch("/.autorelabel")
                    logger.debug("Created /.autorelabel for RHEL-based system")

            if self.os_family == "win":
                if not self.gfs.mounts():
                    self.mount_root()
                nic_f_path = self.nic_file_path()
                f_data = self.gfs.cat(nic_f_path)
                if firstboot:
                    f_data += self._win_str_shutdown()
                f_data += self._win_clean_cloudinit()
                self.gfs.write(nic_f_path, f_data)
                logger.debug(f"Updated Windows startup script at {nic_f_path}")
        except Exception as e:
            logger.error(f"Error in clearfix: {str(e)}")
            raise

    def close(self):
        """
        Close the libguestfs session and free resources.
        """
        try:
            # Ensure all filesystems are unmounted before shutdown
            if self.gfs.mounts():
                for mount in self.gfs.mounts():
                    self.gfs.umount(mount)

            self.gfs.shutdown()
            self.gfs.close()
            logger.debug(f"Successfully closed libguestfs session for {self.drive}")
        except Exception as e:
            logger.error(f"Error closing libguestfs session: {str(e)}")
            # Don't raise here, as this is typically called during cleanup
