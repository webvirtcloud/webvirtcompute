import json
from auth import basic_auth
from libvirt import libvirtError
from lib import network, backup, fwall, images, libvrt
from fastapi import FastAPI, Query, Depends, HTTPException
from model import StorageCreate, StorageAction, VolumeCreate, VolumeAction, NetworkCreate, NetworkAction


app = FastAPI()


def error_msg(msg):
    raise HTTPException(status_code=400, detail=json.dumps(str(msg)))



@app.get("/host/", dependencies=[Depends(basic_auth)])
def host():
    conn = libvrt.LibVrt()
    hostinfo = conn.get_host_info()
    conn.close() 
    return {'host': hostinfo}


@app.get("/storages/", dependencies=[Depends(basic_auth)])
def storages():
    conn = libvrt.wvmStorages()
    storages = conn.get_storages_info()
    conn.close()
    return {'storages': storages}


@app.post("/storages/", response_model=StorageCreate, dependencies=[Depends(basic_auth)])
def storages(pool: StorageCreate):
    conn = libvrt.wvmStorages()
    if pool.type == 'dir':
        if pool.target is None:
            error_msg('Target field required for dir storage pool.')
        try:
            conn.create_storage_dir(
                pool.name,
                pool.target,
            )
        except libvirtError as err:
            error_msg(err)
    if pool.type == 'logical':
        if pool.source is None:
            error_msg('Source field required for dir storage pool.')
        try:
            conn.create_storage_logic(
                pool.name,
                pool.source,
            )
        except libvirtError as err:
            error_msg(err)
    if pool.type == 'rbd':
        if pool.source is None and pool.pool is None and pool.secret is None and pool.host is None:
            error_msg('Pool, secret, host fields required for rbd storage pool.')
        try:
            conn.create_storage_ceph(
                pool.name,
                pool.pool,
                pool.user,
                pool.secret,
                pool.host,
                pool.host2,
                pool.host3
            )
        except libvirtError as err:
            error_msg(err)
    if pool.type == 'nfs':
        if pool.host is None and pool.source is None and pool.format is None and pool.target is None:
            error_msg('Pool, secret, host fields required for rbd storage pool.')
        try:
            conn.create_storage_netfs(
                pool.name,
                pool.host,
                pool.source,
                pool.format,
                pool.target
            )
        except libvirtError as err:
            error_msg(err)
    conn.close()
    return pool


@app.get("/storages/{pool}/", dependencies=[Depends(basic_auth)])
def storage(pool):
    try:
        conn = libvrt.wvmStorage(pool)
    except libvirtError as err:
        error_msg(err)

    storage = {
        'name': pool,
        'active': conn.get_active(),
        'type': conn.get_type(),
        'volumes': conn.get_volumes_info(),
        'size': {
            'total': conn.get_total_size(),
            'used': conn.get_used_size(),
            'free': conn.get_free_size()
        },
        'autostart': conn.get_autostart()
    }
    conn.close()
    return {'storage': storage}


@app.post("/storages/{pool}/", response_model=StorageAction, dependencies=[Depends(basic_auth)])
def storage(pool, val: StorageAction):
    try:
        conn = libvrt.wvmStorage(pool)
    except libvirtError as err:
        error_msg(err)

    if val.action not in ['start', 'stop', 'autostart', 'manualstart']:
        error_msg('Action not exist.')
    
    if val.action == 'start':
        conn.start()
    if val.action == 'stop':
        conn.stop()
    if val.action == 'autostart':
        conn.set_autostart(True)
    if val.action == 'manualstart':
        conn.set_autostart(False)

    conn.close() 
    return val


@app.delete("/storages/{pool}/", dependencies=[Depends(basic_auth)])
def storage(pool):
    try:
        conn = libvrt.wvmStorage(pool)
        conn.stop()
        conn.delete()
    except libvirtError as err:
        error_msg(err)
    conn.close()


@app.get("/storages/{pool}/volumes/", dependencies=[Depends(basic_auth)])
def storage(pool):
    try:
        conn = libvrt.wvmStorage(pool)
    except libvirtError as err:
        error_msg(err)

    volumes = conn.get_volumes_info()
    conn.close()
    return {'volumes': volumes}


@app.post("/storages/{pool}/volumes/", response_model=VolumeCreate, dependencies=[Depends(basic_auth)])
def storage(pool, volume: VolumeCreate):
    try:
        conn = libvrt.wvmStorage(pool)
        conn.create_volume(
            name=volume.name,
            size=volume.size * (1024**3),
            fmt=volume.format
        )
    except libvirtError as err:
        error_msg(err)

    conn.close()
    return volume


@app.get("/storages/{pool}/volumes/{volume}/", dependencies=[Depends(basic_auth)])
def storage(pool, volume):
    try:
        conn = libvrt.wvmStorage(pool)
        vol = conn.get_volume_info(volume)
    except libvirtError as err:
        error_msg(err)
    
    conn.close()
    return {'volume': vol}


@app.post("/storages/{pool}/volumes/{volume}/", response_model=VolumeAction, dependencies=[Depends(basic_auth)])
def storage(pool, volume, val: VolumeAction):
    try:
        conn = libvrt.wvmStorage(pool)
        vol = conn.get_volume(volume)
    except libvirtError as err:
        error_msg(err)

    if val.action not in ['resize', 'clone']:
         error_msg('Action not exist.')

    if val.action == 'resize':
        if not val.size:
            error_msg('Size required for resize ation.')
        try:
            conn.resize_volume(val.size)
        except libvirtError as err:
            error_msg(err)

    if val.action == 'clone':
        if not val.name:
            error_msg('Name required for clone ation.')
        try:
            conn.clone_volume(volume, val.name)
        except libvirtError as err:
            error_msg(err)

    conn.close()
    return val


@app.delete("/storages/{pool}/volumes/{volume}/", status_code=204, dependencies=[Depends(basic_auth)])
def storage(pool, volume):
    try:
        conn = libvrt.wvmStorage(pool)
        vol = conn.del_volume(volume)
    except libvirtError as err:
        error_msg(err)
    conn.close()


@app.get("/networks/", dependencies=[Depends(basic_auth)])
def networks():
    conn = libvrt.wvmNetworks()
    networks = conn.get_networks_info()
    conn.close() 
    return {'networks': networks}


@app.post("/networks/", response_model=NetworkCreate, dependencies=[Depends(basic_auth)])
def networks(net: NetworkCreate):
    conn = libvrt.wvmNetworks()
    try:
        conn.create_network(
            net.name,
            net.forward,
            net.gateway,
            net.mask,
            net.dhcp,
            net.bridge,
            net.openvswitch,
            net.fixed
        )
    except libvirtError as err:
        error_msg(err)
    conn.close() 
    return net


@app.get("/networks/{name}/", dependencies=[Depends(basic_auth)])
def network(name):
    try:
        conn = libvrt.wvmNetwork(name)
    except libvirtError as err:
        error_msg(err)
    
    network = {
        'name': name,
        'active': conn.get_active(),
        'device': conn.get_bridge_device(),
        'forward': conn.get_ipv4_forward()[0]
    }
    conn.close() 
    return {'network': network}


@app.post("/networks/{name}/", response_model=NetworkAction, dependencies=[Depends(basic_auth)])
def network(name):
    try:
        conn = libvrt.wvmNetwork(name)
    except libvirtError as err:
        error_msg(err)
   
    if val.action not in ['start', 'stop', 'autostart', 'manualstart']:
        error_msg('Action not exist.')
    
    if val.action == 'start':
        conn.start()
    if val.action == 'stop':
        conn.stop()
    if val.action == 'autostart':
        conn.set_autostart(True)
    if val.action == 'manualstart':
        conn.set_autostart(False)

    conn.close() 
    return {'network': network}


@app.delete("/networks/{name}/", status_code=204, dependencies=[Depends(basic_auth)])
def network(name):
    try:
        conn = libvrt.wvmNetwork(name)
        conn.stop()
        conn.delete()
    except libvirtError as err:
        error_msg(err)
    conn.close()
