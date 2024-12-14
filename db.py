import sqlite3

conn = sqlite3.connect('clb.db')
def create_table():
    cursor = conn.cursor()
    cursor.execute('create table cLoadBalance (\
                LBId int primary key, \
                uLBId varchar(32) not null, \
                LBType varchar(32) not null, \
                vpcId int not null default 0)')
    cursor.execute('create table cLBListener (\
                id int primary key, \
                uListenerId varchar(32) not null, \
                LBId int not null, \
                protocol varchar(32) not null, \
                vport int not null default 0)')
    cursor.execute('create table cLBListenerLocation (\
                id int primary key, \
                uLocationId varchar(32) not null, \
                uListenerId varchar(32) not null, \
                domain varchar(32) not null, \
                url varchar(32) not null)')
    cursor.execute('create table cLBLocationDevice (\
                deviceId int primary key, \
                uLocationId varchar(32) not null, \
                rsip varchar(32) not null, \
                rsport int not null)')
    
def insert_lb():
    cursor = conn.cursor()
    cursor.execute('insert into cLoadBalance (LBId, uLBId, LBType, vpcId) values (1, "lb-test1", "internal", 11132)')
    
def insert_lis():
    cursor = conn.cursor()
    cursor.execute('insert into cLBListener (id, uListenerId, LBId, protocol, vport) values (1, "lis-test1", 1, "tcp", 80)')
    cursor.execute('insert into cLBListener (id, uListenerId, LBId, protocol, vport) values (2, "lis-test2", 1, "tcp", 433)')
    

# create_table()
# insert_lb()
# insert_lis()

# conn.commit()
# conn.close()
def query_from(table_name, query):
    cursor = conn.cursor()
    where_cond = '1'
    for k, v in query.items():
        where_cond += f' and `{k}` = \'{v}\''
    sql = f'select * from `{table_name}` where {where_cond}'
    record = cursor.execute(sql)
    for row in record:
        print(row)
    
query_from('cLoadBalance', {'uLBId': 'lb-test1'})
