import os
from subprocess import call, STDOUT
from .logger import method_logger
from .libguestfs import GuestFSUtil
from .excpetions import IPRedirectError
from .libredirect import FwRedirect, NetManager
from settings import BRIDGE_EXT, FIREWALLD_STATE_TIMEOUT
try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'wb')


class AnchorIP(object):
    @method_logger()
    def __init__(self, anchor_ip):
        self.anchor_ip = anchor_ip

    @method_logger()
    def attach_floating_ip(self, floating_ip, floating_prefix, floating_gw):
        err_msg = None
        try:
            nmc = NetManager(floating_ip)
            fwd = FwRedirect(floating_ip, self.anchor_ip)
            dev = BRIDGE_EXT
            self.add_redirect(fwd, floating_ip, floating_prefix, floating_gw, nmc, dev)
        except IPRedirectError as err:
            err_msg = err

        return err_msg

    @method_logger()
    def detach_floating_ip(self, floating_ip, floating_prefix):
        err_msg = None
        dev = BRIDGE_EXT
        nmc = NetManager(floating_ip)
        fwd = FwRedirect(floating_ip, self.anchor_ip)
        try:
            self.remove_redirect(fwd, floating_ip, floating_prefix, nmc, dev)
        except IPRedirectError as err:
            err_msg = err

        return err_msg

    @method_logger()
    def change_anchor_ip(self, image_path, distro):
        err_msg = None
        try:
            # Load GuestFS
            gstfish = GuestFSUtil(image_path, distro)
            gstfish.mount_root()
            gstfish.change_ipv4anch(self.anchor_ip)
            gstfish.close()
        except RuntimeError as err:
            err_msg = err

        return err_msg

    @method_logger()
    def add_addr(self, float_addr, nmc, dev, prefix=32):
        if float_addr not in nmc.get_ip_addresses():
            ip_cmd = 'ip addr add {}/{} dev {}'.format(float_addr, prefix, dev)
            run_ip_cmd = call(ip_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
            if run_ip_cmd == 0:
                nmc.add_address(prefix=prefix)
                return True
        return False

    @method_logger()
    def del_addr(self, nmc, float_addr, dev, prefix=32):
        if float_addr in nmc.get_ip_addresses():
            ip_cmd = 'ip addr del {}/{} dev {}'.format(float_addr, prefix, dev)
            run_ip_cmd = call(ip_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
            if run_ip_cmd == 0:
                nmc.remove_address(prefix)
                return True
        return False

    @method_logger()
    def check_rule(self, fwd):
        return fwd.query_rule()

    @method_logger()
    def add_rule(self, fwd):
        if not self.check_rule(fwd):
            fwd.add_rule()

    @method_logger()
    def del_rule(self, fwd):
        if self.check_rule(fwd):
            fwd.remove_rule()

    @method_logger()
    def clear_arp(self, float_addr, float_gw, dev):
        arp_cmd = 'arping -c 3 -s {} -I {} -U {}'.format(float_addr, dev, float_gw)
        run_arp_cmd = call(arp_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
        if run_arp_cmd == 0:
            return True

    @method_logger()
    def add_redirect(self, fwd, float_addr, float_pref, float_gw, nmc, dev):
        if self.add_addr(float_addr, nmc, dev, prefix=float_pref):
            if not fwd.is_locked():
                fwd.set_state()
                self.add_rule(fwd)
                self.clear_arp(float_addr, float_gw, dev)
            else:
                self.del_addr(nmc, float_addr, dev, prefix=float_pref)
                raise IPRedirectError('Firewall closed connection by timeout %ssec.' % FIREWALLD_STATE_TIMEOUT)
        else:
            raise IPRedirectError('Error adding IP address to the network device.')

    @method_logger()
    def remove_redirect(self, fwd, float_addr, float_pref, nmc, dev):
        if self.del_addr(nmc, float_addr, dev, prefix=float_pref):
            if not fwd.is_locked():
                fwd.set_state()
                self.del_rule(fwd)
            else:
                self.add_addr(float_addr, nmc, dev, prefix=float_pref)
                raise IPRedirectError('Firewall closed connection by timeout %ssec.' % FIREWALLD_STATE_TIMEOUT)
        else:
            raise IPRedirectError('Error deleting IP address from the network device.')
