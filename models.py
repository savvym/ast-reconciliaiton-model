from pydantic import BaseModel


class Device(BaseModel):
    rsip: str
    rsport: int
    weight: int

class Location(BaseModel):
    uLocationId: str
    domain: str
    url: str
    Devices: list[Device]    

class Listener(BaseModel):
    uListenerId: str
    protocol: str
    vport: int
    Locations: list[Location]

class LoadBalance(BaseModel):
    LBId: int
    uLBId: str
    vip: str
    vpcId: int
    Listeners: list[Listener]
    

d1 = Device(rsip="192.168.1.2", rsport=80, weight=10)
d2 = Device(rsip="192.168.1.3", rsport=433, weight=10)
loc = Location(uLocationId='uloc-1', domain='', url='', Devices=[d1, d2])
lis = Listener(uListenerId='ulis-1', protocol='tcp', vport=80, Locations=[loc])
lb = LoadBalance(LBId=13213, uLBId='lb-sa', vip='10.0.1.3', vpcId=32321, Listeners=[lis])

import inspect

cls = lb.__class__
class_name = cls.__name__
print(f"Class: {class_name}")
attributes = inspect.getmembers(lb, lambda a: not(inspect.isroutine(a)))
for attribute_name, attribute_value in attributes:
    if not attribute_name.startswith('__'):
        print(f"  Attribute: {attribute_name} = {attribute_value}")
