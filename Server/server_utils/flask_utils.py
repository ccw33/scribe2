#encoding

from flask import Response,request
import traceback



# ----------------------handler---------------------------
def error_500_handler(e,logger):
    '''
    错误处理
    :param e:
    :return:
    '''
    logger.error("%s - %s" % (request.args['uuid'], traceback.format_exc()))
    return Response("服务器出错，请联系管理员，请求id是：%s" % request.args['uuid'],status=500)