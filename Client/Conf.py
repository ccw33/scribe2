#encoding:utf-8

ip_port = '119.246.68.34:5000'
proxy_type = 'socks5'
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36"
}


server='http://localhost:5083/'


class Dynamic_conf():
    '''
    动态配置，每一次获取或设置属性都要打开配置文件Conf.txt
    '''
    
    def common_getter(self,key):
        with open('Conf.txt','r') as fr:
            for line in fr:
                line = line.strip('\n')
                if line.split('=')[0]==key:
                    return line.split('=')[1]
                
    def common_setter(self,key,value):
        with open('Conf.txt', 'r+') as frw:
            lines = frw.readlines()
            for index,line in enumerate(lines):
                if line.split('=')[0] == key:
                    lines[index] = "%s=%s\n" % (key,value)
                    break
            frw.seek(0)
            frw.writelines(lines)
            return
            # line_offset = []
            # offset = 0
            # for index,line in enumerate(frw):
            #     line_offset.append(offset)
            #     offset+=len(line)
            #     line = line.strip('\n')
            #     if line.split('=')[0]==key:
            #         frw.seek(line_offset[index])
            #         frw.write(key+'='+value+'\n')
            #         return
        # raise Exception('设置属性：%s失败，配置文件里没有改属性' % key)

    @property
    def proxy_filt_path(self):
        return self.common_getter('proxy_filt_path')

    @property
    def ip_port_1(self):
        return self.common_getter('proxy1')
    @ip_port_1.setter
    def ip_port_1(self,value):
        key = 'proxy1'
        self.common_setter(key,value)

    @property
    def ip_port_2(self):
        return self.common_getter('proxy2')
    @ip_port_2.setter
    def ip_port_2(self,value):
        key = 'proxy2'
        self.common_setter(key,value)

    @property
    def account(self):
        return self.common_getter('account')
    @account.setter
    def account(self,value):
        key = 'account'
        self.common_setter(key,value)

    @property
    def password(self):
        return self.common_getter('password')
    @password.setter
    def password(self,value):
        key = 'password'
        self.common_setter(key,value)
