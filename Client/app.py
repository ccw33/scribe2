#encoding:utf-8
'''
主程序
'''
import logging
import time
import traceback

from Service import AccountService,ProxyService
from Utils import exception_utils, log_utils

import webbrowser

logger = log_utils.Log('log/debug.log', logging.DEBUG, __name__).logger

if __name__=="__main__":
    # webbrowser.open_new_tab('http://127.0.0.1:5083')
    au = ProxyService.AutoUpdater()
    i = 1
    while True:
        if AccountService.is_logined():
            is_ok,reason = au.test_ok()
            ip_port_list = []
            if not is_ok:
                try:
                    ip_port_list = au.get_useful_ip_port_from_server(reason)
                except AccountService.AccountException as e:
                    AccountService.open_login_UI(e.message)
                    break#打开登录页面后关闭程序，在登陆后再开启
                except exception_utils.ServerErrorException as e:
                    logger.error(traceback.format_exc())
            if ip_port_list:
                au.update_conf(ip_port_list)
                au.update_privoy(ip_port_list)
                au.reload()#从新加载配置文件
        else:
            AccountService.open_login_UI()
            break

        logger.info('ok----------------' + str(i))
        i = i+1
        time.sleep(AccountService.get_delaytime()*60)

