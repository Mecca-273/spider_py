import json
from datetime import datetime
from random import choice
import requests


PROXY_IP_LIST=[]
RETRY_PROXY_TIMES = 3
RETRY_TIME = 0


def get_url_content(URL,HEADERS=({'User-Agent':
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
                    (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',\
                    'Accept-Language': 'en-US, en;q=0.5'}), TIME_OUT=30, proxy_ip_port=None):
    """
    通过get方式获取URL返回结果（不支持异步请求）

    @param proxy_ip_port ,格式：ip:port
    """
    if proxy_ip_port is not None:
        proxy={
            'http': proxy_ip_port
        }
    else:
        proxy = None
    webpage = requests.get(URL, headers=HEADERS,timeout=TIME_OUT,proxies=proxy)
    return webpage.content


def get_proxy_list_history():
    """
    获取历史已有代理ip
    """
    import json
    f = open('/Users/mecca.zhang/Projects/spider_py/proxy_ip_history.txt')
    iplist = []
    for i in f.readlines():
        if len(i)>10:
            info = json.loads(i)
            iplist.append("{}:{}".format(info['ip'], info['port']))
    return iplist


def proxy_valid():
    """
    代理IP可用性测试
        用于测试已有代理IP是否可用
    """
    import re
    pattern = re.compile('((\d+\.){3}\d+.*?)<') 
    ip_list = get_proxy_list_history()
    for i in ip_list:
        try:
            content=str(get_url_content('http://www.ip111.cn/',proxy_ip_port=i).decode("utf-8"))
            print(i,'访问成功')
        except:
            print(i,'失效')
            continue
        if 'Auth Failed' not in content:
            s= pattern.search(content)
            print(i,s.group(1))
        else:
            print("授权失败")


def taiyang_proxy():
    """
    太阳http代理IP池获取
    """
    # proxy_url = 'http://http.tiqu.alibabaapi.com/getip3?num=2&type=2&pack=103890&port=1&ts=1&lb=4&pb=4&gm=4&regions='
    proxy_url = 'http://http.tiqu.alibabaapi.com/getip3?num=2&type=2&pack=103998&port=1&ts=1&lb=1&pb=4&gm=4&regions='
    json_str = get_url_content(proxy_url)
    proxy = json.loads(json_str)
    if 'msg' in proxy.keys() and proxy['msg']=='您的该套餐已经过期了':
        print(proxy['msg'],'程序终止')
        exit(0)
    return [{"ip":i['ip'],"port":i['port'], "expire_time":i['expire_time']} for i in proxy['data']]


def init_proxy_pool(history, proxy_source=taiyang_proxy):
    """
    初始化代理IP池
    @param history: 历史存留可用IP list
    """
    global PROXY_IP_LIST
    ip_list = proxy_source()
    PROXY_IP_LIST = ip_list + history
    if len(PROXY_IP_LIST) > 0:
        with open('proxy_ip_history.txt','a+') as f:
            try:
                f.write("\n".join([json.dumps(i) for i in ip_list])+'\n')
                print('代理IP写入完成')
            except Exception as e:
                print('代理IP写入失败')
                print(e)
            finally:
                f.close()
        print('有效ID ：{}'.format(["{}:{}".format(i['ip'],i['port']) for i in PROXY_IP_LIST]))
    else:
        print('代理IP获取失败')
        global RETRY_TIME
        if RETRY_TIME < RETRY_PROXY_TIMES:
            RETRY_TIME +=1 
            init_proxy_pool([])
        else:
            print("{}次获取代理IP失败，程序终止".format(RETRY_TIME))
            exit(0)


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


def delete_ip(ip_port):
    """
        删除重试3次以上仍无法使用的代理ip
    """
    global PROXY_IP_LIST
    if ip_port is None:
        pass
    else:
        ip = ip_port.split(':')[0]
        l = len(PROXY_IP_LIST)
        for i in range(l):
            if PROXY_IP_LIST[i]['ip'] == ip:
                del PROXY_IP_LIST[i]
                break


from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException


def init_browser(headless=True, default_proxies=None):
    """
    初始化指定代理IP浏览器
    
    @param headless 是否启用浏览器界面
    """
    PROXY = get_proxy_ip() if default_proxies is None else choice(default_proxies)
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
        option.add_argument("--headless")
    try:
        browser = webdriver.Chrome(options=option)
    except WebDriverException as e:
        print(e.msg)
        print('重试一次初始化Chrome...')
        browser = webdriver.Chrome(options=option)
    # 隐式等待30s
    browser.implicitly_wait(30)
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
