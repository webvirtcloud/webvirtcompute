import json
from auth import basic_auth
from libvirt import libvirtError
from lib import network, backup, fwall, images, libvrt
from fastapi import FastAPI, Query, Depends, HTTPException
from model import PoolAdd, PoolAction, VolumeAdd, VolumeAction


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


@app.post("/storages/", response_model=PoolAdd, dependencies=[Depends(basic_auth)])
def storages(pool: PoolAdd):
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
        'name': name,
        'active': conn.get_active(),
        'type': conn.get_type(),
        'volumes': conn.get_volumes(),
        'size': {
            'total': conn.get_total_size(),
            'used': conn.get_used_size(),
            'free': conn.get_free_size()
        },
        'autostart': conn.get_autostart()
    }
    conn.close()
    return {'storage': storage}


@app.post("/storages/{pool}/", response_model=PoolAction, dependencies=[Depends(basic_auth)])
def storage(pool, val: PoolAction):
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
        conn.delete()
    except libvirtError as err:
        error_msg(err)

    conn.close()
    return volume


@app.get("/storages/{pool}/volumes/", dependencies=[Depends(basic_auth)])
def storage(pool):
    try:
        conn = libvrt.wvmStorage(pool)
    except libvirtError as err:
        error_msg(err)

    volumes = conn.get_volumes_info()
    conn.close()
    return {'volumes': volumes}


@app.post("/storages/{pool}/volumes/", response_model=VolumeAdd, dependencies=[Depends(basic_auth)])
def storage(pool, volume: VolumeAdd):
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


@app.delete("/storages/{pool}/volumes/{volume}/", dependencies=[Depends(basic_auth)])
def storage(pool, volume):
    try:
        conn = libvrt.wvmStorage(pool)
        vol = conn.del_volume(volume)
    except libvirtError as err:
        error_msg(err)
    
    conn.close()
    return {'volume': vol}


@app.get("/networks/", dependencies=[Depends(basic_auth)])
def networks():
    conn = libvrt.LibVrt()
    networks = conn.get_networks()
    conn.close() 
    return {'networks': networks}


@app.get("/networks/{ name }", dependencies=[Depends(basic_auth)])
def network(name):
    conn = libvrt.LibVrt()
    networks = conn.get_networks()
    conn.close() 
    return {'network': networks}
