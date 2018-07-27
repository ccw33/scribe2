# encoding:utf-8
import pymongo
import time

client = pymongo.MongoClient('localhost', 27017)

support_transication = client.server_info()['versionArray'][0] >= 4


class Base():
    '''
    collection的模型
    '''
    db_name = ''
    collection_name = ''
    template = {}

    def __init__(self):
        '''
        初始化数据库
        '''
        self.db = client[self.db_name]
        self.collection = self.db[self.collection_name]
        if not self.db_name or not self.collection_name or not self.template:
            raise Exception('缺少定义 self.db_name 或 self.collection_name 或 self.template')

    def validate_data(self, data,template={}):
        if not template:
            template = self.template
        for k, v in template.items():
            if k not in data:
                raise Exception('数据不符合 %s,缺少 %s ' % (str(template), k))
            if type(v)==dict or type(v)==list:
                self.validate_data(data[k],v)
            else:
                if not type(data[k]) == v:
                    raise Exception(
                        '数据不符合 %s,%s 的类型是 %s，而需要的是%s ' % (str(template), k, type(data[k]).__name__, v.__name__))

    def validate_data_partly(self,data,template={}):
        if not template:
            template = self.template
        for k,v in data.items():
            if k not in template:
                if not k == '_id':
                    raise Exception('原数据定义没有这个字段 %s' % k)
            if type(template[k]) == dict or type(template[k]) == list:
                self.validate_data_partly(v,template[k])
            if not type(v) == template[k]:
                raise Exception(
                    '数据不符合 %s,%s 的类型是 %s，而需要的是%s ' % (str(template), k, type(v).__name__, template[k].__name__))

    def save(self, data):
        '''
        保存一条数据
        :param data: 要插入的数据
        :type data: dict
        :return:
        '''
        self.validate_data(data)
        if support_transication:
            with client.start_session() as session:
                with session.start_transaction():
                    data['updated_at'] = time.strftime('%Y-%m-%d')
                    data['created_at'] = time.strftime('%Y-%m-%d')
                    self.collection.insert_one(data, session=session)
        else:
            data['updated_at'] = time.strftime('%Y-%m-%d')
            data['created_at'] = time.strftime('%Y-%m-%d')
            self.collection.insert_one(data)

    def save_multiple(self, data_list):
        '''
        保存多条数据
        :param data_list: 多条数据的list 如[{},{},{}]
        :return:
        '''
        if support_transication:
            with client.start_session() as session:
                with session.start_transaction():
                    for data in data_list:
                        self.validate_data(data)
                        data['updated_at'] = time.strftime('%Y-%m-%d')
                    self.collection.insert_many(data_list, session=session)
        else:
            for data in data_list:
                self.validate_data(data)
                data['updated_at'] = time.strftime('%Y-%m-%d')
            self.collection.insert_many(data_list)

    def delete(self, filter):
        '''
        删除一条数据
        :param filter: 如{'_id': ’1‘}
        :return:
        '''
        if support_transication:
            with client.start_session() as session:
                with session.start_transaction():
                    self.collection.delete_one(filter, session=session)
        else:
            self.collection.delete_one(filter)

    def update(self, data, filter={}, upsert=False):
        '''
        更新或插入一条数据
        :param data: 要更新的数据
        :param filter: 根据filter找出原数据，如果没有给filter，默认根据id
        :param upsert: 如果为True 当找不到相应数据的时候，默认False
        :return:
        '''
        self.validate_data_partly(data)
        if support_transication:
            with client.start_session() as session:
                with session.start_transaction():
                    data['updated_at'] = time.strftime('%Y-%m-%d')
                    self.collection.update_one(filter if filter else {'_id': data['_id']}, {'$set': data},
                                               upsert=upsert, session=session)
        else:
            data['updated_at'] = time.strftime('%Y-%m-%d')
            self.collection.update_one(filter if filter else {'_id': data['_id']}, {'$set': data}, upsert=upsert)

    def query(self, filter={}):
        '''
        查找
        :param filter:如{{'_id': ’1‘}}
        :return: Cursor
        '''
        if support_transication:
            with client.start_session() as session:
                with session.start_transaction():
                    return self.collection.find(filter, session=session)
        else:
            return self.collection.find(filter)
