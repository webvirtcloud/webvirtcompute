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
