import os
import requests
from libvirt import libvirtError
from subprocess import call, STDOUT, DEVNULL

from settings import CACHE_DIR
from .util import md5sum
from .libvrt import wvmStorage
from .libguestfs import GuestFSUtil


ROOT_DIR = os.path.dirname(os.path.abspath(os.path.join(__file__, "..")))


class Template(object):
    def __init__(self, url, md5sum):
        self.url = url
        self.md5sum = md5sum
        self.path = None

    def download(self):
        err_msg = None
        try_download = True
        template_md5 = None
        template_path = os.path.join(CACHE_DIR, os.path.basename(self.url))

        # Check if cache dir exist
        if not os.path.isdir(CACHE_DIR):
            os.mkdir(CACHE_DIR)

        if os.path.exists(template_path):
            template_md5 = md5sum(template_path)
            if template_md5 == self.md5sum:
                try_download = False

        if try_download:
            try:
                r = requests.get(self.url, stream=True)
                with open(template_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=128):
                        f.write(chunk)
            except Exception as err:
                err_msg = err

            template_md5 = md5sum(template_path)

        self.path = template_path

        if self.md5sum != template_md5:
            err_msg = "MD5 sum mismatch"

        return err_msg


class Image(object):
    def __init__(self, name, pool):
        self.name = name if '.img' in name else name + ".img"
        self.pool = pool

        conn = wvmStorage(self.pool)
        conn.refresh()
        self.image_path = f"{conn.get_target_path()}/{self.name}"
        conn.close()

    def resize(self, disk_size):
        conn = wvmStorage(self.pool)
        conn.refresh()
        conn.resize_volume(self.name, disk_size)
        conn.close()

    def create_copy(self, name, pool, compress=False):
        err_msg = None
        target_name = name if '.img' in name else name + ".img"
        target_size = 0
        target_disk_size = 0
        target_md5sum = None
    
        conn = wvmStorage(pool)
        conn.refresh()
        taraget_path = f"{conn.get_target_path()}/{target_name}"

        if err_msg is None:
            qemu_img_cmd = f'qemu-img convert -U -O qcow2 {self.image_path} {taraget_path}'
            if compress is True:
                qemu_img_cmd = f'qemu-img convert -U -c -O qcow2 {self.image_path} {taraget_path}'
            run_qemu_img_cmd = call(qemu_img_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
            if run_qemu_img_cmd == 0:
                conn.refresh()
                vol = conn.get_volume(target_name)
                target_disk_size, target_size = vol.info()[1:3]
                conn.close()

                target_md5sum = md5sum(taraget_path)
            else:
                err_msg = 'Error convert image to snapshot'

        return {
            "error": err_msg, "size": target_size,  "md5sum": target_md5sum,
            "disk_size": target_disk_size, "file_name": target_name,
        }
    
    def restore_copy(self, name, pool, disk_size):
        err_msg = None
        target_disk_size = 0
        target_name = name if '.img' in name else name + ".img"
    
        conn = wvmStorage(pool)
        conn.refresh()
        taraget_path = f"{conn.get_target_path()}/{target_name}"

        if err_msg is None:
            qemu_img_cmd = f'qemu-img convert -O raw {self.image_path} {taraget_path}'
            run_qemu_img_cmd = call(qemu_img_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
            if run_qemu_img_cmd == 0:
                conn.refresh()
                vol = conn.get_volume(target_name)
                target_disk_size = vol.info()[1]
            else:
                err_msg = 'Error convert image to snapshot'
            
        if disk_size > target_disk_size:
            vol.resize(disk_size)

        conn.close()

        return {"error": err_msg}

    def deploy_template(self, template_path, disk_size, networks, public_keys, hostname, root_password, cloud="public"):
        err_msg = "Error convert template to image"

        qemu_img_cmd = f"qemu-img convert -f qcow2 -O raw {template_path} {self.image_path}"
        run_qemu_img_cmd = call(qemu_img_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
        if run_qemu_img_cmd == 0:
            err_msg = self._run(disk_size, networks, public_keys, hostname, root_password, cloud=cloud)

        return err_msg

    def _run(self, disk_size, networks, public_keys, hostname, root_password, cloud="public"):
        err_msg = None
        public_key_string = None

        for key in public_keys:
            if public_key_string is not None:
                public_key_string += f"\n{key}"
            else:
                public_key_string = key

        try:
            self.resize(disk_size)
        except libvirtError as err:
            err_msg = err

        if err_msg is None:
            try:
                # Load GuestFS
                gstfish = GuestFSUtil(self.image_path)
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

    def reset_password(self, root_password):
        err_msg = None

        try:
            # Load GuestFS
            gstfish = GuestFSUtil(self.image_path)
            gstfish.mount_root()
            gstfish.reset_root_passwd(root_password)
            gstfish.clearfix(firstboot=False)
            gstfish.close()
        except RuntimeError as err:
            err_msg = err

        return err_msg

    def guestfs_resize(self, disk_size):
        err_msg = None

        try:
            self.resize(disk_size)
        except libvirtError as err:
            err_msg = err

        if err_msg is None:
            try:
                # Load GuestFS
                gstfish = GuestFSUtil(self.image_path)
                gstfish.resize_fs()
                gstfish.clearfix(firstboot=False)
                gstfish.close()
            except RuntimeError as err:
                err_msg = err

        return err_msg
