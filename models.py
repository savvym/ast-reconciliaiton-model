from typing import Any, Self
from typing import get_origin, get_args
from typing import List
from pydantic import (
    BaseModel,
    Field,
    model_validator,
    ValidationInfo,
)

class Model(BaseModel):
    def __init__(self, /, **data: Any) -> None:
        self.__pydantic_validator__.validate_python(
            data,
            self_instance=self,
            context= data.get('context', {}),
        )
        
    @model_validator(mode='before')
    @classmethod
    def _construct(cls, data: dict, info: ValidationInfo) -> Any:
        context = info.context
        # 初始化
        print(context)
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
                    data[field_name] = []
                    element_type = get_args(annotation)[0]
                    if not ret:
                        continue
                    if isinstance(ret, list):
                        for r in ret:
                            data[field_name].append(element_type(**{extra['key']: r, "context": context}))
                else:
                    data[field_name] = annotation()
                    if not ret:
                        continue
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
        "url": "/index",
        "deviceId": ['dev-1', 'dev-2']
    },
    'loc-2': {
        "domain": "baidu.com",
        "url": "/index"
    },
    'loc-3': {
        "domain": "baidu.com",
        "url": "/index"
    }, 
    'dev-1' : {
        "rsip": "10.0.1.2",
        "rsport": 8080
    },
    'dev-2' : {
        "rsip": "10.0.1.2",
        "rsport": 8888
    }
    
    
}
def db_adapter(query, location):
    return db[query].get(location)

class Device(Model):
    deviceId: str = Field(source={'type': 'primary', 'adapter': db_adapter})
    rsip: str = Field(source={'type': 'db', 'adapter': db_adapter}, 
                      location='rsip', 
                      query='deviceId')
    rsport: int = Field(source={'type': 'db', 'adapter': db_adapter}, 
                        location='rsport', 
                        query='deviceId')

class Location(Model):
    uLocationId: str = Field(source={'type': 'primary', 'adapter': db_adapter})
    domain: str = Field(source={'type': 'db', 'adapter': db_adapter}, 
                        location='domain', 
                        query='uLocationId')
    url: str = Field(source={'type': 'db', 'adapter': db_adapter}, 
                     location='url', 
                     query='uLocationId')
    Devices: list[Device] = Field(source={'type': 'db', 'adapter': db_adapter}, 
                     location='deviceId', 
                     query='uLocationId',
                     key='deviceId')

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
      
lb = LoadBalance(LBId=123)
print(lb)