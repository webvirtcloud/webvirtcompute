import os
import requests
from libvirt import libvirtError
from subprocess import call, STDOUT, DEVNULL

from settings import CACHE_DIR
from .util import md5sum
from .libguestfs import GuestFSUtil
from .libvrt import wvmConnect, wvmStorage


ROOT_DIR = os.path.dirname(os.path.abspath(os.path.join(__file__, "..")))


class Template(object):
    def __init__(self, template_name, template_md5sum):
        self.template_name = template_name
        self.template_md5sum = template_md5sum
        self.template_image_path = None

    def download(self, template_url):
        err_msg = None
        download_image = True
        template_image_md5 = None
        template_image_url = template_url
        template_image_path = os.path.join(CACHE_DIR, os.path.basename(template_image_url))

        # Check if cache dir exist
        if not os.path.isdir(CACHE_DIR):
            os.mkdir(CACHE_DIR)

        if os.path.exists(template_image_path):
            template_image_md5 = md5sum(template_image_path)
            if template_image_md5 == self.template_md5sum:
                download_image = False

        if download_image:
            try:
                r = requests.get(template_image_url, stream=True)
                with open(template_image_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=128):
                        f.write(chunk)
            except Exception as err:
                err_msg = err

            template_image_md5 = md5sum(template_image_path)

        self.template_image_path = template_image_path

        if self.template_md5sum != template_image_md5:
            err_msg = "MD5 sum mismatch"

        return err_msg, template_image_path


class Image(object):
    def __init__(self, name, pool):
        self.name = name
        self.pool = pool

        conn = wvmStorage(self.pool)
        conn.refresh()
        self.image_path = conn.get_target_path() + "/" + self.name
        conn.close()

    def image_resize(self, disk_size):
        conn = wvmStorage(self.pool)
        conn.refresh()
        conn.resize_volume(self.name, disk_size)
        conn.close()

    def deploy_template(self, template, disk_size, networks, public_keys, hostname, root_password, cloud="public"):
        err_msg = "Error convert template to image"
        template_name = template.template_name
        template_image_path = template.template_image_path

        qemu_img_cmd = f"qemu-img convert -f qcow2 -O raw {template.template_image_path} {self.image_path}"
        run_qemu_img_cmd = call(qemu_img_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
        if run_qemu_img_cmd == 0:
            err_msg = self._run(disk_size, template_name, networks, public_keys, hostname, cloud, root_password)

        return err_msg

    def _run(self, disk_size, template_name, networks, public_keys, hostname, cloud, root_password):
        err_msg = None
        public_key_string = None
        
        for key in public_keys:
            if public_key_string is not None:
                public_key_str += "\n" + key
            else:
                public_key_string = key

        try:
            self.image_resize(disk_size)
        except libvirtError as err:
            err_msg = err

        if err_msg is None:
            try:
                # Load GuestFS
                gstfish = GuestFSUtil(self.image_path, template_name)
                gstfish.mount_root()
                gstfish.setup_networking(networks, cloud=cloud)
                gstfish.set_pubic_keys(public_key_string)
                gstfish.set_hostname(hostname)
                gstfish.reset_root_passwd(root_password)
                gstfish.resize_fs()
                gstfish.clearfix()
                gstfish.close()
            except RuntimeError as err:
                err_msg = err

        return err_msg

    def reset_password(self, name, root_password):
        err_msg = None

        try:
            # Load GuestFS
            gstfish = GuestFSUtil(self.image_path, distro)
            gstfish.mount_root()
            gstfish.reset_root_passwd(root_password)
            gstfish.clearfix(firstboot=False)
            gstfish.close()
        except RuntimeError as err:
            err_msg = err

        return err_msg

    def guestfs_resize(self, distro, disk_size):
        err_msg = None

        try:
            self.image_resize(disk_size)
        except libvirtError as err:
            err_msg = err

        if err_msg is None:
            try:
                # Load GuestFS
                gstfish = GuestFSUtil(self.image_path, distro)
                gstfish.resize_fs()
                gstfish.clearfix(firstboot=False)
                gstfish.close()
            except RuntimeError as err:
                err_msg = err

        return err_msg
