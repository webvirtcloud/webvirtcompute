#
# libvrt - simple class for resize images
#

import re
import libvirt
from xml.etree import ElementTree
from .logger import method_logger


class LibVrt(object):
    @method_logger()
    def __init__(self):
        self.conn = libvirt.open('qemu:///system')

    @method_logger()
    def get_cap_xml(self):
        return self.conn.getCapabilities()

    @method_logger()
    def is_kvm_supported(self):
        return util.is_kvm_available(self.get_cap_xml())

    @method_logger()
    def get_node_info(self):
        nodeinfo = self.conn.getInfo()
        return {
            'hostname': self.conn.getHostname(),
            'arch': nodeinfo[0],
            'memory': nodeinfo[1] * (1024 ** 2),
            'cpus': nodeinfo[2],
            'processor': util.get_xml_data(self.conn.getSysinfo(0), 'processor/entry[6]'),
            'connection': self.conn.getURI()
        }

    @method_logger()
    def get_node_type(self):
        return util.get_xml_data(self.get_cap_xml(), 'guest/arch/domain', 'type')

    @method_logger()
    def get_host_mem_usage(self):
        host_mem = self.wvm.getInfo()[1] * (1024**2)
        free_mem = self.wvm.getMemoryStats(-1, 0)
        if isinstance(free_mem, dict):
            mem = list(free_mem.values())
            free = (mem[1] + mem[2] + mem[3]) * 1024
            percent = (100 - ((free * 100) / host_mem))
            usage = (host_mem - free)
            return {'size': host_mem, 'usage': usage, 'percent': round(percent)}
        return {'size': 0, 'usage': 0, 'percent': 0}

    @method_logger()
    def get_host_cpu_usage(self):
        prev_idle = prev_total = diff_usage = 0
        cpu = self.wvm.getCPUStats(-1, 0)
        if isinstance(cpu, dict):
            for num in range(2):
                idle = self.wvm.getCPUStats(-1, 0)['idle']
                total = sum(self.wvm.getCPUStats(-1, 0).values())
                diff_idle = idle - prev_idle
                diff_total = total - prev_total
                diff_usage = (1000 * (diff_total - diff_idle) / diff_total + 5) / 10
                prev_total = total
                prev_idle = idle
                if num == 0:
                    time.sleep(1)
                if diff_usage < 0:
                    diff_usage = 0
        return {'usage': round(diff_usage)}

    @method_logger()
    def get_storage_usage(self, name):
        pool = self.get_storage(name)
        pool.refresh()
        if pool.isActive():
            size = pool.info()[1]
            free = pool.info()[3]
            used = size - free
            percent = (used * 100) / size
            return {'size': size, 'used': used, 'percent': percent}
        return {'size': 0, 'used': 0, 'percent': 0}

    @method_logger()
    def get_storages(self):
        storages = []
        for pool in self.conn.listStoragePools():
            storages.append(pool)
        for pool in self.conn.listDefinedStoragePools():
            storages.append(pool)
        return storages

    @method_logger()
    def get_networks(self):
        virtnet = []
        for net in self.conn.listNetworks():
            virtnet.append(net)
        for net in self.conn.listDefinedNetworks():
            virtnet.append(net)
        return virtnet

    @method_logger()
    def refresh_storages(self):
        for pool in self.conn.listStoragePools():
            stg = self.conn.storagePoolLookupByName(pool)
            stg.refresh()

    @method_logger()
    def get_ifaces(self):
        interface = []
        for inface in self.conn.listInterfaces():
            interface.append(inface)
        for inface in self.conn.listDefinedInterfaces():
            interface.append(inface)
        return interface

    @method_logger()
    def get_iface(self, name):
        return self.conn.interfaceLookupByName(name)

    @method_logger()
    def get_secrets(self):
        return self.conn.listSecrets()

    @method_logger()
    def get_secret(self, uuid):
        return self.conn.secretLookupByUUIDString(uuid)

    @method_logger()
    def get_storage(self, name):
        return self.conn.storagePoolLookupByName(name)

    @method_logger()
    def get_volume_by_path(self, path):
        return self.conn.storageVolLookupByPath(path)

    @method_logger()
    def get_network(self, net):
        return self.conn.networkLookupByName(net)

    @method_logger()
    def get_instance(self, name):
        return self.conn.lookupByName(name)

    @method_logger()
    def get_instance_status(self, name):
        dom = self.conn.lookupByName(name)
        return dom.info()[0]

    @method_logger()
    def get_instances(self):
        instances = []
        for inst_id in self.conn.listDomainsID():
            dom = self.conn.lookupByID(int(inst_id))
            instances.append(dom.name())
        for name in self.conn.listDefinedDomains():
            instances.append(name)
        return instances

    @method_logger()
    def get_snapshots(self):
        instance = []
        for snap_id in self.conn.listDomainsID():
            dom = self.conn.lookupByID(int(snap_id))
            if dom.snapshotNum(0) != 0:
                instance.append(dom.name())
        for name in self.conn.listDefinedDomains():
            dom = self.conn.lookupByName(name)
            if dom.snapshotNum(0) != 0:
                instance.append(dom.name())
        return instance

    @method_logger()
    def get_net_device(self):
        netdevice = []
        for dev in self.conn.listAllDevices(0):
            xml = dev.XMLDesc(0)
            if util.get_xml_data(xml, 'capability', 'type') == 'net':
                netdevice.append(util.get_xml_data(xml, 'capability/interface'))
        return netdevice

    @method_logger()
    def get_host_instances(self):
        vname = {}
        for name in self.get_instances():
            dom = self.get_instance(name)
            mem = util.get_xml_data(dom.XMLDesc(0), 'currentMemory')
            mem = round(int(mem) / 1024)
            cur_vcpu = util.get_xml_data(dom.XMLDesc(0), 'vcpu', 'current')
            if cur_vcpu:
                vcpu = cur_vcpu
            else:
                vcpu = util.get_xml_data(dom.XMLDesc(0), 'vcpu')
            vname[dom.name()] = {'status': dom.info()[0], 'uuid': dom.UUIDString(), 'vcpu': vcpu, 'memory': mem}
        return vname

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
