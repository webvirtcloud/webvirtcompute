import json
from auth import basic_auth
from libvirt import libvirtError
from fastapi import FastAPI, Depends, HTTPException
from lib import network, backup, fwall, images, libvrt
from lib.logger import VirtmgrdLogger, function_logger
from pydantic import BaseModel
from typing import Optional

app = FastAPI()
logger = VirtmgrdLogger()


def error_msg(msg):
    raise HTTPException(status_code=400, detail=json.dumps(str(msg)))


class AddPool(BaseModel):
    name: str
    type: str
    target: Optional[str] = None
    source: Optional[str] = None
    user: Optional[str] = None
    pool: Optional[str] = None
    host: Optional[str] = None
    host2: Optional[str] = None
    host3: Optional[str] = None
    format: Optional[str] = None
    secret: Optional[str] = None


@app.get("/host/", dependencies=[Depends(basic_auth)])
def host():
    conn = libvrt.LibVrt()
    hostinfo = conn.get_host_info()
    conn.close() 
    return {'host': hostinfo}


@app.get("/storages/", dependencies=[Depends(basic_auth)])
def storages():
    storage_list = []
    conn = libvrt.wvmStorages()
    storages = conn.get_storages_info()
    conn.close()
    return {'storages': storages}


@app.post("/storages/", response_model=AddPool, dependencies=[Depends(basic_auth)])
def storages(pool: AddPool):
    conn = libvrt.wvmStorages()
    if pool.type == 'dir':
        if pool.target is None:
            raise HTTPException(status_code=400, detail="Target field required for dir storage pool.")
        try:
            conn.create_storage_dir(
                pool.name,
                pool.target,
            )
        except libvirtError as err:
            error_msg(err)
    conn.close()
    return pool


@app.get("/storages/{name}/", dependencies=[Depends(basic_auth)])
def storage(name):
    try:
        conn = libvrt.wvmStorage(name)
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
        print(storage)
        conn.close()    
    except libvirtError as err:
        error_msg(err)
        
    return {'storage': storage}


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
