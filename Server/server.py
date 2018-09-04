#encoding:utf-8
import json
import logging
import traceback

import requests
import sys
from flask import Flask,render_template,Response,request

from Server.Service import fanqiang_ip_service,user_service
from Utils import  log_utils
from model.fangqiang import user


app = Flask(__name__,static_folder='static',template_folder='dist')
app.debug=True
logger = log_utils.Log('Server/log/server',logging.DEBUG if app.debug else logging.ERROR,__name__).logger


@app.route('/')
def hello_world():
    # ip_port=fanqiang_ip_service.get_random_ip_port_dict()
    # return 'Hello World! ----%s----%s' % (request.args['index'],ip_port)
    return 'Hello World'


@app.route('/get_new_ip_port',methods=['GET'])
def get_new_ip_port():
    request_id = request.args['uuid']
    reason = request.args['reason']
    account = request.args['account']
    password = request.args['password']
    try:
        # 首先测试原来的ip能不能用（防止已更新）
        # 验证用户
        vertify_pass,not_pass_reason = user_service.vertify_user(account,password)[:2]
        if not vertify_pass:
            return Response(not_pass_reason,status=401)
        # 更新并获取该用户的ip_port(ip_port已失效的情况下才会更新)
        ip_with_port_1,ip_with_port_2 = user_service.update_and_get_using_ip_port(account)
    except Exception as e:
        logger.error("%s - %s" % (request_id,traceback.format_exc()))
        return Response("服务器出错，请联系管理员，请求id是：%s" % request_id,status=500)

    return Response(json.dumps([ip_with_port_1,ip_with_port_2]))

@app.route('/get_delaytime', methods=['GET'])
def get_delaytime():
    request_id = request.args['uuid']
    account = request.args['account']
    password = request.args['password']
    try:
        delay = user_service.get_delaytime(account,password)
        return Response(str(delay))
    except Exception as e:
        logger.error("%s - %s" % (request_id,traceback.format_exc()))
        return Response("服务器出错，请联系管理员，请求id是：%s" % request_id,status=500)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'doctest':
            import doctest
            doctest.testmod()
    else:
        app.run(host='0.0.0.0', port='5083')
        # app.run(host='0.0.0.0', port='5083',ssl_context='adhoc')