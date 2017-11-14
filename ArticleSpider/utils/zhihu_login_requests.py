# -*-coding:utf-8-*-
import requests

try:
    import cookielib
except:
    import http.cookiejar as cookielib

import re

session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename="cookies.txt")
try:
    session.cookies.load(ignore_discard=True)
except:
    print("Cookie无法加载")

agent = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36"
headers = {
    "HOST": "www.zhihu.com",
    "Referer": "https://www.zhihu.com",
    "User-Agent": agent
}


def get_xsrf():
    # 获取xsrf code
    response = session.get("https://www.zhihu.com", headers=headers)
    # match是默认从字符串的开头匹配的，但是默认的.又不能匹配换行符造成的，使用正则的单行模式就可以了，re.S
    # 或者re.DOTALL
    match_obj = re.match('.*name="_xsrf" value="(.*?)"', response.text, re.DOTALL)
    if match_obj:
        return (match_obj.group(1))
    else:
        return ""


def is_login():
    # 通过访问个人中心判断
    inbox_url = "https://www.zhihu.com/inbox"
    response = session.get(inbox_url, headers=headers, allow_redirects=False)
    return response.status_code == 200

def get_captcha():
    import time
    t = str(int(time.time()*1000))
    captcha_url = "https://www.zhihu.com/captcha.gif?r={0}&type=login".format(t)
    t = session.get(captcha_url, headers=headers)
    with open("captcha.jpg","wb") as f:
        f.write(t.content)
        f.close()

    from PIL import Image
    try:
        im = Image.open('captcha.jpg')
        im.show()
        im.close()
    except:
        pass

    captcha = input("输入验证码\n>")
    return captcha

def zhihu_login(account, password):
    # 知乎登录
    if re.match("^1\d{10}", account):
        print("手机号码登录")
        post_url = "https://www.zhihu.com/login/phone_num"
        post_data = {
            "_xsrf": get_xsrf(),
            "phone_num": account,
            "password": password,
            "captcha": get_captcha()
        }
    else:
        if "@" in account:
            # 判断用户名是否为邮箱
            print("邮箱方式登录")
            post_url = "https://www.zhihu.com/login/email"
            post_data = {
                "_xsrf": get_xsrf(),
                "email": account,
                "password": password,
                "captcha": get_captcha()
            }
    response_text = session.post(post_url, data=post_data, headers=headers)
    session.cookies.save()


zhihu_login("15754302311", "w707194")
print(is_login())
