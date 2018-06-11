#coding:utf-8
import datetime
import queue
import re

import time

from my_demo import utils
import pymongo
import threading



exitFlag = False

def queue_threads_worker(q,func):
    while not exitFlag:
        try:
            data = q.get(timeout=2)#获取任务（其实就是需要处理的数据/传递给func的参数）
            func(*data[0],**data[1])
        except queue.Empty:#如果过了2秒还没有获得新任务，回去看一下是否已经all_done
            continue
        q.task_done()#任务完成，告诉q一声
#打开数据库


#读取txt并存进数据库
def readTxtAndSaveToMongo(file_path,mongo_path):
    if len(mongo_path.split('.'))<2:
        raise Exception('momngo_path必须是这种形式：”ips.ipsData“')

    client = pymongo.MongoClient('localhost', 27017)

    try:
        database = client[mongo_path.split('.')[0]]
        collection = database[mongo_path.split('.')[1]]
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as fr:
            proxy_text = fr.read()
            ip_with_port_list = re.findall(r'.+?(?=\n)', proxy_text)

            # new_useful_ip_list = []
            # q = queue.Queue()
            # for i in range(20):
            #     t = threading.Thread(target=queue_threads_worker,
            #                          args=(q, utils.get_useful_ip))
            #     t.start()
            # for ip_with_port in ip_with_port_list:
            #     q.put(((ip_with_port, 'socks5', None, new_useful_ip_list), {}))
            #
            # q.join()
            # exitFlag = True

            threads = []
            new_useful_ip_list = []
            for ip_with_port in ip_with_port_list:
                thread=threading.Thread(target=utils.get_useful_ip,
                                        args=(ip_with_port,'socks5',None,new_useful_ip_list))
                thread.start()
                threads.append(thread)
            for thread in threads:
                thread.join()

            utils.logger.info(new_useful_ip_list)
            old_data = list(collection.find())[-1]
            old_ip_fanqiang_list = old_data['ip_fanqiang_list']
            old_ip_fanqiang_list.extend(new_useful_ip_list)
            ip_fanqiang_list = list(set([utils.HashableDict(ip) for ip in old_ip_fanqiang_list]))  # 去重
            collection.update_one({'_id': list(collection.find())[-1]['_id']}, {'$set': {
            'updated_at': time.strftime('%Y-%m-%d'),
            'ip_fanqiang_list': ip_fanqiang_list,
            'isFanqiang': True
        }}, upsert=True)

    finally:
        client.close()



if __name__ == "__main__":
    start = datetime.datetime.now()
    readTxtAndSaveToMongo('../file/proxies4.txt','ips.ipsFanqiangData')
    utils.logger.info('总共花费时间：' + str((datetime.datetime.now() - start).seconds) + '秒')
    # get_location('183.62.251.45')