# encoding:utf-8
import json
import math
import re
import traceback
import uuid
import requests
import time
import logging

from Service.AccountService import AccountException
from Utils import log_utils,exception_utils
import Conf

logger = log_utils.Log('log/debug.log', logging.DEBUG).logger
dynamic_conf = Conf.Dynamic_conf()



class AutoUpdater():

    def __init__(self):
        # self.ip_port = Conf.ip_port
        self.ip_port_list = [dynamic_conf.ip_port_1,dynamic_conf.ip_port_2]
        self.account = dynamic_conf.account
        self.password = dynamic_conf.password
        self.proxy_filt_path = dynamic_conf.proxy_filt_path
        self.proxy_type = Conf.proxy_type
        self.headers = Conf.headers

    def reload(self):
        '''
        重新加载配置文件
        :return: 
        '''
        self.__init__()

    def test_ok(self):
        '''
        测试是否能翻墙
        :return:(是否ok<Bool>,原因<String>)
        '''

        def test_and_use_bak():
            '''
            当第一个ip_port不能使用的时候，就用第二个
            :return:
            '''
            try:
                if self.ip_port_list[1]:
                    resp = requests.get('https://www.google.com/', headers=self.headers,
                                        proxies={'http': self.proxy_type + (
                                            'h' if self.proxy_type == 'socks5' else '') + '://' + self.ip_port_list[1],
                                                 'https': self.proxy_type + (
                                                     'h' if self.proxy_type == 'socks5' else '') + '://' +
                                                          self.ip_port_list[1]},
                                        timeout=10)
            except requests.exceptions.ConnectionError or requests.exceptions.ReadTimeout or requests.exceptions.SSLError as e:  # request 访问错误
                logger.debug(e.message)
            except Exception as e:
                logger.warning(traceback.format_exc())


        try:
            #-------检查配置文件
            with open(self.proxy_filt_path,'r+') as frw:
                text = frw.read()
                # 首先查看privoxy有没有配置，如果没有则配置(先给个假ip_port，后面再改)
                if not re.findall(r'forward-socks5 \/ \d+\.\d+\.\d+\.\d+\:\d+ \.\nlisten-address 0\.0\.0\.0:8118\n',text):
                    new_text = "forward-socks5 / %s .\nlisten-address 0.0.0.0:8118\n%s" % ('1.1.1.1:8080',text)
                    frw.write(new_text)

                # 查看ip_port配置是否与配置文件相同
                # 先检测一下配置文件里是否有ip_port,如果没有抛错
                if not self.ip_port_list[0]:
                    return False, '配置文件的ip_port为空'
                frw.seek(0)
                text = frw.read()
                find_res = re.findall(r'forward-socks5 \/ (\d+\.\d+\.\d+\.\d+\:\d+)',text)
                if not find_res:
                    raise Exception('请配置代理')
                if not (find_res[0] in self.ip_port_list):
                    # 如果没有使用配置文件里的ip_port就修改文件
                    new_text = text.replace(find_res[0],self.ip_port_list[0])
                    frw.seek(0)
                    frw.write(new_text)

            #-------验证两个ip_port,保证都能用
            resp = requests.get('https://www.google.com/', headers=self.headers,
                                proxies={'http': self.proxy_type + (
                                    'h' if self.proxy_type == 'socks5' else '') + '://' + self.ip_port_list[0],
                                         'https': self.proxy_type + (
                                             'h' if self.proxy_type == 'socks5' else '') + '://' + self.ip_port_list[0]},
                                timeout=10)
            # if not re.findall(r'input value=\"Google', resp.text):
            #     raise exception_utils.RoboException()
            return True,'ok'
        except requests.exceptions.ConnectionError or requests.exceptions.ReadTimeout or requests.exceptions.SSLError as e:  # request 访问错误
            test_and_use_bak()
            return False,'访问不了'
        except exception_utils.RoboException as e:
            test_and_use_bak()
            return False,e.message
        except Exception as e:
            logger.warning(traceback.format_exc())
            test_and_use_bak()
            return False,str(e)


    def get_useful_ip_port_from_server(self,reason)->list:
        # 获取有用的ip_port_list
        payload = {'uuid': uuid.uuid1(), 'reason': reason, 'account': self.account, 'password': self.password}
        resp = requests.get(Conf.server + 'get_new_ip_port', params=payload)
        if not resp.status_code == 200:
            if resp.status_code==401:
                raise AccountException(message=resp.content.decode('utf-8'))
            raise exception_utils.ServerErtrorException(resp.content.decode('utf-8'))
        ip_port_list_and_delaytime = json.loads(resp.content.decode('utf-8'))
        return ip_port_list_and_delaytime

    def update_privoy(self,ip_port_list):
        with open(self.proxy_filt_path,'r+') as frw:
            text = frw.read()
            find_res = re.findall(r'forward-socks5 \/ (\d+\.\d+\.\d+\.\d+\:\d+)', text)
            new_text = text.replace(find_res[0],ip_port_list[0])
            frw.seek(0)
            frw.write(new_text)

    def update_conf(self,ip_port_list):
        dynamic_conf.ip_port_1, dynamic_conf.ip_port_2 = ip_port_list

    def update(self,reason):
        '''
        更新配置文件
        :param reason: 
        :return: 
        '''
        # 获取有用的ip_port_list
        ip_port_list = self.get_useful_ip_port_from_server(reason)
        # 更新本地的privoxy配置文件
        self.update_privoy(ip_port_list)
        # 更新Conf.txt文件
        self.update_conf(ip_port_list)


if __name__ == "__main__":
    auto_updater = AutoUpdater()
    while True:
        auto_updater.reload()
        is_ok,reason = auto_updater.test_ok()
        if not is_ok:
            auto_updater.update(reason)
        time.sleep(120)

    # payload = {'uuid': uuid.uuid1()}
    # resp = requests.get(Conf.server + 'get_new_ip_port', params=payload)
    # content = resp.content.decode('utf-8')
    # a = 1

