from typing import Any, Self
from typing import get_origin, get_args
from typing import List
from pydantic import (
    BaseModel,
    Field,
    model_validator,
    ValidationInfo,
)
import sqlite3
import json
from functools import cache


def extract_listener_from_l4rule(rulelist):
    listeners = []
    for one_rule in rulelist:
        rule = one_rule['rule']
        rslist = one_rule['rslist']
        listener = {
            'protocol': rule['protocol'],
            'vport': rule['vport'],
            'Locations': {"domain": "", "url": "", "Devices": rslist}
        }
        listeners.append(listener)
    return listeners

def extract_locations(locations):
    Locations = []
    for one_location in locations:
        domain = one_location['domain']
        locationlist = one_location['locationlist']
        for location in locationlist:
            rslist = location['rslist']
            url = location['url']
            Locations.append({
                'domain': domain,
                'url': url,
                'Devices': rslist
            })
    return Locations

def extract_listener_from_l7rule(rulelist):
    listeners = []
    lis_dict = {}
    for one_rule in rulelist:
        rule = one_rule['virtualservice']
        protocol = rule['fwdmode']
        if protocol.lower() in ['http', 'https']:
            vport = rule['vports'][0]
            locationlist = one_rule.get('locationlist', [])
            listener_key = (protocol, vport)
            if listener_key not in lis_dict:
                lis_dict[listener_key] = {
                    'protocol': protocol,
                    'vport': vport,
                    'Locations': [{'domain': rule['domain'], 'locationlist': locationlist}]
                }
            else:
                lis_dict[listener_key]['Locations'].append({'domain': rule['domain'], 'locationlist': locationlist})
        else:
            pass
    for lis_key, lis_info in lis_dict.items():
        lis_info['Locations'] = extract_locations(lis_info['Locations'])
        listeners.append(lis_info)
    return listeners
       
        
@cache
def get_lb(vip, vpcId):
    path = 'l7rule.json'
    with open(path, 'r') as f:
        data = json.load(f)
    if data and data['data']:
        data = data['data'][0]
    else:
        return {}
    l4rulelist = data['rulelist']
    l7rulelist = data['l7rulelist']
    l4_listener = extract_listener_from_l4rule(l4rulelist)
    l7_listener = extract_listener_from_l7rule(l7rulelist)
    l4_filter_key = []
    for listener in l7_listener:
        if listener['protocol'].lower() in ['http', 'https', 'tcp_ssl']:
            l4_filter_key.append(('tcp', listener['vport']))
        else:
            l4_filter_key.append(('udp', listener['vport']))
    l4_listener = [lis for lis in l4_listener if (lis['protocol'].lower(), lis['vport']) not in l4_filter_key]
    listeners = l4_listener + l7_listener
    if data:
        vip = l4rulelist[0]['rule']['vip']
        vpcId = l4rulelist[0]['rule'].get('vpcid', -1)
        resp = {
            'vip': vip,
            'vpcId': vpcId,
            'Listeners': listeners
        }
        return resp
    return {}            


@cache
def get_listener(vip, vpcId, protocol, vport):
    lb = get_lb(vip, vpcId)
    lis_list = lb['Listeners']
    listener = [lis for lis in lis_list 
                if lis['protocol'].lower() == protocol.lower() and lis['vport'] == vport]
    if not listener:
        return {}
    return listener[0]

@cache
def get_location(vip, vpcId, protocol, vport, domain, url):
    lis = get_listener(vip, vpcId, protocol, vport)
    if not lis:
        return {}
    loc_list = lis['Locations']
    location = [loc for loc in loc_list
                if loc['domain'].lower() == domain and loc['url'].lower() == url]
    if not location:
        return {}
    return location[0]


@cache
def get_devices(vip, vpcId, protocol, vport, domain, url, rsip, rsport):
    loc = get_location(vip, vpcId, protocol, vport, domain, url)
    if not loc:
        return {}
    devices = loc['Devices']
    rs = [rs for rs in devices
                if rs['rsip'].lower() == rsip and rs['rsport'] == rsport]
    if not rs:
        return {}
    return rs[0]

vip = "42.194.174.26"
vpcId = -1

lb = get_lb(vip, vpcId)
listener = get_listener(vip, vpcId, 'HTTPS', 5601)
location = get_location(vip, vpcId, 'HTTPS', 5601, "es-rkili2t7.kibana.tencentelasticsearch.com", "/")
rs = get_devices(vip, vpcId, 'HTTPS', 5601, "es-rkili2t7.kibana.tencentelasticsearch.com", "/", "9.99.64.9", 5601)
print(rs)
# class Model(BaseModel):
#     def __init__(self, /, **data: Any) -> None:
#         self.__pydantic_validator__.validate_python(
#             data,
#             self_instance=self,
#             context=data.get('context', {})
#         )
        
#     @model_validator(mode='before')
#     @classmethod
#     def _construct(cls, data: dict, info: ValidationInfo) -> Any:
#         context = info.context
#         for field_name, field_info in cls.model_fields.items():
#             extra = field_info.json_schema_extra
#             source = extra.get('source')
#             if source['type'] == 'primary':
#                 # do query
#                 continue
#             if source['type'] == 'db':
#                 adapter = source['adapter']
#                 location = extra['location']
#                 query = extra['query']
#                 ret = adapter(data[query], location)
#                 annotation = field_info.annotation
#                 if get_origin(annotation) is list:
#                     data[field_name] = []
#                     element_type = get_args(annotation)[0]
#                     if not ret:
#                         continue
#                     if isinstance(ret, list):
#                         for r in ret:
#                             data[field_name].append(element_type(**{extra['key']: r, "context": context}))
#                 else:
#                     data[field_name] = annotation()
#                     if not ret:
#                         continue
#                     data[field_name] = annotation(ret)
#                 # 进行List类型的操作
#         return data
# db = {
#     123: {
#         'uLBId': 'lbxxxxx',
#         'uListenerId': ['lis-1', 'lis-2'],
#     },
#     'lis-1': {
#         "protocol": "tcp",
#         "vport": 80,
#         "uLocationId": ['loc-1', 'loc-2']
#     },
#     'lis-2': {
#         "protocol": "tcp",
#         "vport": 443,
#         "uLocationId": ['loc-3']
#     },
#     'loc-1': {
#         "domain": "baidu.com",
#         "url": "/index",
#         "deviceId": ['dev-1', 'dev-2']
#     },
#     'loc-2': {
#         "domain": "baidu.com",
#         "url": "/index"
#     },
#     'loc-3': {
#         "domain": "baidu.com",
#         "url": "/index"
#     }, 
#     'dev-1' : {
#         "rsip": "10.0.1.2",
#         "rsport": 8080
#     },
#     'dev-2' : {
#         "rsip": "10.0.1.2",
#         "rsport": 8888
#     }
    
    
# }
# def db_adapter(query, location):
    
#     return db[query].get(location)

# class Device(Model):
#     deviceId: str = Field(source={'type': 'primary', 'adapter': db_adapter})
#     rsip: str = Field(source={'type': 'db', 'adapter': db_adapter}, 
#                       location='rsip', 
#                       query='deviceId')
#     rsport: int = Field(source={'type': 'db', 'adapter': db_adapter}, 
#                         location='rsport', 
#                         query='deviceId')

# class Location(Model):
#     uLocationId: str = Field(source={'type': 'primary', 'adapter': db_adapter})
#     domain: str = Field(source={'type': 'db', 'adapter': db_adapter}, 
#                         location='domain', 
#                         query='uLocationId')
#     url: str = Field(source={'type': 'db', 'adapter': db_adapter}, 
#                      location='url', 
#                      query='uLocationId')
#     Devices: list[Device] = Field(source={'type': 'db', 'adapter': db_adapter}, 
#                      location='deviceId', 
#                      query='uLocationId',
#                      key='deviceId')

# class Listener(Model):
#     uListenerId: str = Field(source={'type': 'primary'})
#     protocol: str = Field(source={'type': 'db', 'adapter': db_adapter}, 
#                           location='protocol', 
#                           query='uListenerId')
#     vport: int = Field(source={'type': 'db', 'adapter': db_adapter}, 
#                        location='vport', 
#                        query='uListenerId')
#     Locations: list[Location] = Field(source={'type': 'db', 'adapter': db_adapter}, 
#                                       location='uLocationId', 
#                                       query='uListenerId', 
#                                       key='uLocationId')

# class LoadBalance(Model):
#     LBId: int = Field(source={'type': 'primary'})
#     uLBId: str = Field(source={'type': 'db', 'adapter': db_adapter}, 
#                        location='uLBId', 
#                        query='LBId')
#     vip: str = Field(source={'type': 'db', 'adapter': db_adapter}, 
#                      location= 'vip',
#                      query='LBId', 
#                      key='vip')
#     Listeners: list[Listener] = Field(source={'type': 'db', 'adapter': db_adapter}, 
#                                       location='uListenerId', 
#                                       query='LBId', 
#                                       key='uListenerId')
      
# lb = LoadBalance(LBId=123)
# print(lb)