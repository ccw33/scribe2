#encoding:utf-8

class RoboException(Exception):
    '''
    需要机器人验证报错
    '''
    
    def __init__(self,*args,message='需要机器人验证',**kwargs):
        super(RoboException,self).__init__(*args,**kwargs)
        self.message = message


class ServerErrorException(Exception):
    '''
    服务器出错
    '''

    def __init__(self, *args, message='服务器出错', **kwargs):
        super(ServerErrorException, self).__init__(*args, **kwargs)
        self.message = message