import os
import requests
from subprocess import call, STDOUT
from settings import CACHE_DIR
from .common import md5sum
from .logger import method_logger
from .libvrt import LibVrt
from .libguestfs import GuestFSUtil
try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'wb')


ROOT_DIR = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))


class Template(object):
    @method_logger()
    def __init__(self, template_name, template_md5sum):
        self.template_name = template_name
        self.template_md5sum = template_md5sum
        self.template_image_path = None

    @method_logger()
    def download(self, template_url):
        """
        :param template_url(string): url todownload if not in cache
        :return: err_msg(string),template_image_path(string):err_msg will be None if successful
        """
        err_msg = 'MD5 sum mismatch'
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
                with open(template_image_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=128):
                        f.write(chunk)
            except Exception as err:
                err_msg = err

            template_image_md5 = md5sum(template_image_path)

        self.template_image_path = template_image_path

        if self.template_md5sum == template_image_md5:
            return None, template_image_path
        else:
            return err_msg, template_image_path


class Image(object):
    @method_logger()
    def __init__(self, image_path):
        self.image_path = image_path

    @method_logger()
    def deploy_template(self, template, disk_size, networks, public_key, hostname, root_password, cloud):
        """
        :param template(instance of class Template):
        :param disk_size:
        :param networks:
        :param public_key:
        :param hostname:
        :param root_password:
        :param cloud:
        :return: err_msg(string)
        """
        template_image_path = template.template_image_path
        template_name = template.template_name

        err_msg = 'Error convert template to image'

        qemu_img_cmd = "qemu-img convert -f qcow2 -O raw %s %s" % (template_image_path, self.image_path)
        run_qemu_img_cmd = call(qemu_img_cmd.split(), stdout=DEVNULL, stderr=STDOUT)
        if run_qemu_img_cmd == 0:
            err_msg = self._run(disk_size, template_name, networks, public_key, hostname,cloud, root_password)

        return err_msg

    @method_logger()
    def _run(self, disk_size, template_name, networks, public_key, hostname, cloud, root_password):
        err_msg = None

        vrt = LibVrt()
        vrt.image_resize(self.image_path, disk_size)
        vrt.close()

        try:
            # Load GuestFS
            gstfish = GuestFSUtil(
                self.image_path,
                template_name
            )
            gstfish.mount_root()
            gstfish.setup_networking(
                networks,
                cloud=cloud
            )
            gstfish.set_pubic_keys(public_key)
            gstfish.set_hostname(hostname)
            gstfish.reset_root_passwd(root_password)
            gstfish.resize_fs()
            gstfish.clearfix()
            gstfish.close()
        except RuntimeError as err:
            err_msg = err

        return err_msg

    @method_logger()
    def reset_password(self, distro, root_password):
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

    @method_logger()
    def resize(self, distro, disk_size):
        err_msg = None
        vrt = LibVrt()
        vrt.image_resize(self.image_path, disk_size)
        vrt.close()
        try:
            # Load GuestFS
            gstfish = GuestFSUtil(self.image_path, distro)
            gstfish.resize_fs()
            gstfish.clearfix(firstboot=False)
            gstfish.close()
        except RuntimeError as err:
            err_msg = err

        return err_msg
