from typing import Optional
from pydantic import BaseModel


class PoolAdd(BaseModel):
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


class PoolAction(BaseModel):
    action: str


class VolumeAdd(BaseModel):
    name: str
    size: int
    format: Optional[str] = None


class VolumeAction(BaseModel):
    action: str
    name: Optional[str] = None
    size: Optional[int] = None
