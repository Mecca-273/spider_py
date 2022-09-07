import json
from datetime import datetime
from random import choice
import requests


PROXY_IP_LIST=[]


def init_proxy_pool(history):
    """
    初始化代理IP池
    @param history: 历史存留可用IP list
    """
    global PROXY_IP_LIST
    proxy_url = 'http://http.tiqu.alibabaapi.com/getip3?num=2&type=2&pack=103890&port=1&ts=1&lb=4&pb=4&gm=4&regions='
    json_str = get_url_content(proxy_url)
    proxy = json.loads(json_str)
    PROXY_IP_LIST = proxy['data'] + history
    print('有效ID ：{}'.format(["{}:{}".format(i['ip'],i['port']) for i in PROXY_IP_LIST]))


def get_proxy_ip(min_num=2):
    """
    从代理IP池随机获取一个可用IP，若不足最小个数，将进行重新获取
    @param min_num IP池保留有效IP最小个数
    """
    global PROXY_IP_LIST
    avalible = []
    for ip_info in PROXY_IP_LIST:
        expire_time = datetime.strptime(ip_info['expire_time'], '%Y-%m-%d %H:%M:%S')
        if (expire_time - datetime.now()).seconds > 2*60:
            avalible.append(ip_info)
    if len(avalible) >= min_num:
        # 更新IP
        PROXY_IP_LIST = avalible
    else:
        init_proxy_pool(avalible)
    
    use = choice(PROXY_IP_LIST)
    # "122.241.191.96:4331"
    return "{}:{}".format(use['ip'],use['port'])


def get_url_content(URL,HEADERS=({'User-Agent':
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
                    (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',\
                    'Accept-Language': 'en-US, en;q=0.5'}), TIME_OUT=30):
    """
    通过get方式获取URL返回结果（不支持异步请求）
    """
    webpage = requests.get(URL, headers=HEADERS,timeout=TIME_OUT)
    return webpage.content

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait


def init_browser(headless=True, default_proxy=None):
    """
    初始化指定代理IP浏览器
    
    @param headless 是否启用浏览器界面
    """
    PROXY = get_proxy_ip() if default_proxy is None else default_proxy
    # 设置代理IP
    webdriver.DesiredCapabilities.CHROME['proxy'] = {
        "httpProxy": PROXY,
        "ftpProxy": PROXY,
        "sslProxy": PROXY,
        "proxyType": "MANUAL"
        }
    option = webdriver.ChromeOptions()
    option.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    if headless == True:
        option.add_argument("headless")
        option.add_argument("disable-gpu")
    browser = webdriver.Chrome(options=option)
    # 用于滚动页面
    wait=WebDriverWait(browser,30)
    return browser, wait


# for i in range(100):
#     driver, wait = init_browser()
#     from selenium.webdriver.support.wait import WebDriverWait
#     from selenium.webdriver.common.by import By

#     def document_initialised(driver):
#         return driver.execute_script("return initialised")

#     driver.get("http://httpbin.org/ip")
#     WebDriverWait(driver, timeout=10).until(document_initialised)
#     print(driver.page_source)
#     el = driver.find_element(By.TAG_NAME, 'p')
#     el.text
