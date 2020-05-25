import requests
from urllib.parse import urlencode
from lxml import etree
from config import headers,Cookie
import os
import time
from bs4 import BeautifulSoup
import base64
import re
import urllib
import json
import rsa
import binascii
from datetime import timedelta
import datetime
from requests.packages.urllib3.connectionpool import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Referer': 'https://weibo.com/?sudaref=www.baidu.com&display=0&retcode=6102',
    'Connection': 'keep-alive'
}


class Login(object):
    session = requests.session()
    user_name = "微博账号"
    pass_word = "微博密码"

    def get_username(self):
        # request.su = sinaSSOEncoder.base64.encode(urlencode(username));
        return base64.b64encode(urllib.parse.quote(self.user_name).encode("utf-8")).decode("utf-8")

    def get_pre_login(self):
        # 取servertime, nonce,pubkey
        # int(time.time() * 1000)
        params = {
            "entry": "weibo",
            "callback": "sinaSSOController.preloginCallBack",
            "su": self.get_username(),
            "rsakt": "mod",
            "checkpin": "1",
            "client": "ssologin.js(v1.4.19)",
            "_": int(time.time() * 1000)
        }
        try:
            response = self.session.post("https://login.sina.com.cn/sso/prelogin.php", params=params, headers=header,
                                         verify=False)
            return json.loads(re.search(r"\((?P<data>.*)\)", response.text).group("data"))
        except:
            print("获取公钥失败")
            return 0

    def get_password(self):
        # RSAKey.setPublic(me.rsaPubkey, "10001");
        # password = RSAKey.encrypt([me.servertime, me.nonce].join("\t") + "\n" + password)
        public_key = rsa.PublicKey(int(self.get_pre_login()["pubkey"], 16), int("10001", 16))
        password_string = str(self.get_pre_login()["servertime"]) + '\t' + str(
            self.get_pre_login()["nonce"]) + '\n' + self.pass_word
        return binascii.b2a_hex(rsa.encrypt(password_string.encode("utf-8"), public_key)).decode("utf-8")

    def login(self):

        post_data = {
            "entry": "weibo",
            "gateway": "1",
            "from": "",
            "savestate": "7",
            "qrcode_flag": "false",
            "useticket": "1",
            "vsnf": "1",
            "su": self.get_username(),
            "service": "miniblog",
            "servertime": self.get_pre_login()["servertime"],
            "nonce": self.get_pre_login()["nonce"],
            "pwencode": "rsa2",
            "rsakv": self.get_pre_login()["rsakv"],
            "sp": self.get_password(),
            "sr": "1536*864",
            "encoding": "UTF-8",
            "prelt": "529",
            "url": "https://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack",
            "returntype": "TEXT"
        }

        login_data = self.session.post("https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.18)",
                                       data=post_data, headers=header, verify=False)
        params = {
            "ticket": login_data.json()['ticket'],
            "ssosavestate": int(time.time()),
            "callback": "sinaSSOController.doCrossDomainCallBack",
            "scriptId": "ssoscript0",
            "client": "ssologin.js(v1.4.19)",
            "_": int(time.time() * 1000)
        }
        self.session.post("https://passport.weibo.com/wbsso/login", params=params, verify=False, headers=header)
        return self.session


login = Login()
session = login.login()

def change_time(start_time, end_time):
    t = timedelta(hours=1)
    start_time = start_time + t
    end_time = end_time + t
    return start_time, end_time


def get_page_session(url):
    time.sleep(5)
    return session.post(
        url,
        verify=False, headers=header)
def get_page_res(url):
    try:
        return get_page_session(url)
    except:
        try:
            return get_page_session(url)
        except:
            print("获取页码信息失败")
            return 0



if __name__ == '__main__':
    proxy = {'https':"111.47.154.34:53281"}
    path = 'Covid-19' + os.path.sep
    url = 'https://s.weibo.com/weibo?'
    start_time = datetime.datetime(2020,3,12,18)
    end_time = datetime.datetime(2020,3,12,19)
    for i in range(0,2000):
        #initial_time.strftime("%Y-%m-%d-%H")  #字符串
        scope = 'timescope=custom:' + start_time.strftime("%Y-%m-%d-%H") + ":" + end_time.strftime("%Y-%m-%d-%H")
        params = {
            'q': '新冠肺炎',
            'scope': 'ori',
        }
        weibo_url = 'https://s.weibo.com/weibo?' + urlencode(params) + '&' + scope
        response = get_page_res(weibo_url)
        if response.status_code == 200:
            html = etree.HTML(response.text)
            pages = html.xpath('//ul[@class="s-scroll"]/li')
            id_list = []
            for i in range(1,len(pages)+1):
                url = weibo_url + "&page=" + str(i)
                response = session.post(url, verify=False, headers=header)
                time.sleep(0.5)
                if response.status_code == 200:
                    re = etree.HTML(response.text)
                    id = html.xpath('//div/@mid')
                    id_list = id_list + id
                else:
                    print('访问不成功，状态码为',response.status_code)
                time.sleep(1)
            #time.sleep(10)
            folder_path = path + os.path.sep + start_time.strftime("%Y-%m")
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            with open(folder_path + os.path.sep + start_time.strftime("%Y-%m-%d-%H") + '.txt', 'a+', encoding='utf-8') as f:
                for id in id_list:
                    f.write(str(id) + '\n')
            print(id_list)
            print(len(id_list))
            start_time, end_time = change_time(start_time, end_time)
            print('start_time: ',start_time)
            print('end_time', end_time)
        else: print('访问不成功，状态码为：',response.status_code)
