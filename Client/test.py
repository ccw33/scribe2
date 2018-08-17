#encoding:utf-8
import asyncio
import datetime

import requests

from Service.ProxyService import AutoUpdater
import Conf

au = AutoUpdater()


async def send_request(index):
    print('sended--' + str(index))
    resp = requests.get(Conf.server, params={'index': index})
    print(resp.content.decode('utf-8')+'--------------------'+datetime.datetime.now().time().strftime('%H:%M:%S'))

loop = asyncio.get_event_loop()
tasks = [send_request(i) for i in range(20)]
loop.run_until_complete(asyncio.wait(tasks))
loop.close()


# def send_request2(index):
#     print('sended--' + str(index))
#     resp = requests.get(Conf.server, params={'index': index})
#     print(resp.content.decode('utf-8')+'--------------------'+datetime.datetime.now().time().strftime('%H:%M:%S'))
#
# ts=[]
# for i in range(20):
#     t = threading.Thread(target=send_request2,args=(i,))
#     t.start()
# for t in ts:
#     t.join()

# try:
#     raise Exception('hahaha')
# except Exception as e:
#     print(e.args[0])