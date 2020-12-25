#
# libvrt - libvirt wrapper class
#

import re
import libvirt
from . import util
from xml.etree import ElementTree
from .logger import method_logger


class wvmConnect(object):
    @method_logger()
    def __init__(self):
        self.wvm = libvirt.open('qemu:///system')

    @method_logger()
    def get_cap_xml(self):
        return self.wvm.getCapabilities()

    @method_logger()
    def is_kvm_supported(self):
        return util.is_kvm_available(self.get_cap_xml())

    @method_logger()
    def get_host_info(self):
        nodeinfo = self.wvm.getInfo()
        processor = util.get_xml_data(self.wvm.getSysinfo(0), 'processor/entry[6]')
        return {
            'hostname': self.wvm.getHostname(),
            'arch': nodeinfo[0],
            'memory': nodeinfo[1] * (1024 ** 2),
            'cpus': nodeinfo[2],
            'processor': processor if processor else 'Unknown',
            'connection': self.wvm.getURI()
        }

    @method_logger()
    def get_host_type(self):
        return util.get_xml_data(self.get_cap_xml(), 'guest/arch/domain', 'type')

    @method_logger()
    def get_host_mem_usage(self):
        hostemem = self.wvm.getInfo()[1] * (1024**2)
        freemem = self.wvm.getMemoryStats(-1, 0)
        if isinstance(freemem, dict):
            mem = list(freemem.values())
            free = (mem[1] + mem[2] + mem[3]) * 1024
            percent = (100 - ((free * 100) / hostmem))
            usage = (hostmem - free)
            return {'size': hostmem, 'usage': usage, 'percent': round(percent)}
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
    def get_storages(self):
        storages = []
        for pool in self.wvm.listStoragePools():
            storages.append(pool)
        for pool in self.wvm.listDefinedStoragePools():
            storages.append(pool)
        return storages

    @method_logger()
    def get_storage(self, name):
        return self.wvm.storagePoolLookupByName(name)

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
    def get_networks(self):
        virtnet = []
        for net in self.wvm.listNetworks():
            virtnet.append(net)
        for net in self.wvm.listDefinedNetworks():
            virtnet.append(net)
        return virtnet

    @method_logger()
    def refresh_storages(self):
        for pool in self.wvm.listStoragePools():
            stg = self.wvm.storagePoolLookupByName(pool)
            stg.refresh()

    @method_logger()
    def get_ifaces(self):
        interface = []
        for inface in self.wvm.listInterfaces():
            interface.append(inface)
        for inface in self.wvm.listDefinedInterfaces():
            interface.append(inface)
        return interface

    @method_logger()
    def get_iface(self, name):
        return self.wvm.interfaceLookupByName(name)

    @method_logger()
    def get_secrets(self):
        return self.wvm.listSecrets()

    @method_logger()
    def get_secret(self, uuid):
        return self.wvm.secretLookupByUUIDString(uuid)

    @method_logger()
    def get_volume_by_path(self, path):
        return self.wvm.storageVolLookupByPath(path)

    @method_logger()
    def get_network(self, net):
        return self.wvm.networkLookupByName(net)

    @method_logger()
    def get_instance(self, name):
        return self.wvm.lookupByName(name)

    @method_logger()
    def get_instance_status(self, name):
        dom = self.wvm.lookupByName(name)
        return dom.info()[0]

    @method_logger()
    def get_instances(self):
        instances = []
        for inst_id in self.wvm.listDomainsID():
            dom = self.wvm.lookupByID(int(inst_id))
            instances.append(dom.name())
        for name in self.wvm.listDefinedDomains():
            instances.append(name)
        return instances

    @method_logger()
    def get_snapshots(self):
        instance = []
        for snap_id in self.wvm.listDomainsID():
            dom = self.wvm.lookupByID(int(snap_id))
            if dom.snapshotNum(0) != 0:
                instance.append(dom.name())
        for name in self.wvm.listDefinedDomains():
            dom = self.wvm.lookupByName(name)
            if dom.snapshotNum(0) != 0:
                instance.append(dom.name())
        return instance

    @method_logger()
    def get_net_device(self):
        netdevice = []
        for dev in self.wvm.listAllDevices(0):
            xml = dev.XMLDesc(0)
            if util.get_xml_data(xml, 'capability', 'type') == 'net':
                netdevice.append(util.get_xml_data(xml, 'capability/interface'))
        return netdevice

    @method_logger()
    def get_host_instances(self):
        vname = []
        for name in self.get_instances():
            dom = self.get_instance(name)
            mem = util.get_xml_data(dom.XMLDesc(0), 'currentMemory')
            mem = round(int(mem) / 1024)
            cur_vcpu = util.get_xml_data(dom.XMLDesc(0), 'vcpu', 'current')
            if cur_vcpu:
                vcpu = cur_vcpu
            else:
                vcpu = util.get_xml_data(dom.XMLDesc(0), 'vcpu')
            vname.append({'name': dom.name(), 'status': dom.info()[0], 'uuid': dom.UUIDString(), 'vcpu': vcpu, 'memory': mem})
        return vname

    @method_logger()
    def close(self):
        self.wvm.close()


class wvmStorages(wvmConnect):

    def get_storages_info(self):
        volumes = []
        storages = []
        for storage in self.get_storages():
            stg = self.get_storage(storage)
            active = bool(stg.isActive())
            s_type = util.get_xml_data(stg.XMLDesc(0), element='type')
            if active is True:
                volumes = stg.listVolumes()              
            storages.append({
                'name': storage,
                'active': active,
                'type': s_type,
                'volumes': volumes,
                'size': {
                    'total': stg.info()[1],
                    'used': stg.info()[2],
                    'free': stg.info()[3]
                },
                'autostart': bool(stg.autostart())
            })
        return storages

    def define_storage(self, xml, flag=0):
        self.wvm.storagePoolDefineXML(xml, flag)

    def create_storage_dir(self, name, target):
        xml = f"""
                <pool type='dir'>
                <name>{name}</name>
                <target>
                    <path>{target}</path>
                </target>
                </pool>"""
        self.define_storage(xml, 0)
        stg = self.get_storage(name)
        stg.create(0)
        stg.setAutostart(1)

    def create_storage_logic(self, name, source):
        xml = f"""
                <pool type='logical'>
                <name>{name}</name>
                  <source>
                    <device path='{source}'/>
                    <name>{name}</name>
                    <format type='lvm2'/>
                  </source>            
                  <target>
                       <path>/dev/{name}</path>
                  </target>
                </pool>"""
        self.define_storage(xml, 0)
        stg = self.get_storage(name)
        stg.build(0)
        stg.create(0)
        stg.setAutostart(1)

    def create_storage_ceph(self, name, pool, user, secret, host, host2=None, host3=None):
        xml = f"""
                <pool type='rbd'>
                <name>{name}</name>
                <source>
                    <name>{pool}</name>
                    <host name='{host}' port='6789'/>"""
        if host2:
            xml += f"""<host name='{host2}' port='6789'/>"""
        if host3:
            xml += f"""<host name='{host3}' port='6789'/>"""

        xml += f"""<auth username='{user}' type='ceph'>
                        <secret uuid='{secret}'/>
                    </auth>
                </source>
                </pool>"""
        self.define_storage(xml, 0)
        stg = self.get_storage(name)
        stg.create(0)
        stg.setAutostart(1)

    def create_storage_netfs(self, name, host, source, format, target):
        xml = f"""
                <pool type='nfs'>
                <name>{name}</name>
                <source>
                    <host name='{host}'/>
                    <dir path='{source}'/>
                    <format type='{format}'/>
                </source>
                <target>
                    <path>{target}</path>
                </target>
                </pool>"""
        self.define_storage(xml, 0)
        stg = self.get_storage(name)
        stg.create(0)
        stg.setAutostart(1)


class wvmStorage(wvmConnect):
    def __init__(self, pool):
        wvmConnect.__init__(self)
        self.pool = self.get_storage(pool)

    def get_name(self):
        return self.pool.name()

    def get_active(self):
        return bool(self.pool.isActive())

    def get_status(self):
        status = ['Not running', 'Initializing pool, not available', 'Running normally', 'Running degraded']
        try:
            return status[self.pool.info()[0]]
        except ValueError:
            return 'Unknown'

    def get_total_size(self):
        return self.pool.info()[1]

    def get_used_size(self):
        return self.pool.info()[3]

    def get_free_size(self):
        return self.pool.info()[3]

    def XMLDesc(self, flags):
        return self.pool.XMLDesc(flags)

    def createXML(self, xml, flags):
        self.pool.createXML(xml, flags)

    def createXMLFrom(self, xml, vol, flags):
        self.pool.createXMLFrom(xml, vol, flags)

    def define(self, xml):
        return self.wvm.storagePoolDefineXML(xml, 0)

    def is_active(self):
        return bool(self.pool.isActive())

    def get_uuid(self):
        return self.pool.UUIDString()

    def start(self):
        self.pool.create(0)

    def stop(self):
        self.pool.destroy()

    def delete(self):
        self.pool.undefine()

    def get_autostart(self):
        return bool(self.pool.autostart())

    def set_autostart(self, value):
        self.pool.setAutostart(value)

    def get_type(self):
        return util.get_xml_data(self.XMLDesc(0), element='type')

    def get_target_path(self):
        return util.get_xml_data(self.XMLDesc(0), 'target/path')

    def get_allocation(self):
        return int(util.get_xml_data(self.XMLDesc(0), 'allocation'))

    def get_available(self):
        return int(util.get_xml_data(self.XMLDesc(0), 'available'))

    def get_capacity(self):
        return int(util.get_xml_data(self.XMLDesc(0), 'capacity'))

    def get_pretty_allocation(self):
        return util.pretty_bytes(self.get_allocation())

    def get_pretty_available(self):
        return util.pretty_bytes(self.get_available())

    def get_pretty_capacity(self):
        return util.pretty_bytes(self.get_capacity())

    def get_volumes(self):
        return self.pool.listVolumes()

    def get_volume(self, name):
        return self.pool.storageVolLookupByName(name)

    def get_volume_size(self, name):
        vol = self.get_volume(name)
        return vol.info()[1]

    def _vol_XMLDesc(self, name):
        vol = self.get_volume(name)
        return vol.XMLDesc(0)

    def del_volume(self, name):
        vol = self.pool.storageVolLookupByName(name)
        vol.delete(0)

    def get_volume_type(self, name):
        return util.get_xml_data(self._vol_XMLDesc(name), 'target/format', 'type')

    def refresh(self):
        self.pool.refresh(0)

    def update_volumes(self):
        try:
            self.refresh()
        except Exception:
            pass
        vols = self.get_volumes()
        vol_list = []

        for volname in vols:
            vol_list.append({
                'name': volname,
                'size': self.get_volume_size(volname),
                'type': self.get_volume_type(volname)
            })
        return vol_list

    def create_volume(self, name, size, vol_fmt='qcow2', metadata=False):
        storage_type = self.get_type()
        alloc = size
        if vol_fmt == 'unknown':
            vol_fmt = 'raw'
        if storage_type == 'dir':
            name += '.img'
            alloc = 0
        xml = f"""
            <volume>
                <name>{name}</name>
                <capacity>{size}</capacity>
                <allocation>{alloc}</allocation>
                <target>
                    <format type='{vol_fmt}'/>
                </target>
            </volume>"""
        self.createXML(xml, metadata)

    def clone_volume(self, name, clone, vol_fmt=None, metadata=False):
        storage_type = self.get_type()
        if storage_type == 'dir':
            clone += '.img'
        vol = self.get_volume(name)
        if not vol_fmt:
            vol_fmt = self.get_volume_type(name)
        xml = f"""
            <volume>
                <name>{clone}</name>
                <capacity>0</capacity>
                <allocation>0</allocation>
                <target>
                    <format type='{vol_fmt}'/>
                </target>
            </volume>"""
        self.createXMLFrom(xml, vol, metadata)
