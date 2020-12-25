from auth import basic_auth
from fastapi import FastAPI, Depends
from lib import network, backup, fwall, images, libvrt
from lib.logger import VirtmgrdLogger, function_logger


app = FastAPI()
logger = VirtmgrdLogger()


@function_logger()
def result(err_msg=None, **kwargs):
    if err_msg:
        return {'result': 'fail', 'message': err_msg.encode()}
    else:
        res = {'result': 'success'}
        if kwargs:
            res.update(kwargs)
        return res


@app.get("/host/", dependencies=[Depends(basic_auth)])
def host():
    conn = libvrt.LibVrt()
    hostinfo = conn.get_host_info()
    conn.close() 
    return {'host': hostinfo}


@app.get("/storages/", dependencies=[Depends(basic_auth)])
def storages():
    conn = libvrt.LibVrt()
    storages = conn.get_storages()
    conn.close() 
    return {'storages': storages}


@app.get("/storages/{ name }", dependencies=[Depends(basic_auth)])
def storage(name):
    conn = libvrt.LibVrt()
    hostinfo = conn.get_storages()
    conn.close() 
    return {'storage': storages}


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
