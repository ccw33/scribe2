# encoding:utf-8
import re
import sys
import json
import logging
import multiprocessing
import traceback

from flask import Response, request, Blueprint, session, abort
import requests
from Utils import log_utils
import Conf

from Server import server_conf

logger = log_utils.Log('Server/log/server',logging.DEBUG if server_conf.is_debug_mode else logging.ERROR,__name__).logger

common_api_blueprint = Blueprint(
    'common_api',
    __name__,
    url_prefix='/api/common_api'
)

server = 'https://10.100.11.199:444/'


@common_api_blueprint.before_request
def before_request():
    if 'account' in session and request.cookies['account'] == session['account']:
        pass
    else:
        resp = Response(json.dumps({'content': '未登录'}), mimetype='application/json', status=401)
        resp.headers.extend(server_conf.Cross_Origin_Headers)
        abort(resp)

@common_api_blueprint.route('/<api_route>', methods=['GET', 'POST'])
def get_or_post(api_route):
    try:
        path = api_route.replace('.', '/')
        if path == 'api/login':
            raise Exception('此方法不能用于登录')
        query_string = request.query_string

        query_string = 'account={0}&password={1}&{2}'.format(session['account'],session['password'],
                                                             query_string)
        if request.method == 'GET':
            response = requests.get('{0}{1}?{2}'.format(server, path, query_string), verify=False)
        elif request.method == 'POST':
            response = requests.post('{0}{1}?{2}'.format(server, path, query_string), data=request.form.to_dict(),
                                     verify=False)
        else:
            raise Exception('目前只支持get和post两种方法')

        if response.status_code == 200:
            resp = Response(response.content, mimetype='application/json')
            if path=='api/EditPassword' and response.json()['errorinfo']=='success':
                session['password'] = request.args['newPassword']
        else:
            raise Exception(str(response.status_code))
    except Exception  as e:
        resp = Response(e.message, mimetype='application/text', status=500)
        logger.error(traceback.format_exc())
    resp.headers.extend(server_conf.Cross_Origin_Headers)
    return resp
