#encoding:utf-8
import json
import logging
import traceback

import requests
from flask import Flask,render_template,Response,request

from Server.Service import fanqiang_ip_service
from Utils import  log_utils


app = Flask(__name__,static_folder='static',template_folder='dist')
app.debug=True
logger = log_utils.Log('Server/log/server',logging.DEBUG if app.debug else logging.ERROR).logger


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/get_new_ip_port',methods=['GET'])
def get_lans_data():
    request_id = request.args['uuid']
    try:
        # todo 首先测试原来的ip能不能用（防止而已更新）
        # 获取当前用户使用的ip
        # 测试，如果不能用就换

        # 获取能用的ip_with_port，
        ip_with_port=fanqiang_ip_service.get_random_ip_port_dict()
    except Exception as e:
        logger.error("%s - %s" % (request_id,traceback.format_exc()))
        return Response("服务器出错，请联系管理员，请求id是：%s" % request_id,status=500)
    return Response(ip_with_port['ip_with_port'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5083')