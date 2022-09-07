from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from lxml import etree


from bs4 import BeautifulSoup

from urllib.request import quote


import time
from datetime import datetime
from random import random,randint,choice
import json
import re

from proxy_ip import delete_ip, get_proxy_ip, get_url_content, init_browser


"""
 每个商城的appid不一样，所以采集时需要指定不同的商城ID
"""
market_dict = {'huawei':2,'xiaomi':3,'vivo':4,'oppo':5,'meizu':6,'应用宝':7,'baidu':8,'360':9,'豌豆荚':10}


def get_app_info(URL, type='browser', retry_times=3):
    # URL = 'https://app.diandian.com/app/nlxiruxj218miqn/android'
    have = False
    times = 0
    while have == False and times<retry_times:
        if type=='browser':
            dom, proxy_ip = get_url_html(URL)
            have = False if dom is None else True
        else:
            # webpage = requests.get(URL, headers=HEADERS,timeout=30)
            soup = BeautifulSoup(get_url_content(URL), "html.parser")
            dom = etree.HTML(str(soup))
            have = len(dom.xpath('//*[@id="content_open"]/p/text()'))>0 & len(dom.xpath("//div[@class='out-box']/div[2]/div[1]/div[2]/div/div/div/a/text()"))>0
        
        if have == False:
            times+=1
            print("{} 失败，重试：{}次".format(URL, times))
            time.sleep(5)
            if times == retry_times:
                # 达到重试次数后，删除代理IP，并使用driver重新请求一次
                delete_ip(proxy_ip)
                dom, proxy_ip = get_url_html(URL)
                have = False if dom is None else True

    
    info = parse_app_info(dom) if have else {}
    return info


def parse_app_info(dom):
    """
    解析app详情页的属性
    """
    pattern = re.compile("[\s]")
    info = {}
    try:
        info["bundleid"] = dom.xpath("//div[@class='out-box']/div[2]/div[1]/div[2]/div/div/div/a/text()")[0]
        info["down_link"] = dom.xpath("//div[@class='out-box']/div[2]/div[1]/div[2]/div/div/div/a/@href")[0]
        info["score"] = pattern.sub("",dom.xpath("//div[@class='out-box']/div[2]/div[2]/div[1]/a/text()")[0])
        info["join_score"] = pattern.sub("",dom.xpath("//div[@class='out-box']/div[2]/div[2]/a/text()")[0])
        info["developer"] = dom.xpath("//div[@class='out-box']/div[2]/div[5]/div[2]/div[1]/div[1]/div[1]/a/text()")[0]
        info["developer_host"] = dom.xpath("//div[@class='out-box']/div[2]/div[5]/div[2]/div[1]/div[1]/div[1]/a/@href")[0]
        info["download_count"] = pattern.sub("",dom.xpath("//div[@class='out-box']/div[2]/div[6]/div[1]/a/text()")[0])
        info["comment"] = dom.xpath('//*[@id="content_open"]/p/text()')[0]
        info["tags"] = ','.join([i.text for i in dom.xpath("//div[@class='tag-content']/span")])
    except:
        print("有部分信息为空")
        time.sleep(15)
    return info


def get_url_html(URL):
    browser, _ = init_browser(False)
    try:
        browser.get(URL)
    except WebDriverException as e:
        print(e.msg)
        return None, None
    
    try:
        browser.find_element_by_xpath('//div[@class="weixin-dialog"]/div[1]/i').click()
    except:
        print('没有广告弹窗')
    #获取网页源码
    resp_text = browser.page_source
    #数据解析
    page_html = etree.HTML(resp_text)
    try:
        proxyip = browser.capabilities['proxy']['httpProxy']
        print('ProxyIp = {}'.format(proxyip))
    except KeyError as e:
        print('未获得代理ip！')
        proxyip = None
    browser.close()
    return page_html, proxyip


def login_by_code(driver):
    mobile = input('请输入手机号：')
    # 输入手机号
    driver.find_element_by_css_selector('.sms-login-input').find_element_by_tag_name('input').send_keys(mobile)

    # 点击获取验证码
    driver.find_element_by_css_selector('.el-button').click()
    # 这个地方可以对接自动输入验证码功能，目前手工输入
    code = input('请输入验证码：')
    driver.find_element_by_xpath('//input[@placeholder="请输入手机验证码"]').send_keys(code)
    # 点击登录按钮
    driver.find_element_by_css_selector('.login-btn').click()


def login_by_pwd(browser):
    # 密码登录跳转app后会退出
    browser.get('https://www.diandian.com/login')
    browser.find_element_by_css_selector('.login-type').click()
    cur_type = browser.find_element_by_css_selector('.login-type.active')
    if cur_type.text=='快捷登录':
        browser.find_element_by_xpath('//div[@class="login-type"]').click()
    
    mobile = ''
    # 输入手机号
    browser.find_element_by_xpath('//input[@placeholder="请输入手机号"]').send_keys(mobile)
    time.sleep(2.3)
    # 这个地方可以对接自动输入验证码功能，目前手工输入
    code = ''
    browser.find_element_by_xpath('//input[@placeholder="输入密码"]').send_keys(code)
    # 点击登录按钮
    browser.find_element_by_css_selector('.login-btn').click()


def login_dd(driver,login_type='mima'):
    """
    完成登录，优先使用cookie登录，否则通过验证码登录，密码登录界面跳转后会退出

    @param driver : webdriver
    @param login_type: 登录方式，目前mima密码方式不可用，仅支持验证码登录
    """
    login = False
    try:
        print("通过cookies登录")
        driver.get("https://app.diandian.com")
        close_pop(driver)
        # 从保存文件中提取cookies
        f1 = open('cookie.txt')
        cookie = f1.read()
        cookie_list = json.loads(cookie)    #json读取cookies
        for c in cookie_list:
            driver.add_cookie(c)    #取出的cookie循环加入driver
        
        driver.refresh()    # 刷新后页面显示已登录
        close_pop(driver)
        login = True
        time.sleep(5)
    except:
        print("cookie处理失败")
    
    if login == False:
        # 点击登录注册
        try:
            driver.find_element_by_xpath('//*[@id="__layout"]/div/section/div/div[2]/div/div[2]/div/a').click()
        except:
            print('点击登录按钮失败！！！')
        # if driver.find_element_by_css_selector('use[xlink:href="#Dianzhanghaomima"]'): 每次都是二维码，去除判断
        driver.find_element_by_css_selector('.login-type').click()

        if login_type == 'code':
            login_by_code(driver)
        else:
            login_by_pwd(driver)
        
        # 避免cookie写入较慢    
        time.sleep(10)
        cookies = driver.get_cookies()    # 获取cookies
        f1 = open('cookie.txt', 'w')    #cookies存入文件JSON字符串
        f1.write(json.dumps(cookies))
        f1.close()


def close_pop(browser):
    """
    关闭页面弹窗
    """
    #  会有一个弹窗，需要关闭 
    try:
        # 首页
        a= browser.find_element_by_xpath('//*[@id="__layout"]/div/section/main/div/div[2]/div[7]/div/div[2]/div/div[1]/i')
    except:
        # 搜索页面
        try:
            a = browser.find_element_by_xpath('//*[@id="__layout"]/div/div[5]/div/div[2]/div/div[1]/i')
        except:
            print('没有弹窗！')
            a = None
    if a:
        a.click()


def search_in_page(driver):
    # 转入搜索页
    driver.get("https://app.diandian.com/search")
    
    # 点击应用榜单类型
    driver.find_element_by_xpath('//div[@slot="prefix"]').click()
    # 选择安卓榜单
    driver.find_element_by_css_selector('.dd-android-logo-16').click()
    # 输入理财 关键字
    driver.find_element_by_xpath('//*[@id="__layout"]/div/section/main/div/div[1]/div/div/div[2]/div[3]/div/div/div[1]/input').send_keys('理财')


def scroll(browser, wait, times=15):
    """
        滚动到页面底部
    """
    print('开始滚动页面到底部')
    refresh = True
    retry_times = 0;
    while refresh and retry_times < 3:
        try:
            total=wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,".screen-layout > div:nth-child(5)")))
            refresh = False
        except:
            print('页面未完全加载，重新刷新{}次'.format(retry_times))
            browser.refresh()
            time.sleep(5)
            retry_times += 1
    # total = wait.until(EC.presence_of_element_located((By.XPATH,'//*[@class="table-container"]/tr')))

    for i in range(times):
        browser.execute_script("window.scrollBy(0, 1000)")
        time.sleep(1)
    print('滚动结束')


def search_by_url(browser, wait ,shop_id, key_words):
    """
    通过商城ID及关键词进行应用搜索
    """
    url = 'https://app.diandian.com/search/android-{}-{}'.format(shop_id,key_words)
    print('访问搜索页面:{}'.format(url))
    # 直接跳转搜索结果页
    browser.get(url)
    close_pop(browser)
    scroll(browser, wait)
    #获取网页源码
    resp_text = browser.page_source
    #数据解析
    page_html = etree.HTML(resp_text)
    return page_html


def get_file_lines_count(filename):
    """
    获得文件行数

    @param filename: 文件名
    """
    count = -1
    import os
    if os.path.exists(filename) == True:
        for count,line in enumerate(open(filename,'rU')):
            pass
            count += 1
    else:
        count = 0
    return count


def exists_app_list(filename):
    """
    补充app
    """
    import os
    exists = {}
    if os.path.exists(filename) == True:
        file = open(filename)
        while True:
            text_line = file.readline()
            if len(text_line)>10:
                appinfo = json.loads(text_line.strip('\n'))
                if 'bundleid' in appinfo.keys():
                    exists[appinfo['url'].split('/')[2]]=appinfo
            else:
                break
    return exists


def parse_android_list(page_html, file_name):
    print('开始解析列表页内容：')
    data_list = []
    subset = []
    trs = page_html.xpath('//*[@class="table-container"]/tr/td[3]/div/div/div/div/div/div/div/a')
    ads = page.xpath('//*[@class="table-container"]/tr/td[2]/div')
    dates = page_html.xpath('//*[@class="table-container"]/tr/td[7]/div/div/a/text()')
    print('当前列表共【{}】个'.format(len(trs)))
    base_url = 'https://app.diandian.com'
    index = 0
    # c = get_file_lines_count(file_name.format(kw))
    exists = exists_app_list(file_name.format(kw))
    # 将中间数据转为最终结果list
    data_list = [json.dumps(i, ensure_ascii=False) for i in list(exists.values())]
    print('=========历史已采集【{}】个=========='.format(len(data_list)))
    for i in range(len(trs)):
        # 通过url处理明细数据采集 # 应用明细数据
        # https://app.diandian.com/app/nlxiruxj218miqn/android
        app_info_url = trs[i].attrib['href']
        if app_info_url.split('/')[2] in exists.keys():
            continue
        print('开始解析第【{}】个,url ={} '.format(i+1,app_info_url))
        info = get_app_info(base_url + app_info_url)
        info['name'] = trs[i].text
        info['url'] = app_info_url
        info['update'] = dates[i]
        try:
            info['ad'] = ads[i].xpath('span/text()')
        except:
            info['ad'] = '-1'
        subset.append(json.dumps(info, ensure_ascii=False))

        if len(subset)%5 == 0 or i==len(trs)-1:
            with open(file_name.format(kw),'a+') as f:
                f.write('\n'.join(subset)+'\n')
                index += 1
                print('写入临时批次[{}]'.format(index))
                data_list = data_list + subset
                subset.clear()
        time.sleep(round(random(),1)+randint(5,10))
    return data_list


if __name__ == '__main__':
    driver, wait = init_browser(headless=False,default_proxy=None)

    login_dd(driver, 'code')
    keywords = ["huawei:汽车"]
    file_name = './datas/applist-{}'
    for kw in keywords:
        kws = kw.split(':')
        page = search_by_url(driver, wait, market_dict[kws[0]], quote(kws[1], safe=";/?:@&=+$,", encoding="utf-8"))
        datas = parse_android_list(page, file_name)
        with open(file_name.format(kw) + '_all','a+') as f:
            f.write('\n'.join(datas))

    time.sleep(3)

    # 关闭当前窗口
    driver.close()
    # 退出浏览器
    driver.quit()