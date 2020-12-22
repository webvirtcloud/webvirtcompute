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


@app.get("/", dependencies=[Depends(basic_auth)])
def root():
    return {"root": "success"}

@app.get("/instances/{instance_id}/", dependencies=[Depends(basic_auth)])
def instance_item(instance_id):
    libvrt.
    return {'instance': instance_id}

