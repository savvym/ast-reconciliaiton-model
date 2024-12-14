from typing import Any, Self
from typing import get_origin, get_args
from typing import List
from pydantic import (
    BaseModel,
    Field,
    model_validator,
    ValidationInfo,
    ConfigDict
)

class Model(BaseModel):
    def __init__(self, /, **data: Any) -> None:
        self.__pydantic_validator__.validate_python(
            data,
            self_instance=self,
            context= {},
        )
        
    @model_validator(mode='before')
    @classmethod
    def _construct(cls, data: dict, info: ValidationInfo) -> Any:
        context = info.context
        # 初始化
        for field, value in data.items():
            context.get('id', []).append(field)
            context['field_' + field] = value
        for field_name, field_info in cls.model_fields.items():
            extra = field_info.json_schema_extra
            source = extra.get('source')
            if source['type'] == 'primary':
                # do query
                continue
            if source['type'] == 'db':
                adapter = source['adapter']
                location = extra['location']
                query = extra['query']
                ret = adapter(data[query], location)
                annotation = field_info.annotation
                if get_origin(annotation) is list:
                    element_type = get_args(annotation)[0]
                    if isinstance(ret, list):
                        for r in ret:
                            if field_name not in data:
                                data[field_name] = []
                            data[field_name].append(element_type(**{extra['key']: r}))
                else:
                    data[field_name] = annotation(ret)
                # 进行List类型的操作
        return data
db = {
    123: {
        'uLBId': 'lbxxxxx',
        'uListenerId': ['lis-1', 'lis-2'],
    },
    'lis-1': {
        "protocol": "tcp",
        "vport": 80,
        "uLocationId": ['loc-1', 'loc-2']
    },
    'lis-2': {
        "protocol": "tcp",
        "vport": 443,
        "uLocationId": ['loc-3']
    },
    'loc-1': {
        "domain": "baidu.com",
        "url": "/index"
    },
    'loc-2': {
        "domain": "baidu.com",
        "url": "/index"
    },
    'loc-3': {
        "domain": "baidu.com",
        "url": "/index"
    }
    
    
}
def db_adapter(query, location):
    return db[query][location]

class Device(Model):
    rsip: str = Field(source={'type': 'db'}, 
                      location='rsip', 
                      query='LBId')
    rsport: int = Field(source={'type': 'db'}, 
                        location='rsport', 
                        query='LBId')

class Location(Model):
    uLocationId: str = Field(source={'type': 'primary', 'adapter': db_adapter})
    domain: str = Field(source={'type': 'db', 'adapter': db_adapter}, 
                        location='domain', 
                        query='uLocationId')
    url: str = Field(source={'type': 'db', 'adapter': db_adapter}, 
                     location='url', 
                     query='uLocationId')

class Listener(Model):
    uListenerId: str = Field(source={'type': 'primary'})
    protocol: str = Field(source={'type': 'db', 'adapter': db_adapter}, 
                          location='protocol', 
                          query='uListenerId')
    vport: int = Field(source={'type': 'db', 'adapter': db_adapter}, 
                       location='vport', 
                       query='uListenerId')
    Locations: list[Location] = Field(source={'type': 'db', 'adapter': db_adapter}, 
                                      location='uLocationId', 
                                      query='uListenerId', 
                                      key='uLocationId')

class LoadBalance(Model):
    LBId: int = Field(source={'type': 'primary'})
    uLBId: str = Field(source={'type': 'db', 'adapter': db_adapter}, 
                       location='uLBId', 
                       query='LBId')
    Listeners: list[Listener] = Field(source={'type': 'db', 'adapter': db_adapter}, 
                                      location='uListenerId', 
                                      query='LBId', 
                                      key='uListenerId')
      
# d = {'rsip': '192.168.1.2', 'rsport': [1, 4]}
# d1 = Device(**d)
# d2 = Device(rsip="192.168.1.3", rsport=[1, 4], weight=10)
# loc = Location(uLocationId='uloc-1', domain='', url='', Devices=[d1, d2])
# lis = Listener(uListenerId='ulis-1', protocol='tcp', vport=80, Locations=[loc])
# lb = LoadBalance(LBId=13213, uLBId='lb-sa', vip='10.0.1.3', vpcId=32321, Listeners=[lis])
lb = LoadBalance(LBId=123)
print(lb)