# -*- coding: utf-8 -*-
import requests
import chardet
import asyncio
from fake_useragent import UserAgent
import aiohttp
from urllib3 import ProxyManager


def get_proxy(source="http://121.36.18.153:5010/get/"):
    return eval(requests.get(source).text)


class Request:
    def __init__(self, url, cookie='', retry_times=6, timeout=2, allow_redirect=True):
        self.url = url
        self.cookie = cookie
        self.retry_times = retry_times
        self.timeout = timeout
        self.allow_redirect = allow_redirect
        self.ua = UserAgent(verify_ssl=False)
        self.text = ''
        self.status_info = ''
    
    async def get_page_async(self):
        session = aiohttp.ClientSession()
        headers = {
            'User-Agent': self.ua.random,
        }
        if self.cookie:
            headers['cookie'] = self.cookie
        try:
            response = await session.get(self.url, headers=headers, timeout=self.timeout * 2,
                                         allow_redirects=self.allow_redirect)
            # print(response.status)
            if response and response.status == 200:
                self.text = await response.text(encoding='utf-8-sig')
                self.status_info = '200'
            else:
                self.get_page(proxy_mode=True)
                # self.status_info = str(response.status)
        except Exception:
            self.get_page(proxy_mode=True)
        await session.close()
    
    def get_page(self, proxy_mode=False):
        # proxy_mode 表示直接使用代理
        if proxy_mode:
            retry = 1
        else:
            retry = 0
        while retry < self.retry_times:
            headers = {
                'User-Agent': self.ua.random,
            }
            if self.cookie:
                headers['cookie'] = self.cookie
            try:
                if retry == 0:
                    response = requests.get(self.url, headers=headers, timeout=self.timeout, allow_redirects=self.allow_redirect)
                else:
                    proxy = {'http': get_proxy().get("proxy")}
                    print(proxy)
                    response = requests.get(self.url, headers=headers, timeout=self.timeout,
                                            allow_redirects=self.allow_redirect, proxies=proxy)
                if response and response.status_code == 200:
                    encode = chardet.detect(response.content).get('encoding', 'utf-8')  # 通过第3方模块来自动提取网页的编码
                    self.text = response.content.decode(encode, 'ignore')
                    self.status_info = '200'
                    break
                else:
                    self.status_info = str(response.status_code)
            except Exception as e:
                self.status_info = str(e)
            retry += 1


async def main():
    request = Request('http://www.ankang.gov.cn/Content-2142036.html')
    # await request.get_page_async()
    request.get_page(proxy_mode=True)
    print(request.status_info)


if __name__ == '__main__':
    asyncio.run(main())
    # request = Request('https://www.jianshu.com/p/20ca9daba85f')
    # request.get_page()
    # print(request.status_info)
