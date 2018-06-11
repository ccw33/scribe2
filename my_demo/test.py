# coding:utf-8
import multiprocessing
import threading
import requests
import pymongo
from selenium import webdriver
from multiprocessing import Pool
from my_demo import utils

def test_in_chrome_driver(ip_with_port_dict):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--proxy-server=%s://%s' % (ip_with_port_dict['proxy_type'],ip_with_port_dict['ip_with_port']))
    chrome=webdriver.Chrome(executable_path='D:/geckodriver/chromedriver.exe',chrome_options=chrome_options)
    # chrome.get('http://whatismyipaddress.com')
    try:
        chrome.get('http://www.google.com')
        b = 1
    except Exception as e:
        print(e)



def test_in_webdriver(ip_with_port_dict,useful_list=None):
    driver = utils.ready(
        {'proxy_type': ip_with_port_dict['proxy_type'], 'ip_with_port': ip_with_port_dict['ip_with_port']})
    try:
        driver.get('http://www.google.com/')
    except Exception as e:
        print(str(ip_with_port_dict) + '  ' + str(e))
        driver.quit()
        return
    tags = utils.wait_and_get_elements_until_ok(driver, 'input#lst-ib')
    if not tags:
        print(str(ip_with_port_dict) + '  no tags')
        driver.quit()
        return
    print('OK  ' + str(ip_with_port_dict))
    driver.quit()
    if isinstance(useful_list,dict):
        useful_list.append(ip_with_port_dict)
    else:
        return ip_with_port_dict

def test_in_request(ip_with_port_dict):
    print("begin %s" % ip_with_port_dict)
    try:
        resp = requests.get('http://www.google.com', headers=headers,
                     proxies={'http': ip_with_port_dict['proxy_type'] +('h' if  ip_with_port_dict['proxy_type']=='socks5' else '') + '://' + ip_with_port_dict['ip_with_port'],
                              'https': ip_with_port_dict['proxy_type'] +('h' if  ip_with_port_dict['proxy_type']=='socks5' else '') + '://' + ip_with_port_dict['ip_with_port']},timeout=10)
    except Exception as e:
        print(str(ip_with_port_dict)+'  '+ str(e))
        return
    if not resp.status_code==200:
        print(str(ip_with_port_dict) + str(resp.status_code))
        return
    print('OK  '+ str(ip_with_port_dict))


def test_profile(ip_with_port_dict):
    profile = webdriver.FirefoxProfile()
    profile.set_preference("network.proxy.type",1)
    if ip_with_port_dict['proxy_type'] == 'http':
        profile.set_preference("network.proxy.http",ip_with_port_dict['ip_with_port'].split(':')[0])
        profile.set_preference("network.proxy.http_port",int(ip_with_port_dict['ip_with_port'].split(':')[1]))
    else:
        profile.set_preference('network.proxy.socks', ip_with_port_dict['ip_with_port'].split(':')[0])
        profile.set_preference('network.proxy.socks_port', int(ip_with_port_dict['ip_with_port'].split(':')[1]))
    profile.update_preferences()

    driver = webdriver.Firefox(executable_path='D:/geckodriver/geckodriver.exe',firefox_profile=profile)
    driver.get("http://whatismyipaddress.com")



s = 'abc'
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36"
}
url = 'https://www.google.com/'
# url = 'https://www.baidu.com/'
proxy_type = 'socks5'
ip_with_port = '35.187.215.227:2016'
# ip_with_port = '114.43.183.208:1080'
if __name__ == '__main__':

    client = pymongo.MongoClient('localhost', 27017)
    ips = client['ips']
    ipsData = ips['ipsData']
    ipsFanqiangData = ips['ipsFanqiangData']
    ip_fanqiang_list = list(ipsFanqiangData.find())[-1]['ip_fanqiang_list']
    #
    # # ip_list = list(ipsData.find())[-1]['ip_list']
    # # ip_list = [ip for ip in ip_list if not ip['proxy_type'] == 'socks4']
    # # ipsData.update_one({'_id':list(ipsData.find())[-1]['_id']},{'$set':{'ip_list':ip_list}})
    #
    # a = list(ipsData.find())[-1]
    # ip_list = a['ip_list']
    # socks5 = [ip['ip_with_port'] for ip in ip_list if ip['proxy_type'] == 'socks5']
    # useful_ip = []
    # useful = []
    # for ip_with_port_dict in ip_fanqiang_list:
    #     get_useful_ip(ip_with_port_dict['ip_with_port'], useful_ip, useful,
    #                                         ip_with_port_dict['proxy_type'])

    ip_list = list(ipsData.find())[-1]['ip_list']
    ip_fanqiang_list = list(ipsFanqiangData.find())[-1]['ip_fanqiang_list']

    ip_with_port_dict = {'proxy_type':'socks5','ip_with_port':'75.97.107.190:25326'}

    # ip_with_port_dict = {'proxy_type': 'http', 'ip_with_port': '210.5.149.43:8090'}

    # test_in_chrome_driver(ip_with_port_dict)
    # test_profile(ip_with_port_dict)
    # test_in_webdriver(ip_with_port_dict)
    # test_in_request(ip_with_port_dict)


    threads=[]
    for ip_with_port_dict in ip_fanqiang_list:
        t = threading.Thread(target=test_in_request,args=(ip_with_port_dict,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    # useful_list=[]
    # threads=[]
    # for ip_with_port_dict in ip_fanqiang_list:
    #     if not ip_with_port_dict['proxy_type'] == 'socks5':
    #         continue
    #     t = threading.Thread(target=test_in_webdriver,args=(ip_with_port_dict,useful_list))
    #     t.start()
    #     threads.append(t)
    # for t in threads:
    #     t.join()




    # threads = []
    # for ip_with_port_dict in ip_list[:10]:
    #     t = threading.Thread(target=test_in_request, args=(ip_with_port_dict,))
    #     t.start()
    #     threads.append(t)
    # for t in threads:
    #     t.join()


    # useful_list = []
    # asy_list = []
    # pool = Pool()
    # for ip_with_port_dict in [ip for ip in ip_list if ip['proxy_type']=='socks5']:
    #     asy_list.append( pool.apply_async(test_in_webdriver,args=(ip_with_port_dict,)))
    # pool.close()
    # pool.join()
    # useful_list =[asy.get() for asy in asy_list if asy.get()]
    #
    # ipsFanqiangData.update_one({'_id': list(ipsFanqiangData.find())[-1]['_id']}, {'$set': {'ip_fanqiang_list': useful_list}})

    a = 1
