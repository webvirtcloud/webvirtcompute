from auth import basic_auth
from fastapi import FastAPI, Depends
from lib import network, backup, fwall, images
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


@app.get("/", dependencies=[Depends(basic_auth)])
def root():
    return {"root": "success"}

@app.get("/instances/", dependencies=[Depends(basic_auth)])
def create_item():
    return {'get': 'test'}

@app.post("/instances/", dependencies=[Depends(basic_auth)])
def create_item():
    return {'post': 'test'}

@app.get("/instances/{instance_id}/", dependencies=[Depends(basic_auth)])
def create_item(instance_id):
    return {'get': instance_id}

@app.post("/instances/{instance_id}/", dependencies=[Depends(basic_auth)])
def create_item(instance_id):
    return {'post': instance_id}

@app.delete("/instances/{instance_id}/", dependencies=[Depends(basic_auth)])
def create_item(instance_id):
    return {'post': instance_id}

@app.post("/floating_ips/{foating_ip}", dependencies=[Depends(basic_auth)])
def create_item(foating_ip):
    return {'get': foating_ip}

@app.delete("/floating_ips/{foating_ip}", dependencies=[Depends(basic_auth)])
def create_item():
    return {'get': foating_ip}
