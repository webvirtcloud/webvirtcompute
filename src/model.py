from typing import Optional
from pydantic import BaseModel


class VirtanceCreate(BaseModel):
    uuid: str
    name: str
    hostname: str
    vcpu: int
    memory: int
    images: list
    network: dict
    keypairs: list
    password_hash: str


class VirtanceRebuild(BaseModel):
    hostname: str
    images: list
    network: dict
    keypairs: list
    password_hash: str


class VirtanceStatus(BaseModel):
    action: str


class VirtanceResize(BaseModel):
    vcpu: int
    memory: int
    disk_size: Optional[int] = None


class VirtanceMedia(BaseModel):
    device: str
    path: Optional[str] = None
    image: Optional[str] = None


class VirtanceSnapshot(BaseModel):
    name: str
    disk_size: Optional[int] = None


class VirtanceSnapshotReponse(BaseModel):
    size: int
    disk_size: int
    md5sum: str
    file_name: str


class StorageCreate(BaseModel):
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


class StorageAction(BaseModel):
    action: str


class VolumeCreate(BaseModel):
    name: str
    size: int
    format: Optional[str] = None


class VolumeAction(BaseModel):
    action: str
    name: Optional[str] = None
    size: Optional[int] = None


class NetworkCreate(BaseModel):
    name: str
    forward: str
    gateway: Optional[str] = None
    mask: Optional[str] = None
    dhcp: Optional[str] = None
    bridge: Optional[str] = None
    openvswitch: Optional[bool] = None
    fixed: Optional[str] = None


class NetworkAction(BaseModel):
    action: str


class SecretCreate(BaseModel):
    type: str
    data: str
    private: str
    ephemeral: str


class SecretValue(BaseModel):
    value: str


class NwFilterCreate(BaseModel):
    xml: str


class FloatingIP(BaseModel):
    fixed_ip: str
    floating_ip: str
    floating_prefix: str
    floating_gateway: str


class ResetPassword(BaseModel):
    password_hash: str


class FirewallAttach(BaseModel):
    id: int
    ipv4_public: str
    ipv4_private: str
    inbound: list
    outbound: list


class FirewallRule(BaseModel):
    inbound: list
    outbound: list


class FirewallDetach(BaseModel):
    ipv4_public: str
    ipv4_private: str
