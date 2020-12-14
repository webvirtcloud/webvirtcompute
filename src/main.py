from fastapi import FastAPI, Depends
from auth import basic_auth


app = FastAPI()


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
