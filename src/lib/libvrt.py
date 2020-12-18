#
# libvrt - simple class for resize images
#

import re
import libvirt
from xml.etree import ElementTree
from .logger import method_logger, function_logger


@function_logger()
def refresh_storages(conn):
    for pool in conn.listStoragePools():
        stg = conn.storagePoolLookupByName(pool)
        stg.refresh()


class LibVrt(object):
    @method_logger()
    def __init__(self):
        self.conn = libvirt.open('qemu:///system')

    @method_logger()
    def __get_run_instances(self):
        instances = []
        for inst_id in self.conn.listDomainsID():
            dom = self.conn.lookupByID(int(inst_id))
            instances.append(dom.name())
        return instances

    @method_logger()
    def image_resize(self, path, size):
        refresh_storages(self.conn)
        vol = self.conn.storageVolLookupByPath(path)
        vol.resize(size, 0)

    @method_logger()
    def get_image_size(self, path):
        refresh_storages(self.conn)
        vol = self.conn.storageVolLookupByPath(path)
        stg = vol.storagePoolLookupByVolume()
        stg.refresh()
        return vol.info()[2]

    @method_logger()
    def get_disk_size(self, path):
        refresh_storages(self.conn)
        vol = self.conn.storageVolLookupByPath(path)
        stg = vol.storagePoolLookupByVolume()
        stg.refresh()
        return vol.info()[1]

    @method_logger()
    def check_image(self, path, size):
        refresh_storages(self.conn)
        vol = self.conn.storageVolLookupByPath(path)
        stg = vol.storagePoolLookupByVolume()
        if vol.info()[2] > 200704:
            name = vol.name()
            vol.delete(0)
            xml = """
                <volume>
                    <name>%s</name>
                    <capacity>%s</capacity>
                    <allocation>0</allocation>
                    <target>
                        <format type='qcow2'/>
                    </target>
                </volume>""" % (name, size)
            stg.createXML(xml, 0)
            stg.refresh()

    @method_logger()
    def win_img_for_resize(self, path, size):
        refresh_storages(self.conn)
        vol = self.conn.storageVolLookupByPath(path)
        name = vol.name().split('.')[0] + '_resize' + '.img'
        xml = """
            <volume>
                <name>%s</name>
                <capacity>%s</capacity>
                <allocation>0</allocation>
                <target>
                    <format type='qcow2'/>
                </target>
            </volume>""" % (name, size)
        stg = vol.storagePoolLookupByVolume()
        stg.refresh()
        try:
            stg.createXML(xml, 0)
        except libvirt.libvirtError:
            vol = stg.storageVolLookupByName(name)
            vol.delete(0)
            stg.createXML(xml, 0)
        created_vol = stg.storageVolLookupByName(name)
        return created_vol.path()

    @method_logger()
    def close(self):
        self.conn.close()
