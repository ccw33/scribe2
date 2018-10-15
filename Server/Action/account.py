# encoding:utf-8

import json
import logging
import traceback

from flask import Response, request, Blueprint, session, abort
import requests
from Utils import log_utils
from Server import server_conf

logger = log_utils.Log('Server/log/server',logging.DEBUG if server_conf.is_debug_mode else logging.ERROR,__name__).logger


account_blueprint = Blueprint(
    'account',
    __name__,
    url_prefix='/account'
)


@account_blueprint.route('/login', methods=['GET'])
def login():
    try:
        session['account'] = request.args.to_dict()['account']
        session['password'] = request.args.to_dict()['password']
    except Exception  as e:
        resp = Response(e.message, mimetype='application/text', status=500)
        logger.error(traceback.format_exc())
    resp.headers.extend(server_conf.Cross_Origin_Headers)
    return resp


@account_blueprint.route('/logout', methods=['GET'])
def logout():
    try:
        resp = Response(json.dumps({'content': '登出成功'}), mimetype='application/json', status=200)
        session.pop('account', None)
        session.pop('password', None)
        session.pop('dynamicPass', None)
        resp.set_cookie('account', '')
    except Exception  as e:
        resp = Response(json.dumps(e.message, mimetype='application/text', status=500))
        logger.error(traceback.format_exc())
    resp.headers.extend(server_conf.Cross_Origin_Headers)
    return resp

