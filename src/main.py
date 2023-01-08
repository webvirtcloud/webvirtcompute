import requests
from typing import Optional
from libvirt import libvirtError
from fastapi import FastAPI, Depends

from vrtmgr import libvrt
from vrtmgr import images
from vrtmgr import network
from auth import basic_auth
from helper import raise_error_msg
from settings import METRICS_URL, STORAGE_IMAGE_POOL
from model import VirtanceCreate, VirtanceStatus, VirtanceResize, VirtanceMedia
from model import StorageCreate, StorageAction, VolumeCreate, VolumeAction, NwFilterCreate
from model import NetworkCreate, NetworkAction, SecretCreate, SecretValue, FloatingIPs, ResetPassword


app = FastAPI(dependencies=[Depends(basic_auth)])


@app.get("/metrics/")
def metrics(query: Optional[str] = "", start: Optional[str] = "", end: Optional[str] = "", step: Optional[str] = ""):
    params = {"query": query, "start": start, "end": end, "step": step}
    res = requests.get(METRICS_URL, params=params).json()
    return res


@app.post("/virtances/", response_model=VirtanceCreate)
def virtance_create(virtance: VirtanceCreate):
    # Download and deploy images template
    for img in virtance.images:
        if img.get("primary") is True:
            template = images.Template(img.get("name"), img.get("md5sum"))
            err_msg, template_path = template.download(img.get("url"))
            if err_msg is None:
                image = images.Image(img.get("name"), STORAGE_IMAGE_POOL)
                err_msg = image.deploy_template(
                    template=template,
                    disk_size=img.get("size"),
                    networks=virtance.network,
                    public_keys=virtance.keypairs,
                    hostname=virtance.name,
                    root_password=virtance.root_password,
                )
        else:
            try:
                conn = libvrt.wvmStorage(STORAGE_IMAGE_POOL)
                conn.create_volume(img.get("name"), img.get("size"), fmt="raw")
                conn.close()
            except libvirtError as err:
                raise_error_msg(err)

    if err_msg is not None:
        raise_error_msg(err_msg)

    # Create XML
    try:
        conn = libvrt.wvmCreate()
        conn.create_xml(
            virtance.name, virtance.vcpu, virtance.memory, virtance.images, virtance.network, uuid=virtance.uuid
        )
        conn.close()
    except libvirtError as err:
        raise_error_msg(err)

    # Run VM
    try:
        conn = libvrt.wvmInstance(virtance.name)
        conn.start()
        conn.close()
    except libvirtError as err:
        raise_error_msg(err)

    return virtance


@app.get("/virtances/")
def virtances():
    virtances = []
    conn = libvrt.wvmConnect()
    virtance_names = conn.get_instances()
    conn.close()
    for name in virtance_names:
        dconn = libvrt.wvmInstance(name)
        virtances.append(
            {
                "name": name,
                "status": dconn.get_state(),
                "uuid": dconn.get_uuid(),
                "vcpu": dconn.get_vcpu(),
                "memory": dconn.get_memory(),
                "disks": dconn.get_disk_device(),
                "media": dconn.get_media_device(),
                "ifaces": dconn.get_net_ifaces(),
            }
        )
        dconn.close()
    return {"virtances": virtances}


@app.get("/virtances/{name}/")
def virtance_info(name):
    try:
        conn = libvrt.wvmInstance(name)
        response = {
            "name": name,
            "uuid": conn.get_uuid(),
            "vcpu": conn.get_vcpu(),
            "disks": conn.get_disk_device(),
            "media": conn.get_media_device(),
            "status": conn.get_state(),
            "memory": conn.get_memory(),
            "ifaces": conn.get_net_ifaces(),
        }
        conn.close()
    except libvirtError as err:
        raise_error_msg(err)

    return {"virtances": response}


@app.get("/virtances/{name}/status/")
def virtance(name):
    try:
        conn = libvrt.wvmInstance(name)
        status = conn.get_state()
        conn.close()
    except libvirtError as err:
        raise_error_msg(err)
    return {"status": status}


@app.post("/virtances/{name}/status/", response_model=VirtanceStatus)
def virtance_status(name, status: VirtanceStatus):

    if status.action not in ["start", "stop", "suspend", "resume"]:
        raise_error_msg("Status does not exist.")

    try:
        conn = libvrt.wvmInstance(name)
        if status.action == "start":
            conn.start()
        if status.action == "stop":
            conn.shutdown()
        if status.action == "suspend":
            conn.suspend()
        if status.action == "resume":
            conn.resume()
        conn.close()
    except libvirtError as err:
        raise_error_msg(err)

    return status


@app.post("/virtances/{name}/resize/", response_model=VirtanceResize)
def virtance_resize(name, resize: VirtanceResize):
    try:
        conn = libvrt.wvmInstance(name)
        if conn.get_state() != "shutoff":
            raise_error_msg("Please shutoff the virtual machine.")
        conn.resize_resources(resize.vcpu, resize.memory)
        if resize.disk_size:
            drivers = conn.get_disk_device()
            for drive in drivers:
                if drive.get("dev") == "vda" or drive.get("dev") == "sda":
                    sconn = libvrt.wvmStorage(drive.get("pool"))
                    sconn.resize_volume(drive.get("name"), resize.disk_size)
                    sconn.close()
        conn.close()
    except libvirtError as err:
        raise_error_msg(err)

    return resize


@app.get("/virtances/{name}/media/", dependencies=[Depends(basic_auth)])
def virtance_media_info(name):
    try:
        conn = libvrt.wvmInstance(name)
        media = conn.get_media_device()
        conn.close()
    except libvirtError as err:
        raise_error_msg(err)
    return {"media": media}


@app.post("/virtances/{name}/media/", response_model=VirtanceMedia)
def virtance_media_mount(name, media: VirtanceMedia):
    try:
        conn = libvrt.wvmInstance(name)
        conn.mount_iso(media.device, media.image)
        conn.close()
    except libvirtError as err:
        raise_error_msg(err)

    return media


@app.delete("/virtances/{name}/media/", response_model=VirtanceMedia)
def virtance_media_umount(name, media: VirtanceMedia):
    try:
        conn = libvrt.wvmInstance(name)
        conn.umount_iso(media.device, media.image)
        conn.close()
    except libvirtError as err:
        raise_error_msg(err)

    return media


@app.post("/virtances/{name}/reset_password/", response_model=ResetPassword)
def virtance_reset_password(name, reset_pass: ResetPassword):
    raise_error_msg = None

    try:
        conn = libvrt.wvmInstance(name)
        drives = conn.get_disk_device()
        conn.close()
    except libvirtError as err:
        raise_error_msg(err)

    try:
        image = images.Image(drives[0].get("name"), drives[0].get("pool"))
        err_msg = image.reset_password(reset_pass.get("distro"), reset_pass.get("password"))
    except Exception as err:
        raise_error_msg(err)

    if err_msg:
        raise_error_msg(err_msg)

    return reset_pass


@app.delete("/virtances/{name}/")
def virtance_detele(name):
    try:
        conn = libvrt.wvmInstance(name)
        drivers = conn.get_disk_device()
        for drive in drivers:
            if drive.get("dev") == "vda" or drive.get("dev") == "sda":
                sconn = libvrt.wvmStorage(drive.get("pool"))
                vol = sconn.get_volume(drive.get("name"))
                vol.delete()
                sconn.refresh()
                sconn.close()
        conn.delete()
        conn.close()
    except libvirtError as err:
        raise_error_msg(err)


@app.get("/host/")
def host():
    conn = libvrt.wvmConnect()
    hostinfo = conn.get_host_info()
    conn.close()
    return {"host": hostinfo}


@app.get("/storages/")
def storages():
    conn = libvrt.wvmStorages()
    storages = conn.get_storages_info()
    conn.close()
    return {"storages": storages}


@app.post("/storages/", response_model=StorageCreate)
def storages_list(pool: StorageCreate):
    conn = libvrt.wvmStorages()
    if pool.type == "dir":
        if pool.target is None:
            raise_error_msg("Target field required for dir storage pool.")
        try:
            conn.create_storage_dir(
                pool.name,
                pool.target,
            )
        except libvirtError as err:
            raise_error_msg(err)
    if pool.type == "logical":
        if pool.source is None:
            raise_error_msg("Source field required for dir storage pool.")
        try:
            conn.create_storage_logic(
                pool.name,
                pool.source,
            )
        except libvirtError as err:
            raise_error_msg(err)
    if pool.type == "rbd":
        if pool.source is None and pool.pool is None and pool.secret is None and pool.host is None:
            raise_error_msg("Source, pool, secret and host fields required for rbd storage pool.")
        try:
            conn.create_storage_ceph(pool.name, pool.pool, pool.user, pool.secret, pool.host, pool.host2, pool.host3)
        except libvirtError as err:
            raise_error_msg(err)
    if pool.type == "nfs":
        if pool.host is None and pool.source is None and pool.format is None and pool.target is None:
            raise_error_msg("Pool, source, source and target fields required for nfs storage pool.")
        try:
            conn.create_storage_netfs(pool.name, pool.host, pool.source, pool.format, pool.target)
        except libvirtError as err:
            raise_error_msg(err)
    conn.close()
    return pool


@app.get("/storages/{pool}/")
def storage_info(pool):
    try:
        conn = libvrt.wvmStorage(pool)
    except libvirtError as err:
        raise_error_msg(err)

    storage = {
        "name": pool,
        "active": conn.get_active(),
        "type": conn.get_type(),
        "volumes": conn.get_volumes_info(),
        "size": {"total": conn.get_total_size(), "used": conn.get_used_size(), "free": conn.get_free_size()},
        "autostart": conn.get_autostart(),
    }
    conn.close()
    return {"storage": storage}


@app.post("/storages/{pool}/", response_model=StorageAction)
def storage_action(pool, val: StorageAction):
    try:
        conn = libvrt.wvmStorage(pool)
    except libvirtError as err:
        raise_error_msg(err)

    if val.action not in ["start", "stop", "autostart", "manualstart"]:
        raise_error_msg("Action not exist.")

    if val.action == "start":
        conn.start()
    if val.action == "stop":
        conn.stop()
    if val.action == "autostart":
        conn.set_autostart(True)
    if val.action == "manualstart":
        conn.set_autostart(False)

    conn.close()
    return val


@app.delete("/storages/{pool}/")
def storage_delete(pool):
    try:
        conn = libvrt.wvmStorage(pool)
        conn.stop()
        conn.delete()
    except libvirtError as err:
        raise_error_msg(err)
    conn.close()


@app.get("/storages/{pool}/volumes/")
def storage_volume_list(pool):
    try:
        conn = libvrt.wvmStorage(pool)
    except libvirtError as err:
        raise_error_msg(err)

    volumes = conn.get_volumes_info()
    conn.close()
    return {"volumes": volumes}


@app.post("/storages/{pool}/volumes/", response_model=VolumeCreate)
def storage_volume_create(pool, volume: VolumeCreate):
    try:
        conn = libvrt.wvmStorage(pool)
        conn.create_volume(name=volume.name, size=volume.size * (1024**3), fmt=volume.format)
    except libvirtError as err:
        raise_error_msg(err)

    conn.close()
    return volume


@app.get("/storages/{pool}/volumes/{volume}/")
def storage_volume_info(pool, volume):
    try:
        conn = libvrt.wvmStorage(pool)
        vol = conn.get_volume_info(volume)
    except libvirtError as err:
        raise_error_msg(err)

    conn.close()
    return {"volume": vol}


@app.post("/storages/{pool}/volumes/{volume}/", response_model=VolumeAction)
def storage_volume_action(pool, volume, val: VolumeAction):
    try:
        conn = libvrt.wvmStorage(pool)
        conn.get_volume(volume)
    except libvirtError as err:
        raise_error_msg(err)

    if val.action not in ["resize", "clone"]:
        raise_error_msg("Action not exist.")

    if val.action == "resize":
        if not val.size:
            raise_error_msg("Size required for resize ation.")
        try:
            conn.resize_volume(val.size)
        except libvirtError as err:
            raise_error_msg(err)

    if val.action == "clone":
        if not val.name:
            raise_error_msg("Name required for clone ation.")
        try:
            conn.clone_volume(volume, val.name)
        except libvirtError as err:
            raise_error_msg(err)

    conn.close()
    return val


@app.delete("/storages/{pool}/volumes/{volume}/", status_code=204)
def storage_volume_delete(pool, volume):
    try:
        conn = libvrt.wvmStorage(pool)
        conn.del_volume(volume)
    except libvirtError as err:
        raise_error_msg(err)
    conn.close()


@app.get("/networks/")
def networks_list():
    conn = libvrt.wvmNetworks()
    networks = conn.get_networks_info()
    conn.close()
    return {"networks": networks}


@app.post("/networks/", response_model=NetworkCreate)
def network_create(net: NetworkCreate):
    conn = libvrt.wvmNetworks()
    try:
        conn.create_network(
            net.name, net.forward, net.gateway, net.mask, net.dhcp, net.bridge, net.openvswitch, net.fixed
        )
    except libvirtError as err:
        raise_error_msg(err)
    conn.close()
    return net


@app.get("/networks/{name}/")
def network_info(name):
    try:
        conn = libvrt.wvmNetwork(name)
    except libvirtError as err:
        raise_error_msg(err)

    network = {
        "name": name,
        "active": conn.get_active(),
        "device": conn.get_bridge_device(),
        "forward": conn.get_ipv4_forward()[0],
    }
    conn.close()
    return {"network": network}


@app.post("/networks/{name}/", response_model=NetworkAction)
def network_action(name, val: NetworkAction):
    try:
        conn = libvrt.wvmNetwork(name)
    except libvirtError as err:
        raise_error_msg(err)

    if val.action not in ["start", "stop", "autostart", "manualstart"]:
        raise_error_msg("Action not exist.")

    if val.action == "start":
        conn.start()
    if val.action == "stop":
        conn.stop()
    if val.action == "autostart":
        conn.set_autostart(True)
    if val.action == "manualstart":
        conn.set_autostart(False)

    conn.close()
    return {"network": network}


@app.delete("/networks/{name}/", status_code=204)
def network_delete(name):
    try:
        conn = libvrt.wvmNetwork(name)
        conn.stop()
        conn.delete()
    except libvirtError as err:
        raise_error_msg(err)
    conn.close()


@app.get("/secrets/")
def secrets_list():
    secrets_list = []
    conn = libvrt.wvmSecrets()
    for uuid in conn.get_secrets():
        secret = conn.get_secret(uuid)
        secrets_list.append(
            {
                "usage": secret.usageID(),
                "uuid": secret.UUIDString(),
                "usageType": secret.usageType(),
                "value": conn.get_secret_value(uuid),
            }
        )
    conn.close()
    return {"secrets": secrets_list}


@app.post("/secrets/", response_model=SecretCreate)
def secret_create(secret: SecretCreate):
    conn = libvrt.wvmSecrets()
    try:
        conn.create_secret(secret.ephemeral, secret.private, secret.secret_type, secret.data)
    except libvirtError as err:
        raise_error_msg(err)
    conn.close()
    return secret


@app.get("/secrets/{uuid}/")
def secret_info(uuid):
    conn = libvrt.wvmSecrets()
    try:
        secret = conn.get_secret(uuid)
    except libvirtError as err:
        raise_error_msg(err)

    secret = {
        "usage": secret.usageID(),
        "uuid": secret.UUIDString(),
        "usageType": secret.usageType(),
        "value": conn.get_secret_value(uuid),
    }
    conn.close()
    return {"secret": secret}


@app.post("/secrets/{uuid}/", response_model=SecretValue)
def secret_value(uuid, secret: SecretValue):
    conn = libvrt.wvmSecrets()
    try:
        conn.set_secret_value(uuid, secret.value)
    except libvirtError as err:
        raise_error_msg(err)

    conn.close()
    return secret


@app.delete("/secrets/{uuid}/", status_code=204)
def secret_detele(uuid):
    conn = libvrt.wvmSecrets()
    try:
        conn.delete_secret(uuid)
    except libvirtError as err:
        raise_error_msg(err)
    conn.close()


@app.get("/nwfilters/")
def nwfilters_list():
    nwfilters_list = []
    conn = libvrt.wvmNWfilter()
    nwfilters = conn.get_nwfilter()
    for nwfilter in nwfilters:
        nwfilters_list.append({"name": nwfilter, "xml": conn.get_nwfilter_xml(nwfilter)})
    conn.close()
    return {"nwfilters": nwfilters_list}


@app.post("/nwfilters/", response_model=NwFilterCreate)
def nwfilter_ctreate(nwfilter: NwFilterCreate):
    conn = libvrt.wvmNWfilter()
    try:
        conn.create_nwfilter(nwfilter.xml)
    except libvirtError as err:
        raise_error_msg(err)
    conn.close()
    return nwfilter


@app.get("/nwfilters/{name}/")
def nwfilter_info(name):
    conn = libvrt.wvmNWfilter()
    try:
        nwfilter = {"name": name, "xml": conn.get_nwfilter_xml(name)}
    except libvirtError as err:
        raise_error_msg(err)

    conn.close()
    return {"nwfilter": nwfilter}


@app.delete("/nwfilters/{name}/", status_code=204)
def nwfilter_delete(name):
    conn = libvrt.wvmNWfilter()
    try:
        conn.delete_nwfilter(name)
    except libvirtError as err:
        raise_error_msg(err)

    conn.close()


@app.post("/floating_ips/", response_model=FloatingIPs)
def floating_ip_attach(name, floating_ip: FloatingIPs):
    try:
        ip = network.FixedIP(floating_ip.fixed_address)
        err_msg = ip.attach_floating_ip(floating_ip.address, floating_ip.prefix, floating_ip.gateway)
    except Exception as err:
        raise_error_msg(err)

    if err_msg:
        raise_error_msg(err_msg)

    return floating_ip


@app.delete("/floating_ips/", response_model=FloatingIPs)
def floating_ip_detach(name, floating_ip: FloatingIPs):
    raise_error_msg = None

    try:
        ip = network.FixedIP(floating_ip.fixed_address)
        err_msg = ip.detach_floating_ip(floating_ip.address, floating_ip.prefix)
    except Exception as err:
        raise_error_msg(err)

    if err_msg:
        raise_error_msg(err_msg)

    return floating_ip
